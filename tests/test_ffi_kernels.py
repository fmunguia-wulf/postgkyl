"""Tests for ``postgkyl.ffi.kernels`` — weak algebra, lincomb, reduce, integrate.

Run:  PYTHONPATH=src pytest tests/test_ffi_kernels.py -v
"""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
  sys.path.insert(0, SRC)

from postgkyl import ffi  # noqa: E402
from postgkyl.ffi import kernels as k  # noqa: E402
from postgkyl.ffi.array import GkylArray  # noqa: E402

needs_gkeyll = pytest.mark.skipif(not ffi.available(),
    reason="no compiled Gkeyll (libg0core.so) found")

pytestmark = needs_gkeyll


def _smooth_field(basis_type, ndim, p, cells, rng, shift=0.0):
  """Random-but-smooth modal coefficients: only the constant + a small
  perturbation on the higher modes, and shifted away from zero so weak
  division never divides by (near-)zero."""
  nb = ffi.basis.num_basis(basis_type, ndim, p)
  coeffs = rng.normal(scale=0.05, size=(cells, nb))
  coeffs[:, 0] += shift
  return GkylArray.from_numpy(coeffs)


# --------------------------------------------------------------- weak algebra
@pytest.mark.parametrize("ndim,p", [(1, 1), (1, 2), (2, 1), (2, 2)])
def test_weak_mul_div_are_inverses_on_smooth_fields(ndim, p):
  rng = np.random.default_rng(42)
  basis_type = "serendipity"
  cells = 6
  a = _smooth_field(basis_type, ndim, p, cells, rng, shift=3.0)
  b = _smooth_field(basis_type, ndim, p, cells, rng, shift=5.0)
  ab = k.weak_mul(basis_type, ndim, p, a, b)
  back = k.weak_div(basis_type, ndim, p, ab, b)
  np.testing.assert_allclose(back.view(), a.view(), atol=1e-10)


def test_weak_inv_matches_weak_div_by_one():
  rng = np.random.default_rng(7)
  basis_type, ndim, p, cells = "serendipity", 1, 1, 4
  a = _smooth_field(basis_type, ndim, p, cells, rng, shift=4.0)
  one = GkylArray.from_numpy(
      np.zeros((cells, ffi.basis.num_basis(basis_type, ndim, p))))
  # constant field 1: coefficient 0 is 1/normalization, i.e. sqrt(2)**ndim
  one.view()  # no-op just to document one is unused below (division test)
  inv_a = k.weak_inv(basis_type, ndim, p, a)
  back = k.weak_mul(basis_type, ndim, p, inv_a, a)
  # a * (1/a) == 1: coefficient 0 equals normalization constant, others ~ 0.
  expect = np.zeros_like(back.view())
  expect[:, 0] = np.sqrt(2.0)
  np.testing.assert_allclose(back.view(), expect, atol=1e-10)


def test_weak_mul_rejects_ncomp_not_a_multiple_of_num_basis():
  basis_type, ndim, p = "serendipity", 1, 1  # num_basis == 2
  a = GkylArray.alloc(3, 4)  # 3 is not a multiple of 2
  b = GkylArray.alloc(3, 4)
  with pytest.raises(ValueError, match="not a multiple"):
    k.weak_mul(basis_type, ndim, p, a, b)


def test_weak_mul_rejects_shape_mismatch():
  basis_type, ndim, p = "serendipity", 1, 1
  a = GkylArray.alloc(2, 4)
  b = GkylArray.alloc(2, 5)  # different size
  with pytest.raises(ValueError, match="shape mismatch"):
    k.weak_mul(basis_type, ndim, p, a, b)


def test_weak_ops_reject_unknown_basis_type():
  a = GkylArray.alloc(2, 4)
  b = GkylArray.alloc(2, 4)
  with pytest.raises(NotImplementedError, match="serendipity"):
    k.weak_mul("bogus", 1, 1, a, b)


@pytest.mark.parametrize("ndim", [4, 5, 6])
def test_weak_mul_div_refuse_ndim_above_3(ndim):
  """gkyl_dg_bin_ops' kernel tables assert(dim < 4) -- a process abort if
  this guard were missing; it must degrade to a clean exception instead."""
  basis = ffi.basis.get_basis("serendipity", ndim, 1)
  a = GkylArray.alloc(basis.num_basis, 3)
  b = GkylArray.alloc(basis.num_basis, 3)
  with pytest.raises(NotImplementedError, match="ndim 1..3"):
    k.weak_mul("serendipity", ndim, 1, a, b)
  with pytest.raises(NotImplementedError, match="ndim 1..3"):
    k.weak_div("serendipity", ndim, 1, a, b)


def test_weak_mul_div_refuse_tensor_poly_order_above_table():
  """Tensor mul/div kernels only go to p2 at ndim 2-3 (p3 slot is NULL)."""
  a = GkylArray.alloc(16, 3)  # shape irrelevant; guard fires first
  b = GkylArray.alloc(16, 3)
  with pytest.raises(NotImplementedError, match="poly_order 0..2"):
    k.weak_mul("tensor", 2, 3, a, b)


