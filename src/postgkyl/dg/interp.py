"""Discontinuous-Galerkin interpolation — modal coefficients -> mesh values.

**This is the one-way bridge between the two domains**: DG coefficients in
(read through the container's NumPy view of the native array), plain NumPy
values out. The interpolation matrix is built from Gkeyll's own basis
functions (:mod:`postgkyl.ffi.basis` calls the ``eval`` pointer carried by
``struct gkyl_basis``), then applied per cell with a NumPy ``tensordot`` —
so the result is always a *new, by-value* NumPy array, never a view of C
memory. The vendored sympy matrix tables this replaced lived in
``matrices.py`` (see ``src_bak`` history).
"""

from __future__ import annotations

import numpy as np

from postgkyl.ffi import basis as ffi_basis


def num_basis(dim: int, poly_order: int, basis_type: str) -> int:
  """Number of DG basis functions, straight from Gkeyll's basis object."""
  return ffi_basis.num_basis(basis_type, dim, poly_order)


def _make_mesh(num_interp: int, edges: np.ndarray) -> np.ndarray:
  """Refine a 1-D nodal mesh by ``num_interp`` points per cell (uniform)."""
  nx = edges.shape[0] - 1
  return np.linspace(edges[0], edges[-1], num_interp * nx + 1)


def _interp_on_mesh(c_mat: np.ndarray, q_in: np.ndarray,
    num_interp: int) -> np.ndarray:
  """Apply the interpolation matrix on every cell (per-point scatter)."""
  num_cells = np.array(q_in.shape)[:-1]  # drop the coefficient axis
  num_dims = int(len(num_cells))
  ni = np.array([num_interp] * num_dims)
  q_out = np.zeros(num_cells * ni, np.float64)
  q_in = np.moveaxis(q_in, -1, 0)  # coefficient index first
  for n in range(int(np.prod(ni))):
    temp = np.tensordot(c_mat[n, :], q_in, axes=1)
    start_idx = np.unravel_index(n, ni, order="F")
    idxs = [slice(int(start_idx[i]), int(num_cells[i] * ni[i]), int(ni[i]))
            for i in range(num_dims)]
    q_out[tuple(idxs)] = temp
  # end
  return q_out


def interpolate(values: np.ndarray, grid: list, *, poly_order: int,
    basis_type: str, modal: bool = True, num_interp: int | None = None):
  """Interpolate DG coefficients onto a refined uniform mesh.

  Args:
    values: ``(cells..., total_comps)`` array of DG coefficients.
    grid: list of 1-D nodal edge arrays (one per dimension).
    poly_order: polynomial order of the basis.
    basis_type: long basis name (``"serendipity"`` or ``"tensor"``; the
      hybrid bases are not wired through the FFI in this minimal core).
    modal: False for nodal-basis data (field-blocked node values per cell);
      converted through the exact ``nodal_to_modal`` matrix first.
    num_interp: interpolation points per cell; defaults to ``poly_order + 1``.

  Returns:
    ``(grid_out, values_out)`` — the refined edge grid and a **new**
    ``(refined_cells..., num_fields)`` NumPy value array.
  """
  num_dims = len(grid)
  if num_dims == 1 and basis_type == "hybrid":
    basis_type = "serendipity"  # PKPM hybrid degenerates to serendipity in 1D
  # end
  if num_interp is None:
    num_interp = poly_order + 1
  # end

  nodes = num_basis(num_dims, poly_order, basis_type)
  num_fields = values.shape[-1] // nodes
  c_mat = ffi_basis.interp_matrix(basis_type, num_dims, poly_order, num_interp)

  n2m = (None if modal else
         ffi_basis.nodal_to_modal_matrix(basis_type, num_dims, poly_order))
  out = None
  for c in range(num_fields):
    q = values[..., c * nodes:(c + 1) * nodes]
    if n2m is not None:
      q = np.einsum("jk,...k->...j", n2m, q)
    interp_c = _interp_on_mesh(c_mat, q, num_interp)[..., np.newaxis]
    out = interp_c if out is None else np.append(out, interp_c, axis=-1)
  # end

  grid_out = [_make_mesh(num_interp, grid[d]) for d in range(num_dims)]
  return grid_out, out
