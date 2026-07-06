"""The ``integrate`` verb — grid integrals of modal data via Gkeyll.

A *terminal* verb (like ``info``): it returns numbers, not a dataset. The
integral runs entirely inside Gkeyll (``gkyl_array_integrate``) on the native
DG coefficients — no interpolation involved, and exact for the basis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl import dg

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def integrate(data: "GDataState", *, op: str = "none"):
  """``int dx op(f)`` over the whole grid, one value per field component.

  Args:
    data: a gkyl-backed (native modal) dataset.
    op: ``"none"`` (plain integral), ``"abs"``, or ``"sq"``.

  Returns:
    A float for single-field data, else a ``(num_fields,)`` NumPy array.
  """
  if data.backend != "gkyl":
    raise ValueError(
        "integrate wraps gkyl_array_integrate and needs native modal data; "
        "it is not available after .interp() or without the Gkeyll library.")
  if data.ctx.get("representation", "modal") != "modal":
    raise ValueError(
        f"integrate expects the modal representation, not "
        f"'{data.ctx['representation']}'; call .to_modal() first.")
  basis_type = data.ctx.get("basis_type")
  poly_order = data.ctx.get("poly_order")
  if basis_type is None or poly_order is None:
    raise ValueError("dataset has no basis_type/poly_order metadata")
  grid = {
      "ndim": data.num_dims,
      "lower": np.asarray(data.ctx["lower"]),
      "upper": np.asarray(data.ctx["upper"]),
      "cells": np.asarray(data.ctx["cells"]),
  }
  result = dg.modal.integrate(grid, str(basis_type), int(poly_order),
      data.native, op=op)
  return float(result[0]) if result.size == 1 else result
