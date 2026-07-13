"""The ``animate`` verb — terminal; hands a sequence of datasets to the
render backend's animation engine.

Mirrors ``ops/plot.py``: each modal dataset in the sequence is bridged
through its NumPy shadow (point-value representations plot directly; modal
coefficients refuse) via the shared ``_materialize.materialize_for_render``
before the frames reach :func:`postgkyl.render.animate.animate`.
"""

from __future__ import annotations

from postgkyl import render
from postgkyl.core.state import GDataState

from ._materialize import materialize_for_render


def animate(data, **kwargs):
  """Animate a sequence of frames (see ``render.animate.animate``).

  ``data`` is a flat iterable of datasets (one dataset per frame) or an
  iterable of frames, where each frame is itself a list of datasets drawn
  together. Every dataset is bridged through
  :func:`_materialize.materialize_for_render` first, so the caller may
  freely mix modal and already-interpolated datasets.
  """
  frames = []
  for item in data:
    if isinstance(item, GDataState):
      frames.append(materialize_for_render(item))
    # end
    else:
      frames.append([materialize_for_render(dat) for dat in item])
    # end
  # end
  return render.animate.animate(frames, **kwargs)
# end
