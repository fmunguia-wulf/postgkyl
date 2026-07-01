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

  Projects the three-component vector field ``array`` (u) onto the unit vector
  of the ``rotator`` field (v), returning the parallel vector
  ``(u . v_hat) v_hat`` with its x, y, z components. Both fields are assumed
  to be three-component with components on the last axis.

  Args:
    array: GData
      The three-component vector field to be rotated/projected.
    rotator: GData
      The field defining the rotation direction.
    coords: str
      Half-open 'lo:hi' slice string selecting which ``rotator`` components
      form the direction vector. Defaults to '0:3'; use '3:6' to rotate along
      the magnetic field of a six-component EM field.
    inplace: bool
      When True, mutate and return ``array``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new three-component GData of the parallel projection (or the mutated
    ``array`` when inplace=True).
  """
  grid, values = _parrotate(array, rotator, coords)
  return array._result(grid, values, inplace=inplace, tag=tag, label=label)


def perprotate(array: "GData", rotator: "GData", *, coords: str = "0:3",
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Component of ``array`` perpendicular to ``rotator``: ``u - (u . v_hat) v_hat``.

  Returns the part of the three-component vector field ``array`` (u) that is
  perpendicular to the ``rotator`` field (v), i.e. ``u - (u . v_hat) v_hat``.
  Both fields are assumed to be three-component with components on the last
  axis.

  Args:
    array: GData
      The three-component vector field to be rotated/projected.
    rotator: GData
      The field defining the rotation direction.
    coords: str
      Half-open 'lo:hi' slice string selecting which ``rotator`` components
      form the direction vector. Defaults to '0:3'; use '3:6' to rotate along
      the magnetic field of a six-component EM field.
    inplace: bool
      When True, mutate and return ``array``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new three-component GData of the perpendicular component (or the mutated
    ``array`` when inplace=True).
  """
  grid, values = _perprotate(array, rotator, coords)
  return array._result(grid, values, inplace=inplace, tag=tag, label=label)
