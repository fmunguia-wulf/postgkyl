"""The ``local_poly`` verb — modal DG coefficients -> a discontinuity-
preserving plotting mesh (see ``dg.local_poly``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import dg
from postgkyl.ops.interpolate import BASIS_MAP

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def local_poly(data: "GDataState", *, basis: str | None = None,
    p: int | None = None, npoints: int = 2, inplace: bool = False,
    tag: str | None = None, label: str | None = None):
  """Evaluate the DG polynomial cell-by-cell onto a plotting mesh that keeps
  every inter-cell discontinuity visible, instead of the continuous refined
  mesh ``interpolate`` produces.

  ``npoints`` reference points span the whole cell (``[-1, 1]``, endpoints
  included) and a NaN is spliced in at every cell interface, so a plot breaks
  the curve there rather than drawing a spuriously smooth line across it.

  Basis/order default to ``data.ctx``, same as ``interpolate``. The result is
  flagged ``interpolated=True`` so it becomes safe for element-wise math.
  """
  if basis is not None:
    if basis not in BASIS_MAP:
      raise ValueError(f"Unknown basis '{basis}'. Choices: {sorted(BASIS_MAP)}")
    # end
    basis_type, modal = BASIS_MAP[basis]
  # end
  else:
    basis_type = data.ctx.get("basis_type")
    if not basis_type:
      raise ValueError("No 'basis' given and the dataset has no stored 'basis_type'.")
    # end
    modal = data.ctx.get("is_modal", True)
  # end

  poly_order = p if p is not None else data.ctx.get("poly_order")
  if poly_order is None:
    raise ValueError("No polynomial order given and none stored in the dataset.")
  # end

  if data.backend == "gkyl" and data.ctx.get("representation", "modal") != "modal":
    raise ValueError(
        f"local_poly expects the modal representation, not "
        f"'{data.ctx['representation']}'; call .to_modal() first.")
  # end

  grid, values = dg.local_poly(data.values, data.grid, poly_order=poly_order,
      basis_type=basis_type, modal=modal, npoints=npoints)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label,
      interpolated=True)
# end
