"""Gkeyll basis objects + evaluation matrices, through the pg0 shim.

``struct gkyl_basis`` carries the basis functions themselves; the shim
dispatches its function pointers in compiled C (``pg0_basis_eval`` & co.), so
the interpolation matrix is assembled by evaluating Gkeyll's own basis at the
interpolation points — a few hundred calls, cached per basis — and NumPy
applies it at array speed. The matrices are therefore bit-consistent with the
kernels the simulation used, with zero layout knowledge in Python.

Interpolation points follow the historical postgkyl convention: ``num_interp``
subcell centers per cell, ``z_i = -(n-1)/n + 2 i/n`` on [-1, 1], with
multi-dimensional points ordered Fortran-style (dimension 0 fastest) to match
the per-cell scatter in ``dg/interp.py``.
"""

from __future__ import annotations

import numpy as np

from . import _lib


class Basis:
  """A cached Gkeyll basis: opaque handle + the descriptors postgkyl reads."""

  def __init__(self, cap, ndim: int, poly_order: int, num_basis: int,
      id: str):
    self._cap = cap
    self.ndim = ndim
    self.poly_order = poly_order
    self.num_basis = num_basis
    self.id = id

  def __repr__(self) -> str:
    return (f"<Basis {self.id} ndim={self.ndim} p={self.poly_order} "
            f"N={self.num_basis}>")


_basis_cache: dict[tuple, Basis] = {}
_matrix_cache: dict[tuple, np.ndarray] = {}


def get_basis(basis_type: str, ndim: int, poly_order: int) -> Basis:
  """A cached, fully-initialized Gkeyll basis object."""
  key = (basis_type.lower(), ndim, poly_order)
  if key in _basis_cache:
    return _basis_cache[key]
  cap = _lib.require().basis_new(key[0], ndim, poly_order)
  nd, p, nb, bid = _lib.require().basis_info(cap)
  _basis_cache[key] = Basis(cap, nd, p, nb, bid)
  return _basis_cache[key]


def num_basis(basis_type: str, ndim: int, poly_order: int) -> int:
  """Number of DG basis functions, straight from Gkeyll."""
  return get_basis(basis_type, ndim, poly_order).num_basis


def interp_points_1d(num_interp: int) -> np.ndarray:
  """Subcell-center evaluation points on [-1, 1] (legacy postgkyl convention)."""
  n = num_interp
  return np.array([-(n - 1.0) / n + 2.0 * i / n for i in range(n)])


def tensor_points(pts_1d: np.ndarray, ndim: int) -> np.ndarray:
  """``(len(pts_1d)**ndim, ndim)`` tensor-product point set, dimension 0
  fastest (Fortran multi-index order — the convention every consumer uses)."""
  n = len(pts_1d)
  shape = (n,) * ndim
  out = np.empty((n ** ndim, ndim))
  for i in range(n ** ndim):
    idx = np.unravel_index(i, shape, order="F")
    out[i, :] = [pts_1d[idx[d]] for d in range(ndim)]
  return out


def eval_matrix(basis_type: str, ndim: int, poly_order: int,
    points: np.ndarray) -> np.ndarray:
  """``(npts, num_basis)`` matrix ``M[i, j] = b_j(z_i)`` at arbitrary points
  in the reference cell [-1, 1]^ndim — built by evaluating Gkeyll's own basis
  through the shim. The workhorse behind every representation change *and*
  the plotting bridge."""
  g0 = _lib.require()
  basis = get_basis(basis_type, ndim, poly_order)
  points = np.atleast_2d(np.asarray(points, dtype=np.float64))
  mat = np.empty((points.shape[0], basis.num_basis))
  for i, pt in enumerate(points):
    mat[i, :] = g0.basis_eval(basis._cap, pt)
  return mat


def _cached(key, build):
  if key not in _matrix_cache:
    mat = build()
    mat.flags.writeable = False
    _matrix_cache[key] = mat
  return _matrix_cache[key]