def test_weak_inv_rejects_non_p1():
  a = GkylArray.alloc(2, 3)
  with pytest.raises(NotImplementedError, match="p=1 only"):
    k.weak_inv("serendipity", 1, 2, a)


@pytest.mark.parametrize("ndim", [4, 5, 6])
def test_weak_inv_refuses_ndim_above_3(ndim):
  """gkyl_dg_inv_op's kernel table has NO bounds check at all for ndim; this
  guard is the only thing standing between a call and undefined behavior."""
  basis = ffi.basis.get_basis("serendipity", ndim, 1)
  a = GkylArray.alloc(basis.num_basis, 3)
  with pytest.raises(NotImplementedError, match="ndim"):
    k.weak_inv("serendipity", ndim, 1, a)


# ---------------------------------------------------------- coefficient ops
def test_lincomb_matches_numpy():
  rng = np.random.default_rng(1)
  a = GkylArray.from_numpy(rng.normal(size=(5, 3)))
  b = GkylArray.from_numpy(rng.normal(size=(5, 3)))
  out = k.lincomb(2.0, a, -1.5, b)
  np.testing.assert_allclose(out.view(), 2.0 * a.view() - 1.5 * b.view())


def test_lincomb_rejects_shape_mismatch():
  a = GkylArray.alloc(2, 4)
  b = GkylArray.alloc(3, 4)
  with pytest.raises(ValueError, match="shape mismatch"):
    k.lincomb(1.0, a, 1.0, b)


def test_scale_matches_numpy_and_does_not_mutate_input():
  a = GkylArray.from_numpy(np.arange(6, dtype=np.float64).reshape(3, 2))
  original = a.view().copy()
  out = k.scale(a, -2.0)
  np.testing.assert_allclose(out.view(), -2.0 * original)
  np.testing.assert_allclose(a.view(), original)


def test_shiftc_matches_numpy_and_does_not_mutate_input():
  a = GkylArray.from_numpy(np.zeros((3, 2)))
  out = k.shiftc(a, 7.0, 1)
  expect = np.zeros((3, 2))
  expect[:, 1] = 7.0
  np.testing.assert_allclose(out.view(), expect)
  np.testing.assert_allclose(a.view(), np.zeros((3, 2)))


# ---------------------------------------------------------------- reductions
def test_reduce_of_constant_coefficients():
  a = GkylArray.from_numpy(np.full((4, 2), 3.0))
  np.testing.assert_allclose(k.reduce(a, k.GKYL_SUM), [12.0, 12.0])
  np.testing.assert_allclose(k.reduce(a, k.GKYL_MIN), [3.0, 3.0])
  np.testing.assert_allclose(k.reduce(a, k.GKYL_MAX), [3.0, 3.0])


def test_dg_reduce_of_constant_field_min_max_match_the_constant():
  """min/max of a truly constant field equal that constant regardless of how
  many Gauss-Legendre nodes per cell the kernel evaluates at."""
  basis_type, ndim, p = "serendipity", 1, 1
  nb = ffi.basis.num_basis(basis_type, ndim, p)
  coeffs = np.zeros((5, nb))
  coeffs[:, 0] = 3.0 * np.sqrt(2.0)  # constant mode -> field value 3.0
  a = GkylArray.from_numpy(coeffs)
  assert np.isclose(k.dg_reduce(basis_type, ndim, p, a, 0, "min"), 3.0)
  assert np.isclose(k.dg_reduce(basis_type, ndim, p, a, 0, "max"), 3.0)


def test_dg_reduce_sum_scales_with_cell_count():
  """`sum` totals the per-node field values across every cell (not divided
  by node count), so doubling identical cells must exactly double it —
  a cell-count-independent way to check the "sum over the field" semantics
  without needing to know the kernel's internal Gauss-node count."""
  basis_type, ndim, p = "serendipity", 1, 1
  nb = ffi.basis.num_basis(basis_type, ndim, p)

  def const_field(ncells, value):
    coeffs = np.zeros((ncells, nb))
    coeffs[:, 0] = value * np.sqrt(2.0)
    return GkylArray.from_numpy(coeffs)

  small = k.dg_reduce(basis_type, ndim, p, const_field(3, 3.0), 0, "sum")
  big = k.dg_reduce(basis_type, ndim, p, const_field(6, 3.0), 0, "sum")
  assert small > 0
  assert np.isclose(big, 2.0 * small)


