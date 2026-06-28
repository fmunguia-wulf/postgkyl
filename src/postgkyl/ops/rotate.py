"""The ``parrotate``/``perprotate`` verbs — rotate a vector field along/across
the unit vectors of a second (rotator) field."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.parrotate import parrotate as _parrotate
from postgkyl.tools.perprotate import perprotate as _perprotate

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def parrotate(array: "GData", rotator: "GData", *, coords: str = "0:3",
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Component of ``array`` parallel to ``rotator``: ``(u . v_hat) v_hat``.

  ``coords`` selects which rotator components form the direction vector
  (use '3:6' to rotate along the magnetic field of an EM field array).
  """
  grid, values = _parrotate(array, rotator, coords)
  return array._result(grid, values, inplace=inplace, tag=tag, label=label)


def perprotate(array: "GData", rotator: "GData", *, coords: str = "0:3",
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Component of ``array`` perpendicular to ``rotator``: ``u - (u . v_hat) v_hat``."""
  grid, values = _perprotate(array, rotator, coords)
  return array._result(grid, values, inplace=inplace, tag=tag, label=label)