def interp_matrix(basis_type: str, ndim: int, poly_order: int,
    num_interp: int) -> np.ndarray:
  """Evaluation matrix at ``num_interp`` subcell centers per dimension.

  Row ``i`` corresponds to the point with multi-index
  ``np.unravel_index(i, [num_interp]*ndim, order="F")`` — dimension 0 fastest,
  matching the consumer in ``dg/interp.py``.
  """
  return _cached(("interp", basis_type, ndim, poly_order, num_interp),
      lambda: eval_matrix(basis_type, ndim, poly_order,
          tensor_points(interp_points_1d(num_interp), ndim)))


# ------------------------------------------------- nodal <-> modal (exact)
def node_coords(basis_type: str, ndim: int, poly_order: int) -> np.ndarray:
  """``(num_basis, ndim)`` node coordinates from the basis ``node_list``."""
  basis = get_basis(basis_type, ndim, poly_order)
  return _lib.require().basis_node_list(basis._cap)


def nodal_to_modal_matrix(basis_type: str, ndim: int,
    poly_order: int) -> np.ndarray:
  """Exact N×N change of basis, from Gkeyll's ``nodal_to_modal``
  (columns = images of the nodal unit vectors)."""
  def build():
    g0 = _lib.require()
    basis = get_basis(basis_type, ndim, poly_order)
    nb = basis.num_basis
    mat = np.empty((nb, nb))
    for j in range(nb):
      fin = np.zeros(nb)
      fin[j] = 1.0
      mat[:, j] = g0.basis_nodal_to_modal(basis._cap, fin)
    return mat
  return _cached(("n2m", basis_type, ndim, poly_order), build)


def modal_to_nodal_matrix(basis_type: str, ndim: int,
    poly_order: int) -> np.ndarray:
  """Evaluation at the basis nodes — the exact inverse of ``nodal_to_modal``."""
  return _cached(("m2n", basis_type, ndim, poly_order),
      lambda: eval_matrix(basis_type, ndim, poly_order,
          node_coords(basis_type, ndim, poly_order)))


# ------------------------------------------- quadrature <-> modal (projection)
def gauss_quad(ndim: int, num_quad: int):
  """Tensor-product Gauss–Legendre rule on [-1, 1]^ndim:
  ``(points (nq**ndim, ndim), weights (nq**ndim,))``, dimension 0 fastest."""
  p1, w1 = np.polynomial.legendre.leggauss(num_quad)
  pts = tensor_points(p1, ndim)
  shape = (num_quad,) * ndim
  w = np.empty(num_quad ** ndim)
  for i in range(w.size):
    idx = np.unravel_index(i, shape, order="F")
    w[i] = np.prod([w1[idx[d]] for d in range(ndim)])
  return pts, w


def modal_to_quad_matrix(basis_type: str, ndim: int, poly_order: int,
    num_quad: int) -> np.ndarray:
  """``(nq**ndim, num_basis)`` — evaluate the expansion at the Gauss points."""
  return _cached(("m2q", basis_type, ndim, poly_order, num_quad),
      lambda: eval_matrix(basis_type, ndim, poly_order,
          gauss_quad(ndim, num_quad)[0]))


def quad_to_modal_matrix(basis_type: str, ndim: int, poly_order: int,
    num_quad: int) -> np.ndarray:
  """``(num_basis, nq**ndim)`` quadrature projection ``c_j = sum_i w_i b_j(z_i) f_i``.

  Exact whenever the integrand ``f·b_j`` has degree ≤ 2·num_quad−1 (the bases
  are orthonormal on the reference cell, so no mass-matrix solve is needed).
  ``quad_to_modal @ modal_to_quad == I`` for ``num_quad >= p+1``.
  """
  def build():
    pts, w = gauss_quad(ndim, num_quad)
    B = eval_matrix(basis_type, ndim, poly_order, pts)
    return B.T * w  # (N, npts): rows b_j(z_i), scaled by the weights
  return _cached(("q2m", basis_type, ndim, poly_order, num_quad), build)
