"""The ``plot`` verb — terminal; hands the dataset to the render backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import render

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def plot(data: "GDataState", **kwargs):
  """Render a single dataset. Returns the matplotlib figure."""
  return render.plot(data, **kwargs)
