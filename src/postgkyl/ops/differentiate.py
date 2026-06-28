"""The ``differentiate`` verb — interpolate a derivative of DG data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.ops._dg import make_interpolator

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def differentiate(data: "GData", *, basis: str | None = None, p: int | None = None,
    interp: int | None = None, read: bool | None = None, direction: int | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Interpolate a derivative of DG data onto a uniform mesh.

  ``direction`` selects the derivative axis (default: all). Other arguments
  match :func:`postgkyl.ops.interpolate`. The result is flagged
  ``interpolated=True``.
  """
  dg = make_interpolator(data, basis=basis, p=p, interp=interp, read=read)
  grid, values = dg.differentiate(direction=direction)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label,
      interpolated=True)
