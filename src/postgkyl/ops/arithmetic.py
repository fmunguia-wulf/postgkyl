"""Arithmetic / NumPy-ufunc backend for the fluent operators.

Defined here (in ``ops``) — not on the container — so the computing operators
follow the same one-way layering as every other verb (HIERARCHY_3.md).

Dispatch is on the container's ``backend`` (the two-domain lifecycle of
REFACTOR_GKEYLL_FFI.md):

- **gkyl-backed (modal) operands** run inside Gkeyll: ``*``/``/`` are the weak
  kernels (``gkyl_dg_mul_op``/``div_op``), ``+``/``-`` are coefficient linear
  combinations (``gkyl_array_set``/``accumulate``), scalar multiply is
  ``gkyl_array_scale``, scalar add shifts the mean coefficient, and integer
  powers are repeated weak multiplies. Results stay modal (gkyl-backed).
- **numpy-backed operands** take the unchanged NumPy path.
- **Mixing the domains** in one expression is an error naming the fix.
"""

from __future__ import annotations

import operator

import numpy as np

from postgkyl.core.state import GDataState
from postgkyl import dg, numerics


def _unpack(x):
  """(values, grid, dataset|None) for a dataset; (array, None, None) otherwise."""
  if isinstance(x, GDataState):
    return x.values, x.grid, x
  return np.asarray(x), None, None


def binary(op, a, b):
  """``a <op> b`` where at least one operand is a dataset; result copies its grid."""
  pa = a if isinstance(a, GDataState) else None
  pb = b if isinstance(b, GDataState) else None
  if (pa is not None and pa.backend == "gkyl") or (
      pb is not None and pb.backend == "gkyl"):
    return _modal_binary(op, a, b, pa, pb)
  return _numpy_binary(op, a, b, pa, pb)


# --------------------------------------------------------------- numpy domain
def _numpy_binary(op, a, b, pa, pb):
  va, ga, _ = _unpack(a)
  vb, gb, _ = _unpack(b)
  primary = pa if pa is not None else pb
  primary._require_operable()
  if pa is not None and pb is not None:
    pb._require_operable()
    if not numerics.grids_compatible(ga, gb):
      raise ValueError("operands live on different grids")
    if va.shape != vb.shape:
      raise ValueError(f"incompatible shapes {va.shape} vs {vb.shape}")
  # end
  return primary._result(primary.grid, op(va, vb))


# --------------------------------------------------------------- modal domain
def _basis_of(data: GDataState):
  """(basis_type, ndim, poly_order) from ctx — the modal ops' dispatch key."""
  basis_type = data.ctx.get("basis_type")
  poly_order = data.ctx.get("poly_order")
  if basis_type is None or poly_order is None:
    raise ValueError("modal operand has no basis_type/poly_order metadata")
  return str(basis_type), data.num_dims, int(poly_order)


def _modal_binary(op, a, b, pa, pb):
  if pa is not None and pb is not None:
    return _modal_dataset_pair(op, pa, pb)
  primary = pa if pa is not None else pb
  other = b if pa is not None else a
  if not isinstance(other, (int, float, np.integer, np.floating)):
    raise ValueError(
        "cannot mix native modal data with arrays; call .interp() on the "
        "modal operand first (or use scalars / another modal dataset).")
  return _modal_scalar(op, primary, float(other), scalar_first=pa is None)


def _rep_of(data: GDataState) -> str:
  return data.ctx.get("representation", "modal")


