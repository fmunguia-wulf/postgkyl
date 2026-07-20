"""Visualization backends (a backend layer used by the fluent surface).

Re-exporting the ``plotly`` *function* here (below) shadows the
``postgkyl.render.plotly`` *submodule* reference the import machinery would
otherwise set on this package -- ``pg.render.plotly`` resolves to the
function, matching every other backend's top-level spelling (``pg.render.plot``,
``pg.render.pyvista``). The submodule's other names (``open_preview``,
``save_rotating_plotly_figure``) are re-exported alongside it here for the
same reason: reaching them via ``pg.render.plotly.<name>`` would not work
once ``plotly`` means the function.
"""

from . import animate, labels, style
from .matplotlib import plot
from .plotly import open_preview, plotly, plotly_animate, save_rotating_plotly_figure
from .pyvista import pyvista

__all__ = ["plot", "animate", "labels", "style", "plotly", "plotly_animate",
    "save_rotating_plotly_figure", "open_preview", "pyvista"]
