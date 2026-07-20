"""The ``plotly`` verb — terminal; hands the dataset to the Plotly render backend.

Mirrors ``operations/plot.py``: point-value representations (nodal/quad) plot
directly via ``materialize_for_render``; raw modal coefficients refuse (the
user chooses ``.interpolate()``, ``.to_nodal()``, or ``.to_quad()`` first).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import render

from ._materialize import materialize_for_render

if TYPE_CHECKING:
  from postgkyl.gdatastate.gdatastate import GDataState
# end


def plotly(data: "GDataState", **kwargs):
  """Render a single dataset with Plotly (terminal verb; see ``render.plotly``).

  ``save``/``saveas``/``show`` (and the rotating-export camera parameters)
  are handled entirely by ``render.plotly``, and default to inert -- pass
  ``show=True`` for an auto-rotating browser preview, or
  ``save=True``/``saveas=...`` to write it. Returns the Plotly figure.
  """
  return render.plotly(materialize_for_render(data), **kwargs)
# end