def test_dg_reduce_min_max_at_the_gauss_legendre_nodes_for_a_linear_field():
  """min/max are evaluated at the basis's Gauss-Legendre quadrature NODES
  (interior points), not the cell edges — so for f(z) = 3 + 2z they equal f
  at the nodes nearest each end, not the true f(-1)/f(1) domain extrema.
  Serendipity p=1 in 1D uses the 2-point rule at z = +-1/sqrt(3)."""
  basis_type, ndim, p = "serendipity", 1, 1
  # modal coefficients of 3 + 2z in the (normalized Legendre) basis:
  # b0 = 1/sqrt(2), b1 = sqrt(3/2) z  =>  c0 = 3*sqrt(2), c1 = 2/sqrt(3/2)
  c0 = 3.0 * np.sqrt(2.0)
  c1 = 2.0 / np.sqrt(1.5)
  a = GkylArray.from_numpy(np.array([[c0, c1]]))
  node = 1.0 / np.sqrt(3.0)
  assert np.isclose(k.dg_reduce(basis_type, ndim, p, a, 0, "min"), 3.0 - 2.0 * node)
  assert np.isclose(k.dg_reduce(basis_type, ndim, p, a, 0, "max"), 3.0 + 2.0 * node)


def test_dg_reduce_rejects_bad_op_and_bad_comp():
  a = GkylArray.alloc(2, 3)
  with pytest.raises(ValueError, match="op"):
    k.dg_reduce("serendipity", 1, 1, a, 0, "bogus")
  with pytest.raises(ValueError, match="comp"):
    k.dg_reduce("serendipity", 1, 1, a, 5, "sum")


# ----------------------------------------------------------------- integrate
def test_integrate_constant_field_equals_constant_times_volume():
  basis_type, ndim, p = "serendipity", 1, 1
  nb = ffi.basis.num_basis(basis_type, ndim, p)
  cells = 4
  coeffs = np.zeros((cells, nb))
  coeffs[:, 0] = 2.0 * np.sqrt(2.0)  # constant field value 2.0
  a = GkylArray.from_numpy(coeffs)
  grid = {"ndim": 1, "lower": np.array([0.0]), "upper": np.array([2.0]),
          "cells": np.array([cells])}
  result = k.integrate(grid, basis_type, p, a)
  np.testing.assert_allclose(result, [2.0 * 2.0])  # value * volume


def test_integrate_abs_and_sq_ops():
  basis_type, ndim, p = "serendipity", 1, 1
  nb = ffi.basis.num_basis(basis_type, ndim, p)
  coeffs = np.zeros((3, nb))
  coeffs[:, 0] = -2.0 * np.sqrt(2.0)  # constant field value -2.0
  a = GkylArray.from_numpy(coeffs)
  grid = {"ndim": 1, "lower": np.array([0.0]), "upper": np.array([3.0]),
          "cells": np.array([3])}
  none = k.integrate(grid, basis_type, p, a, op="none")
  absr = k.integrate(grid, basis_type, p, a, op="abs")
  sq = k.integrate(grid, basis_type, p, a, op="sq")
  np.testing.assert_allclose(none, [-6.0])
  np.testing.assert_allclose(absr, [6.0])
  np.testing.assert_allclose(sq, [12.0])  # (-2)^2 * volume(3) = 12


def test_integrate_factor_scales_the_result():
  basis_type, ndim, p = "serendipity", 1, 1
  nb = ffi.basis.num_basis(basis_type, ndim, p)
  coeffs = np.zeros((2, nb))
  coeffs[:, 0] = np.sqrt(2.0)
  a = GkylArray.from_numpy(coeffs)
  grid = {"ndim": 1, "lower": np.array([0.0]), "upper": np.array([2.0]),
          "cells": np.array([2])}
  result = k.integrate(grid, basis_type, p, a, factor=10.0)
  np.testing.assert_allclose(result, [20.0])


def test_integrate_rejects_bad_op():
  a = GkylArray.alloc(2, 2)
  grid = {"ndim": 1, "lower": [0.0], "upper": [1.0], "cells": [2]}
  with pytest.raises(ValueError, match="op"):
    k.integrate(grid, "serendipity", 1, a, op="bogus")


def test_integrate_rejects_unsupported_basis_or_poly_order():
  a = GkylArray.alloc(2, 2)
  grid = {"ndim": 1, "lower": [0.0], "upper": [1.0], "cells": [2]}
  with pytest.raises(NotImplementedError):
    k.integrate(grid, "tensor", 1, a)
  with pytest.raises(NotImplementedError):
    k.integrate(grid, "serendipity", 3, a)  # p3 unsupported by the kernel set


def test_integrate_rejects_ndim_above_3():
  basis = ffi.basis.get_basis("serendipity", 4, 1)
  a = GkylArray.alloc(basis.num_basis, 6)
  grid = {"ndim": 4, "lower": np.zeros(4), "upper": np.ones(4),
          "cells": np.array([1, 1, 1, 6])}
  with pytest.raises(NotImplementedError, match="ndim 1-3"):
    k.integrate(grid, "serendipity", 1, a)


def test_integrate_rejects_grid_array_mismatch():
  basis_type, ndim, p = "serendipity", 1, 1
  a = GkylArray.alloc(ffi.basis.num_basis(basis_type, ndim, p), 4)
  grid = {"ndim": 1, "lower": np.array([0.0]), "upper": np.array([1.0]),
          "cells": np.array([5])}  # 5 != a.size (4)
  with pytest.raises(ValueError, match="do not cover"):
    k.integrate(grid, basis_type, p, a)
