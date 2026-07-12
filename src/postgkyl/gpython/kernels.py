"""Thin wrappers over Gkeyll's compiled operators (weak algebra & reductions).

Each function takes :class:`~postgkyl.gpython.array.GkylArray` operands plus the
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

# Weak mul/div kernel tables (gkyl_dg_bin_ops_priv.h ser_mul_list/ten_mul_list/
# ser_div_set_list/ten_div_set_list) are fixed-size [ndim][poly_order] arrays
# covering ONLY ndim 1..3 — narrower than the basis module's own eval range.
# ndim >= 4 hits `assert(dim < 4)` in choose_ser_mul_kern (a process abort);
# an out-of-table poly_order for tensor (p3 at ndim 2-3) returns a NULL
# kernel pointer that gkyl_dg_mul_op/div_op call with NO null check at all
# (a segfault, not an assert). Both must be refused here.
_WEAK_MAX_POLY_ORDER = {
    "serendipity": {1: 3, 2: 3, 3: 3},
    "tensor": {1: 3, 2: 2, 3: 2},
}
# gkyl_dg_inv_op's kernel table (ser_inv_list) has no dim bound check
# whatsoever (a raw out-of-bounds array read for ndim >= 4) and only fills
# poly_order == 1 for ndim 1..3.
_WEAK_INV_DIMS = (1, 2, 3)


def _check_weak(basis_type: str, ndim: int, poly_order: int,
    *arrays: GkylArray):
  basis_type = basis_type.lower()
  limits = _WEAK_MAX_POLY_ORDER.get(basis_type)
  if limits is None:
    raise NotImplementedError(
        f"Gkeyll weak ops support {_WEAK_BASES}, not '{basis_type}'")
  max_p = limits.get(ndim)
  if max_p is None:
    raise NotImplementedError(
        f"Gkeyll's weak (DG) mul/div kernels support ndim 1..3, got {ndim}")
  if not 0 <= poly_order <= max_p:
    raise NotImplementedError(
        f"Gkeyll's weak {basis_type} mul/div kernels in {ndim}D support "
        f"poly_order 0..{max_p}, got {poly_order}")
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
  _check_weak(basis_type, ndim, poly_order, a, b)
  basis = get_basis(basis_type, ndim, poly_order)
  _fields(a, basis.num_basis)
  out = GkylArray.alloc(a.ncomp, a.size)
  _lib.require().dg_mul(basis._cap, out._cap, a._cap, b._cap)
  return out


def weak_div(basis_type: str, ndim: int, poly_order: int,
    a: GkylArray, b: GkylArray) -> GkylArray:
  """Weak (DG) quotient ``a / b`` via ``gkyl_dg_div_op`` (per-cell solve)."""
  _check_weak(basis_type, ndim, poly_order, a, b)
  basis = get_basis(basis_type, ndim, poly_order)
  _fields(a, basis.num_basis)
  out = GkylArray.alloc(a.ncomp, a.size)
  _lib.require().dg_div(basis._cap, out._cap, a._cap, b._cap)
  return out


def weak_inv(basis_type: str, ndim: int, poly_order: int,
    a: GkylArray) -> GkylArray:
  """Weak reciprocal ``1 / a`` via ``gkyl_dg_inv_op`` (Gkeyll: ser p=1, ndim<=3 only)."""
  if basis_type.lower() != "serendipity" or poly_order != 1:
    raise NotImplementedError(
        "gkyl_dg_inv_op supports serendipity p=1 only (a Gkeyll limit); "
        "use weak division instead.")
  if ndim not in _WEAK_INV_DIMS:
    raise NotImplementedError(
        f"gkyl_dg_inv_op supports ndim {_WEAK_INV_DIMS} only, got {ndim} "
        "(a Gkeyll limit; its kernel table has no bounds check at all, so "
        "this guard is load-bearing, not decorative)")
  basis = get_basis(basis_type, ndim, poly_order)
  _fields(a, basis.num_basis)
  out = GkylArray.alloc(a.ncomp, a.size)
  _lib.require().dg_inv(basis._cap, out._cap, a._cap)
  return out


# -------------------------------------------------- conf-space x phase-space
# gkyl_dg_mul_conf_phase_op_range picks its kernel from the PHASE basis type
# alone (choose_mul_conf_phase_kern in gkyl_dg_bin_ops_priv.h); for
# hybrid/gkhybrid the conf poly_order it reads is unused by that branch, so
# the only real requirement (Gkeyll's own PKPM/GK convention) is a
# serendipity conf basis. Every (cdim, vdim) split our own basis.py
# convention (_HYBRID_CDIM_VDIM) derives from a valid hybrid/gkhybrid ndim
# already has a populated cross_mul_list entry -- verified by hand against
# hyb_cross_mul_list/gkhyb_cross_mul_list, so no extra table is needed there.
# serendipity/tensor phase bases have a genuinely holey (cdim, pdim,
# poly_order) kernel table -- unlike same-basis weak_mul, most combinations
# a valid same-basis object could have are simply absent (NULL function
# pointer, no null check in gkyl_dg_mul_conf_phase_op_range) -- so those are
# guarded explicitly below, transcribed from ser_cross_mul_list /
# ten_cross_mul_list in gkyl_dg_bin_ops_priv.h.
_CROSS_MUL_SER = {
    2: {1: {1, 2, 3}},
    3: {1: {1, 2, 3}, 2: {1, 2, 3}},
    4: {1: {1, 2, 3}, 2: {1, 2, 3}, 3: {1, 2, 3}},
    5: {2: {1, 2}, 3: {1, 2}},
    6: {3: {1}},
}
_CROSS_MUL_TEN = {
    2: {1: {1, 2}},
    3: {1: {1, 2}, 2: {1, 2}},
    4: {1: {1, 2}, 2: {1, 2}, 3: {1}},
    5: {2: {1, 2}, 3: {1}},
    6: {3: {1}},
}
_CROSS_MUL_TABLES = {"serendipity": _CROSS_MUL_SER, "tensor": _CROSS_MUL_TEN}


def _check_mul_conf_phase(conf_basis_type: str, phase_basis_type: str,
    conf_ndim: int, phase_ndim: int, poly_order: int):
  conf_basis_type = conf_basis_type.lower()
  phase_basis_type = phase_basis_type.lower()
  if phase_ndim <= conf_ndim:
    raise ValueError(
        f"phase_ndim ({phase_ndim}) must exceed conf_ndim ({conf_ndim})")
  if phase_basis_type in ("hybrid", "gkhybrid"):
    if conf_basis_type != "serendipity":
      raise NotImplementedError(
          "Gkeyll pairs a hybrid/gkhybrid phase basis with a serendipity "
          f"conf basis only (its own PKPM/GK convention), not "
          f"'{conf_basis_type}'")
    return
  if phase_basis_type in ("serendipity", "tensor"):
    if conf_basis_type != phase_basis_type:
      raise NotImplementedError(
          "gkyl_dg_mul_conf_phase_op_range picks its kernel from the phase "
          f"basis type alone ('{phase_basis_type}'); pair it with a conf "
          f"basis of the same type, not '{conf_basis_type}'")
    valid = _CROSS_MUL_TABLES[phase_basis_type].get(phase_ndim, {}).get(
        conf_ndim)
    if not valid or poly_order not in valid:
      raise NotImplementedError(
          f"Gkeyll has no {phase_basis_type} conf*phase cross-mul kernel "
          f"for conf_ndim={conf_ndim}, phase_ndim={phase_ndim}, "
          f"poly_order={poly_order}")
    return
  raise NotImplementedError(
      "Gkeyll's conf*phase cross-mul supports serendipity, tensor, hybrid, "
      f"gkhybrid phase bases, not '{phase_basis_type}'")


def weak_mul_conf_phase(conf_basis_type: str, conf_ndim: int,
    phase_basis_type: str, phase_ndim: int, poly_order: int,
    conf_cells, phase_cells, cop: GkylArray, pop: GkylArray) -> GkylArray:
  """Conf-space x phase-space weak product ``cop * pop`` via
  ``gkyl_dg_mul_conf_phase_op_range`` -- e.g. a density (conf-space) times a
  distribution function (phase-space) in PKPM/gyrokinetic post-processing.

  Unlike :func:`weak_mul`, this is single-field only on both sides (the
  underlying kernel takes no field-index arguments): ``cop.ncomp`` must
  equal the conf basis's ``num_basis`` and ``pop.ncomp`` the phase basis's.

  ``conf_cells``/``phase_cells`` are each grid's per-dimension cell counts
  (e.g. ``rio``'s ``grid["cells"]``) -- Gkeyll maps each phase cell to its
  conf cell by dropping the velocity-space indices, so both cell counts are
  needed to build matching index ranges; ``conf_cells`` must equal the
  leading ``conf_ndim`` entries of ``phase_cells``.

  The dispatch is asymmetric: Gkeyll chooses the kernel from the PHASE
  basis type alone, so ``conf_basis_type`` must be ``"serendipity"`` when
  pairing with hybrid/gkhybrid, or match ``phase_basis_type`` exactly for
  serendipity/tensor.
  """
  _check_mul_conf_phase(conf_basis_type, phase_basis_type, conf_ndim,
      phase_ndim, poly_order)
  cbasis = get_basis(conf_basis_type, conf_ndim, poly_order)
  pbasis = get_basis(phase_basis_type, phase_ndim, poly_order)
  if cop.ncomp != cbasis.num_basis:
    raise ValueError(
        f"cop.ncomp ({cop.ncomp}) must equal the conf basis's num_basis "
        f"({cbasis.num_basis}); mul_conf_phase is single-field only")
  if pop.ncomp != pbasis.num_basis:
    raise ValueError(
        f"pop.ncomp ({pop.ncomp}) must equal the phase basis's num_basis "
        f"({pbasis.num_basis}); mul_conf_phase is single-field only")
  conf_cells = np.asarray(conf_cells, dtype=np.int32)
  phase_cells = np.asarray(phase_cells, dtype=np.int32)
  out = GkylArray.alloc(pop.ncomp, pop.size)
  _lib.require().dg_mul_conf_phase(cbasis._cap, pbasis._cap, out._cap,
      cop._cap, pop._cap, conf_cells, phase_cells)
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
  """Per-component MIN/MAX/SUM over all cells (gkyl_array_reduce).

  This reduces the raw DG **coefficients**: exact for ``"sum"`` (the sum of
  coefficients over cells is linear), but NOT the field's true min/max — a
  DG expansion can exceed its coefficient values between nodes. Use
  :func:`dg_reduce` for the field-aware version.
  """
  return _lib.require().array_reduce(a._cap, op)


def dg_reduce(basis_type: str, ndim: int, poly_order: int, a: GkylArray,
    comp: int, op: str) -> float:
  """MIN/MAX/SUM of the field ``comp`` actually represents (gkyl_array_dg_reducec).

  Evaluates the DG expansion at each cell's Gauss-Legendre quadrature nodes
  and reduces those values — the true min/max/sum of the represented field,
  exact for ``"sum"`` and correct (not merely coefficient-bounded) for
  ``"min"``/``"max"`` to quadrature precision (exact for polynomials the
  quadrature integrates exactly, i.e. always for a basis's own degree).

  Args:
    basis_type: ``"serendipity"`` or ``"tensor"``.
    ndim: number of dimensions the basis was built for.
    poly_order: polynomial order the basis was built for.
    a: array whose ``ncomp`` is a multiple of the basis's ``num_basis``.
    comp: 0-based field index (NOT a coefficient offset).
    op: one of ``"min"``, ``"max"``, ``"sum"``.

  Returns:
    The reduced scalar.

  Raises:
    ValueError: unknown ``op``, or ``comp`` out of range for ``a``'s fields.
  """
  if op not in REDUCE_OPS:
    raise ValueError(f"dg_reduce op '{op}' not in {sorted(REDUCE_OPS)}")
  basis = get_basis(basis_type, ndim, poly_order)
  nfields = _fields(a, basis.num_basis)
  if not 0 <= comp < nfields:
    raise ValueError(f"comp {comp} out of range for {nfields} field(s)")
  return float(_lib.require().array_dg_reduce(basis._cap, a._cap, comp,
      REDUCE_OPS[op]))


def integrate(grid: dict, basis_type: str, poly_order: int, a: GkylArray,
    op: str = "none", factor: float = 1.0) -> np.ndarray:
  """``int dx op(f)`` per field via ``gkyl_array_integrate`` — one value per field.

  ``grid`` is the dict from ``rio`` (ndim/lower/upper/cells). Guarded to the
  kernel set compiled into libg0core (serendipity p1-p2, ndim 1-3, for
  none/abs/sq) — ``gkyl_array_integrate_choose_kernel`` indexes its kernel
  table by ``ndim-1``/``poly_order-1`` with no bound past an
  ``assert(up->kernel)`` that a genuinely out-of-table ndim can dodge (an
  out-of-bounds array read that happens to be non-NULL), so ndim is checked
  here rather than left to that assert.
  """
  if op not in INTEGRATE_OPS:
    raise ValueError(f"integrate op '{op}' not in {sorted(INTEGRATE_OPS)}")
  if basis_type.lower() != "serendipity" or poly_order not in (1, 2):
    raise NotImplementedError(
        "gkyl_array_integrate kernels in libg0core cover serendipity p1-p2")
  ndim = int(grid["ndim"])
  if ndim not in (1, 2, 3):
    raise NotImplementedError(
        f"gkyl_array_integrate kernels in libg0core cover ndim 1-3, got {ndim}")
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
