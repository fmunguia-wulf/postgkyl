"""The ``interpolate`` verb — DG coefficients -> values on a uniform mesh."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import dg

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

# Short basis code -> (long basis name, is_modal)
BASIS_MAP = {
    "ms": ("serendipity", True),
    "ns": ("serendipity", False),
    "mo": ("maximal-order", True),
    "mt": ("tensor", True),
    "gkhyb": ("gkhybrid", True),
    "pkpmhyb": ("hybrid", True),
}


def interpolate(data: "GDataState", *, basis: str | None = None,
    p: int | None = None, num_interp: int | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """Interpolate DG (modal/nodal) data onto a uniform evaluation mesh.

  Basis/order default to ``data.ctx``. The result is flagged
  ``interpolated=True`` so it becomes safe for element-wise math.
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
        f"interpolate expects the modal representation, not "
        f"'{data.ctx['representation']}'; call .to_modal() first.")
  # end

  grid, values = dg.interpolate(data.values, data.grid, poly_order=poly_order,
      basis_type=basis_type, modal=modal, num_interp=num_interp)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label,
      interpolated=True)
# end
