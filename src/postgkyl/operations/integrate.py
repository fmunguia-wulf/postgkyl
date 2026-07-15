"""The ``integrate`` verb family — grid integrals, two domains.

``integrate`` is a *terminal* verb (like ``info``): it returns numbers, not a
dataset. The integral runs entirely inside Gkeyll (``gkyl_array_integrate``)
on the native DG coefficients — no interpolation involved, and exact for the
basis.

``integrate_axis`` is the NumPy trapezoidal counterpart (``postgkyl.tools.
calculus.integrate`` in the legacy tree, ported verbatim to ``numerics.
calculus.integrate`` and wired here): it collapses one or more axes of
point-value data and returns a new (reduced) dataset, like ``select``. It
never touches raw modal coefficients — nodal/quad representations are
materialized to their true point locations first (the same bridge ``plot``
uses); modal data must be converted explicitly first.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl import dg, numerics

from ._materialize import materialize_for_render

if TYPE_CHECKING:
  from postgkyl.gdatastate.gdatastate import GDataState
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
        "it is not available after .interpolate() or without the Gkeyll library.")
  # end
  if data.ctx.get("representation", "modal") != "modal":
    raise ValueError(
        f"integrate expects the modal representation, not "
        f"'{data.ctx['representation']}'; call .to_modal() first.")
  # end
  basis_type = data.ctx.get("basis_type")
  poly_order = data.ctx.get("poly_order")
  if basis_type is None or poly_order is None:
    raise ValueError("dataset has no basis_type/poly_order metadata")
  # end
  grid = {
      "ndim": data.num_dims,
      "lower": np.asarray(data.ctx["lower"]),
      "upper": np.asarray(data.ctx["upper"]),
      "cells": np.asarray(data.ctx["cells"]),
  }
  result = dg.modal.integrate(grid, str(basis_type), int(poly_order),
      data.native, op=op)
  return float(result[0]) if result.size == 1 else result
# end


def integrate_axis(data: "GDataState", axis: int | tuple | str | None = None, *,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """``int dz`` over one or more axes of point-value data (non-terminal).

  Args:
    data: point-value dataset -- already-interpolated (NumPy) data, or a
      native ``nodal``/``quad`` representation (materialized to its true
      point locations first). Raw modal DG coefficients raise; convert
      explicitly first (``.interpolate()``, ``.to_nodal()``, ``.to_quad()``).
    axis: axis (or axes) to integrate over: an ``int``, a ``tuple`` of
      ``int``, a comma-separated string (``"0,1"``), a colon slice string
      (``"0:2"``), or ``None`` (integrate over every axis).

  Returns:
    A new dataset with the integrated axes collapsed to a single, grid-mean
    cell (shape retained, like ``select``). Always NumPy-backed, whatever the
    input's representation (like ``.interpolate()``'s result): stamped
    ``interpolated=True`` and cleared of any stale ``representation`` tag so
    ``info``/``repr`` don't keep describing collapsed values as "modal".
  """
  data._require_operable()  # the one home for "is this point-value data"
  shadow = materialize_for_render(data)
  grid, values = numerics.integrate(shadow.grid, shadow.values, axis)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label,
      interpolated=True, representation=None)
# end
