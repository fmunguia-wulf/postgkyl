"""The ``transform_frame`` verb — shift a distribution function to a new frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.transform_frame import transform_frame as _transform_frame

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def transform_frame(distribution: "GData", bulk: "GData", *, cdim: int,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Shift a (PKPM) distribution function ``distribution`` to the frame moving
  with the ``bulk`` velocity. ``cdim`` is the number of configuration-space
  dimensions."""
  grid, values = _transform_frame(distribution, bulk, cdim)
  return distribution._result(grid, values, inplace=inplace, tag=tag, label=label)