def _modal_dataset_pair(op, pa: GDataState, pb: GDataState):
  if pb.backend != "gkyl" or pa.backend != "gkyl":
    raise ValueError(
        "one operand is modal (gkyl-native) and the other is interpolated; "
        "call .interp() on the modal operand to combine them.")
  if not numerics.grids_compatible(pa.grid, pb.grid):
    raise ValueError("operands live on different grids")
  basis = _basis_of(pa)
  if _basis_of(pb) != basis:
    raise ValueError("operands have different DG bases")
  rep = _rep_of(pa)
  if rep != _rep_of(pb):
    raise ValueError(
        f"operands are in different representations ({rep} vs {_rep_of(pb)}); "
        "convert one explicitly (.to_modal()/.to_nodal()/.to_quad()).")
  A, B = pa.native, pb.native
  if op is operator.add:                       # linear: valid in any rep
    out = dg.modal.lincomb(1.0, A, 1.0, B)
  elif op is operator.sub:
    out = dg.modal.lincomb(1.0, A, -1.0, B)
  elif rep != "modal":
    # Point values (nodal/quad): every pointwise operation is exact — compute
    # with NumPy on the views, wrap back native, stay in-representation.
    out = dg.rep.wrap(op(np.asarray(pa.values), np.asarray(pb.values)))
  elif op in (operator.mul, operator.truediv):
    out = (dg.modal.weak_mul if op is operator.mul
           else dg.modal.weak_div)(*basis, A, B)
  else:
    raise ValueError(
        f"operation {getattr(op, '__name__', op)} is not defined between two "
        "modal datasets; .to_nodal()/.to_quad() for pointwise math.")
  return pa._result(pa.grid, out)


def _modal_scalar(op, data: GDataState, s: float, *, scalar_first: bool):
  basis = _basis_of(data)
  rep = _rep_of(data)
  A = data.native
  # In point-value representations (nodal/quad) a scalar shift moves every
  # component; in modal it moves only the mean coefficient.
  shift = (dg.modal.shift_all if rep != "modal"
           else lambda a, v: dg.modal.shift_mean(*basis, a, v))
  if op is operator.mul:                       # linear: valid in any rep
    out = dg.modal.scale(A, s)
  elif op is operator.truediv and not scalar_first:
    out = dg.modal.scale(A, 1.0 / s)           # f / s: linear, any rep
  elif op is operator.add:
    out = shift(A, s)
  elif op is operator.sub:
    if scalar_first:  # s - f
      out = shift(dg.modal.scale(A, -1.0), s)
    else:             # f - s
      out = shift(A, -s)
  elif rep != "modal":
    # Point values: any remaining scalar operation is exact pointwise.
    args = (s, np.asarray(data.values)) if scalar_first else (
        np.asarray(data.values), s)
    out = dg.rep.wrap(op(*args))
  elif op is operator.truediv:                 # s / f — weak reciprocal
    out = dg.modal.scale(dg.modal.weak_inv(*basis, A), s)
  elif op is operator.pow and not scalar_first:
    out = dg.modal.power(*basis, A, s if not float(s).is_integer() else int(s))
  else:
    raise ValueError(
        f"operation {getattr(op, '__name__', op)} is not defined for modal "
        "data and a scalar; .to_nodal()/.to_quad() for pointwise math.")
  return data._result(data.grid, out)


# ------------------------------------------------------------------- ufuncs
def apply_ufunc(ufunc, method, *inputs, **kwargs):
  """Backend for ``GData.__array_ufunc__`` — keeps the result a dataset.

  Ufuncs are pointwise, so they are valid wherever the data are point values:
  the NumPy field domain, and the nodal/quad representations (computed on the
  views, wrapped back native, staying in-representation). Modal coefficients
  refuse (via ``_require_operable``): a ufunc has no basis-space meaning.
  """
  if method != "__call__" or "out" in kwargs:
    return NotImplemented
  primary = next(x for x in inputs if isinstance(x, GDataState))
  primary._require_operable()
  rep = (_rep_of(primary) if primary.backend == "gkyl" else None)
  raw = []
  for x in inputs:
    if isinstance(x, GDataState):
      x._require_operable()
      if x.backend == "gkyl" and _rep_of(x) != rep or (
          x.backend != "gkyl" and rep is not None):
        raise ValueError(
            "operands are in different representations; convert one "
            "explicitly (.to_modal()/.to_nodal()/.to_quad()).")
      if x.values.shape != primary.values.shape:
        raise ValueError(
            f"incompatible shapes {x.values.shape} vs {primary.values.shape}")
      raw.append(np.asarray(x.values))
    elif isinstance(x, GDataState._HANDLED_TYPES):
      raw.append(x)
    else:
      return NotImplemented
    # end
  # end
  result = ufunc(*raw, **kwargs)
  if rep is not None:
    return primary._result(primary.grid, dg.rep.wrap(result))
  return primary._result(primary.grid, result)
