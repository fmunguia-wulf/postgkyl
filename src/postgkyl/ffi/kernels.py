"""Thin wrappers over Gkeyll's compiled operators (weak algebra & reductions).

Each function takes :class:`~postgkyl.ffi.array.GkylArray` operands plus the
basis descriptor and calls one shim entry point; the per-field loop for
``ncomp == nfields * num_basis`` arrays and all transient C resources
(``gkyl_dg_bin_op_mem``, integrate updaters) live inside the compiled shim.

Python-side capability guards mirror Gkeyll's own limits (which are C
``assert``s — letting them fire would abort the process).
"""

from __future__ import annotations

import numpy as np

from . import _lib
from .array import GkylArray
from .basis import get_basis

_WEAK_BASES = ("serendipity", "tensor")  # dg_bin_ops: assert(false) otherwise

# enum gkyl_array_op / gkyl_array_integrate_op ordinals used by the shim
REDUCE_OPS = {"min": 0, "max": 1, "sum": 2}
GKYL_MIN, GKYL_MAX, GKYL_SUM = 0, 1, 2
INTEGRATE_OPS = {"none": 0, "abs": 1, "sq": 2}


def _check_weak(basis_type: str, *arrays: GkylArray):
  if basis_type.lower() not in _WEAK_BASES:
    raise NotImplementedError(
        f"Gkeyll weak ops support {_WEAK_BASES}, not '{basis_type}'")
  first = arrays[0]
  for a in arrays[1:]:
    if (a.ncomp, a.size) != (first.ncomp, first.size):
      raise ValueError(f"operand shape mismatch: {a.ncomp}x{a.size} vs "
                       f"{first.ncomp}x{first.size}")


def _fields(arr: GkylArray, num_basis: int) -> int:
  if arr.ncomp % num_basis:
    raise ValueError(f"ncomp {arr.ncomp} is not a multiple of "
                     f"num_basis {num_basis}")
  return arr.ncomp // num_basis


def weak_mul(basis_type: str, ndim: int, poly_order: int,
    a: GkylArray, b: GkylArray) -> GkylArray:
  """Weak (DG) product ``a * b``, field by field, via ``gkyl_dg_mul_op``."""
  _check_weak(basis_type, a, b)
  basis = get_basis(basis_type, ndim, poly_order)
  _fields(a, basis.num_basis)
  out = GkylArray.alloc(a.ncomp, a.size)
  _lib.require().dg_mul(basis._cap, out._cap, a._cap, b._cap)
  return out


def weak_div(basis_type: str, ndim: int, poly_order: int,
    a: GkylArray, b: GkylArray) -> GkylArray:
  """Weak (DG) quotient ``a / b`` via ``gkyl_dg_div_op`` (per-cell solve)."""
  _check_weak(basis_type, a, b)
  basis = get_basis(basis_type, ndim, poly_order)
  _fields(a, basis.num_basis)
  out = GkylArray.alloc(a.ncomp, a.size)
  _lib.require().dg_div(basis._cap, out._cap, a._cap, b._cap)
  return out


def weak_inv(basis_type: str, ndim: int, poly_order: int,
    a: GkylArray) -> GkylArray:
  """Weak reciprocal ``1 / a`` via ``gkyl_dg_inv_op`` (Gkeyll: ser p=1 only)."""
  if basis_type.lower() != "serendipity" or poly_order != 1:
    raise NotImplementedError(
        "gkyl_dg_inv_op supports serendipity p=1 only (a Gkeyll limit); "
        "use weak division instead.")
  basis = get_basis(basis_type, ndim, poly_order)
  _fields(a, basis.num_basis)
  out = GkylArray.alloc(a.ncomp, a.size)
  _lib.require().dg_inv(basis._cap, out._cap, a._cap)
  return out


# ------------------------------------------------------- linear coefficient ops
def lincomb(ca: float, a: GkylArray, cb: float, b: GkylArray) -> GkylArray:
  """``ca*a + cb*b`` on the DG coefficients (gkyl_array_set + accumulate)."""
  if (a.ncomp, a.size) != (b.ncomp, b.size):
    raise ValueError("operand shape mismatch in lincomb")
  g0 = _lib.require()
  out = GkylArray.alloc(a.ncomp, a.size)
  g0.array_set(out._cap, ca, a._cap)
  g0.array_accumulate(out._cap, cb, b._cap)
  return out


def scale(a: GkylArray, factor: float) -> GkylArray:
  """``factor * a`` (gkyl_array_scale on a clone; the input is untouched)."""
  out = a.clone()
  _lib.require().array_scale(out._cap, factor)
  return out


def shiftc(a: GkylArray, val: float, comp: int) -> GkylArray:
  """Add ``val`` to component ``comp`` of every cell (gkyl_array_shiftc)."""
  out = a.clone()
  _lib.require().array_shiftc(out._cap, float(val), comp)
  return out


# ---------------------------------------------------------------- reductions
def reduce(a: GkylArray, op: int) -> np.ndarray:
  """Per-component MIN/MAX/SUM over all cells (gkyl_array_reduce)."""
  return _lib.require().array_reduce(a._cap, op)


def integrate(grid: dict, basis_type: str, poly_order: int, a: GkylArray,
    op: str = "none", factor: float = 1.0) -> np.ndarray:
  """``int dx op(f)`` per field via ``gkyl_array_integrate`` — one value per field.

  ``grid`` is the dict from ``rio`` (ndim/lower/upper/cells). Guarded to the
  kernel set compiled into libg0core (serendipity p1-p2 for none/abs/sq).
  """
  if op not in INTEGRATE_OPS:
    raise ValueError(f"integrate op '{op}' not in {sorted(INTEGRATE_OPS)}")
  if basis_type.lower() != "serendipity" or poly_order not in (1, 2):
    raise NotImplementedError(
        "gkyl_array_integrate kernels in libg0core cover serendipity p1-p2")
  ndim = int(grid["ndim"])
  basis = get_basis(basis_type, ndim, poly_order)
  nfields = _fields(a, basis.num_basis)
  lower = np.asarray(grid["lower"], dtype=np.float64)
  upper = np.asarray(grid["upper"], dtype=np.float64)
  cells = np.asarray(grid["cells"], dtype=np.int32)
  if int(np.prod(cells)) != a.size:
    raise ValueError(f"grid cells {tuple(cells)} do not cover the array "
                     f"({int(np.prod(cells))} vs {a.size} cells)")
  return _lib.require().array_integrate(lower, upper, cells, basis._cap,
      nfields, INTEGRATE_OPS[op], float(factor), a._cap)
