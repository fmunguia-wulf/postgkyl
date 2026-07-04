"""The ``plot`` verb — terminal; hands the dataset to the render backend.

Point-value representations (nodal/quad) plot **directly**: their values are
materialized at the true physical point locations (a non-uniform mesh whose
cell centers coincide with the points — ``dg.rep.materialize``), then rendered
by the unchanged backend. Modal data refuses: coefficients are not plottable;
the user chooses ``.interp()``, ``.to_nodal()``, or ``.to_quad()`` explicitly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import dg, render

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def plot(data: "GDataState", **kwargs):
  """Render a single dataset. Returns the matplotlib figure."""
  if data.backend == "gkyl":
    rep = data.ctx.get("representation", "modal")
    if rep == "modal":
      raise ValueError(
          "modal DG coefficients are not plottable; choose explicitly: "
          ".interp() (uniform evaluation mesh), .to_nodal() or .to_quad() "
          "(plot at the basis/quadrature points).")
    edges, values = dg.rep.materialize(
        str(data.ctx["basis_type"]), data.num_dims,
        int(data.ctx["poly_order"]), data.native, data.grid, rep,
        data.ctx.get("num_quad"))
    data = data._result(edges, values)  # transient NumPy shadow for rendering
  # end
  return render.plot(data, **kwargs)
