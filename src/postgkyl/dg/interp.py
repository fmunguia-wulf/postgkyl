"""Discontinuous-Galerkin interpolation — pure array in, array out.

A leaf: this module knows nothing about ``GDataState``/``ops``. It takes raw
DG basis coefficients (an ``(N+1)``-D NumPy array) plus the nodal grid and
returns the values evaluated on a refined uniform mesh together with that mesh.
The verb :func:`postgkyl.ops.interpolate` is the only thing that adapts a
dataset to this signature.
"""

from __future__ import annotations

import numpy as np

from .matrices import createInterpMatrix

# Number of basis functions per (dim, poly_order). Columns are poly_order 0..4.
_NUM_NODES_SERENDIPITY = np.array([
    [1, 2, 3, 4, 5],
    [1, 4, 8, 12, 17],
    [1, 8, 20, 32, 50],
    [1, 16, 48, 80, 136],
    [1, 32, 112, 192, 352],
    [1, 64, 256, 448, 880]])

_NUM_NODES_MAXIMAL = np.array([
    [2, 3, 4, 5],
    [3, 6, 10, 15],
    [4, 10, 20, 35],
    [5, 15, 35, 70],
    [6, 21, 56, 126],
    [7, 28, 84, 210]])

_NUM_NODES_TENSOR = np.array([
    [2, 3, 4, 5],
    [4, 9, 16, 25],
    [8, 27, 64, 125],
    [16, 81, 256, 625],
    [32, 343, 1024, 3125],
    [64, 729, 4096, 15625]])

_NUM_NODES_GKHYBRID = np.array([1, 6, 12, 24, 48])
_NUM_NODES_HYBRID = np.array([1, 6, 12, 24, 48])


def num_basis(dim: int, poly_order: int, basis_type: str) -> int:
  """Number of DG basis functions for a (dim, poly_order, basis_type)."""
  bt = basis_type.lower()
  if bt == "serendipity":
    return int(_NUM_NODES_SERENDIPITY[dim - 1, poly_order])
  if bt == "maximal-order":
    return int(_NUM_NODES_MAXIMAL[dim - 1, poly_order - 1])
  if bt == "tensor":
    return int(_NUM_NODES_TENSOR[dim - 1, poly_order - 1])
  if bt == "gkhybrid":
    return int(_NUM_NODES_GKHYBRID[dim - 1])
  if bt == "hybrid":
    return int(_NUM_NODES_HYBRID[dim - 1])
  raise NameError(f"Unsupported DG basis '{basis_type}'")


def _make_mesh(num_interp: int, edges: np.ndarray) -> np.ndarray:
  """Refine a 1-D nodal mesh by ``num_interp`` points per cell (uniform)."""
  nx = edges.shape[0] - 1
  return np.linspace(edges[0], edges[-1], num_interp * nx + 1)


def _raw_modal(values: np.ndarray, comp: int, nodes: int) -> np.ndarray:
  return values[..., comp * nodes:(comp + 1) * nodes]


def _raw_nodal(values: np.ndarray, comp: int, nodes: int, num_eqns: int) -> np.ndarray:
  shp = list(values.shape[:-1]) + [nodes]
  out = np.zeros(shp, np.float64)
  for n in range(nodes):
    out[..., n] = values[..., int(comp + n * num_eqns)]
  # end
  return out


def _interp_on_mesh(c_mat: np.ndarray, q_in: np.ndarray, num_interp: int,
    basis_type: str) -> np.ndarray:
  """Apply the interpolation matrix on every cell (ported from legacy dg.py)."""
  num_cells = np.array(q_in.shape)[:-1]  # drop the node axis
  num_dims = int(len(num_cells))
  num_interp_nd = np.array([max(num_interp, 2)] * num_dims)
  if basis_type == "gkhybrid":
    vpardir = (1 if num_dims in (2, 3) else (2 if num_dims == 4
        else (3 if num_dims == 5 else 99)))
    num_interp_nd[vpardir] = num_interp + 1
  elif basis_type == "hybrid":
    num_interp_nd[-1] = num_interp + 1
  # end
  q_out = np.zeros(num_cells * num_interp_nd, np.float64)
  q_in = np.moveaxis(q_in, -1, 0)  # node index first
  for n in range(int(np.prod(num_interp_nd))):
    temp = np.tensordot(c_mat[n, :], q_in, axes=1)
    start_idx = np.unravel_index(n, num_interp_nd, order="F")
    idxs = [slice(int(start_idx[i]), int(num_cells[i] * num_interp_nd[i]),
                  int(num_interp_nd[i]))
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
    basis_type: long basis name (``"serendipity"``, ``"maximal-order"``,
      ``"tensor"``, ``"gkhybrid"``, ``"hybrid"``).
    modal: whether the basis is modal (vs nodal).
    num_interp: interpolation points per cell; defaults to ``poly_order + 1``.

  Returns:
    ``(grid_out, values_out)`` — the refined edge grid and the
    ``(refined_cells..., num_components)`` value array.
  """
  num_dims = len(grid)
  if num_dims == 1 and basis_type == "hybrid":
    basis_type = "serendipity"  # PKPM hybrid degenerates to serendipity in 1D
  # end
  if num_interp is None:
    num_interp = poly_order + 1
  # end

  nodes = num_basis(num_dims, poly_order, basis_type)
  num_components = values.shape[-1] // nodes
  c_mat = createInterpMatrix(num_dims, poly_order, basis_type, num_interp, modal, False)

  out = None
  for c in range(num_components):
    q = (_raw_modal(values, c, nodes) if modal
         else _raw_nodal(values, c, nodes, num_components))
    interp_c = _interp_on_mesh(c_mat, q, num_interp, basis_type)[..., np.newaxis]
    out = interp_c if out is None else np.append(out, interp_c, axis=-1)
  # end

  # Points-per-dimension for the output grid (hybrids carry an extra one).
  if basis_type == "gkhybrid":
    vpardir = (1 if num_dims in (2, 3) else (2 if num_dims == 4
        else (3 if num_dims == 5 else 99)))
    ni = [num_interp] * num_dims
    ni[vpardir] = num_interp + 1
  elif basis_type == "hybrid":
    ni = [num_interp] * num_dims
    ni[-1] = num_interp + 1
  else:
    ni = [int(round(c_mat.shape[0] ** (1.0 / num_dims)))] * num_dims
  # end
  grid_out = [_make_mesh(ni[d], grid[d]) for d in range(num_dims)]
  return grid_out, out
