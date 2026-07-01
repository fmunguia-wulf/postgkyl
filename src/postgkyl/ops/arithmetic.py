"""Arithmetic / NumPy-ufunc backend for the fluent operators.

Defined here (in ``ops``) — not on the container — so the computing operators
follow the same one-way layering as every other verb. See HIERARCHY_3.md.
"""

from __future__ import annotations

import numpy as np

from postgkyl.core.state import GDataState
from postgkyl import numerics


def _unpack(x):
  """(values, grid, dataset|None) for a dataset; (array, None, None) otherwise."""
  if isinstance(x, GDataState):
    return x.values, x.grid, x
  return np.asarray(x), None, None


def binary(op, a, b):
  """``a <op> b`` where at least one operand is a dataset; result copies its grid."""
  va, ga, pa = _unpack(a)
  vb, gb, pb = _unpack(b)
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


def apply_ufunc(ufunc, method, *inputs, **kwargs):
  """Backend for ``GData.__array_ufunc__`` — keeps the result a dataset."""
  if method != "__call__" or "out" in kwargs:
    return NotImplemented
  primary = next(x for x in inputs if isinstance(x, GDataState))
  primary._require_operable()
  raw = []
  for x in inputs:
    if isinstance(x, GDataState):
      x._require_operable()
      if x.values.shape != primary.values.shape:
        raise ValueError(
            f"incompatible shapes {x.values.shape} vs {primary.values.shape}")
      raw.append(x.values)
    elif isinstance(x, GDataState._HANDLED_TYPES):
      raw.append(x)
    else:
      return NotImplemented
    # end
  # end
  return primary._result(primary.grid, ufunc(*raw, **kwargs))
