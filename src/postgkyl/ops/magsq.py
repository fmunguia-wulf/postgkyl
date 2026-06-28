"""The ``magsq`` verb — magnitude squared of a vector field."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.mag_sq import mag_sq as _mag_sq

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def magsq(data: "GData", *, coords: str = "0:3", inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Magnitude squared of the components selected by ``coords`` ('lo:hi')."""
  grid, values = _mag_sq(data, coords=coords)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
