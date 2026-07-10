"""The shared "bridge modal data to its plottable NumPy shadow" logic.

Centralizes the check-and-bridge that ``plot`` and ``animate`` both need:
point-value representations (nodal/quad) materialize directly at their true
physical point locations; raw modal coefficients refuse -- the caller must
choose ``.interp()``, ``.to_nodal()``, or ``.to_quad()`` explicitly. One home
for the fact, mirroring ``ops/_guards.py``'s centralization of the analogous
field-domain check.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import dg

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def materialize_for_render(data: "GDataState") -> "GDataState":
  """Bridge one modal dataset to its plottable NumPy shadow.

  Args:
    data: Dataset to bridge; returned unchanged if already NumPy-backed.

  Returns:
    A NumPy-backed dataset (a transient shadow, for the caller's render
    backend) ready to plot/animate.

  Raises:
    ValueError: ``data`` holds native modal (gkyl-backed) DG coefficients.
  """
  if data.backend != "gkyl":
    return data
  # end
  rep = data.ctx.get("representation", "modal")
  if rep == "modal":
    raise ValueError(
        "modal DG coefficients are not plottable; choose explicitly: "
        ".interp() (uniform evaluation mesh), .to_nodal() or .to_quad() "
        "(plot at the basis/quadrature points).")
  # end
  edges, values = dg.rep.materialize(
      str(data.ctx["basis_type"]), data.num_dims,
      int(data.ctx["poly_order"]), data.native, data.grid, rep,
      data.ctx.get("num_quad"))
  return data._result(edges, values)
