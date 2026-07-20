"""The ``plotly_animate`` verb — terminal; hands a sequence of datasets to the
Plotly render backend's animation engine.

Mirrors ``operations/animate.py``, minus the "a frame may itself be a list of
datasets drawn together" flexibility: a Plotly animation frame is one
trace-set, so ``data`` is always a flat, one-dataset-per-frame sequence.
"""

from __future__ import annotations

from postgkyl import render

from ._materialize import materialize_for_render


def plotly_animate(data, **kwargs):
  """Animate a flat sequence of datasets, one Plotly frame per dataset.

  Every dataset is bridged through :func:`_materialize.materialize_for_render`
  first (see ``render.plotly.plotly_animate``). ``save``/``saveas``/``show``
  are handled entirely by the render layer, and default to inert -- pass
  ``show=True`` to open the animation in the browser, or
  ``save=True``/``saveas=...`` to write it. Returns the Plotly figure.
  """
  frames = [materialize_for_render(dat) for dat in data]
  return render.plotly_animate(frames, **kwargs)
# end
