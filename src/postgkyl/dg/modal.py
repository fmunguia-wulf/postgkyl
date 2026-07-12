"""Modal (DG-coefficient) operations — thin orchestration over Gkeyll kernels.

Everything here acts on native :class:`~postgkyl.gpython.array.GkylArray` data and
returns native data (or plain numbers for reductions): the modal domain never
leaves Gkeyll's memory. The only logic this layer adds over ``gpython.kernels`` is
DG bookkeeping — e.g. what "add a scalar" means for modal coefficients.
"""

from __future__ import annotations

import numpy as np

from postgkyl import gpython
from postgkyl.gpython.array import GkylArray

# Weak algebra and coefficient linear combinations — direct kernel calls.
weak_mul = gpython.kernels.weak_mul
weak_div = gpython.kernels.weak_div
weak_inv = gpython.kernels.weak_inv
weak_mul_conf_phase = gpython.kernels.weak_mul_conf_phase
lincomb = gpython.kernels.lincomb
scale = gpython.kernels.scale
integrate = gpython.kernels.integrate
reduce = gpython.kernels.reduce


def shift_mean(basis_type: str, ndim: int, poly_order: int,
    a: GkylArray, val: float) -> GkylArray:
  """``f + val`` for a modal field: only the mean coefficient moves.

  The normalized constant basis function is ``b_0 = 2^(-ndim/2)``, so a shift
  of the field by ``val`` is a shift of coefficient 0 by ``val * 2^(ndim/2)``,
  applied per field (``gkyl_array_shiftc`` on each field's coefficient 0).
  """
  nb = gpython.basis.num_basis(basis_type, ndim, poly_order)
  coeff_shift = float(val) * 2.0 ** (ndim / 2.0)
  out = a
  for f in range(a.ncomp // nb):
    out = gpython.kernels.shiftc(out, coeff_shift, f * nb)
  return out


def shift_all(a: GkylArray, val: float) -> GkylArray:
  """``values + val`` for point-value representations (nodal/quad): every
  component of every cell is a field value, so shift them all."""
  out = a.clone()
  for k in range(a.ncomp):
    out = gpython.kernels.shiftc(out, float(val), k)
  return out


def power(basis_type: str, ndim: int, poly_order: int,
    a: GkylArray, exponent) -> GkylArray:
  """``f ** n`` for a positive integer ``n``, as repeated weak multiplies."""
  n = exponent
  if not (isinstance(n, (int, np.integer)) and n >= 1):
    raise ValueError(
        f"modal power supports positive integer exponents only, got {n!r}; "
        "interpolate first for general powers.")
  out = a.clone()
  for _ in range(int(n) - 1):
    out = weak_mul(basis_type, ndim, poly_order, out, a)
  return out
