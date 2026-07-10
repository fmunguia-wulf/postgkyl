"""The ``parrotate``/``perprotate`` verbs — rotate a vector field along/across
the unit vectors of a second (rotator) field."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import models
from ._guards import require_field_domain as _require_field_domain

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

_REASON = "rotating raw DG coefficients would mix basis functions"


def parrotate(array: "GDataState", rotator: "GDataState", *,
    coords: str = "0:3", inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Component of ``array`` parallel to ``rotator``: ``(u . v_hat) v_hat``.

  Projects the three-component vector field ``array`` (u) onto the unit
  vector of the ``rotator`` field (v), returning the parallel vector
  ``(u . v_hat) v_hat`` with its x, y, z components. Both fields are
  assumed to be three-component with components on the last axis.

  Args:
    array: The three-component vector field to be rotated/projected; must
      be NumPy-backed.
    rotator: The field defining the rotation direction; must be
      NumPy-backed.
    coords: Half-open 'lo:hi' slice string selecting which ``rotator``
      components form the direction vector. Defaults to '0:3'; use '3:6'
      to rotate along the magnetic field of a six-component EM field.
    inplace: mutate and return ``array`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A three-component dataset of the parallel projection.

  Raises:
    ValueError: if either input is native modal (gkyl-backed), or the
      component counts do not match a three-component field.
  """
  _require_field_domain(array, "parrotate", _REASON)
  _require_field_domain(rotator, "parrotate", _REASON)
  grid, values = models.parrotate(array.grid, array.values, rotator.values,
      rotate_coords=coords)
  return array._result(grid, values, inplace=inplace, tag=tag, label=label)


def perprotate(array: "GDataState", rotator: "GDataState", *,
    coords: str = "0:3", inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Component of ``array`` perpendicular to ``rotator``:
  ``u - (u . v_hat) v_hat``.

  Both fields are assumed to be three-component with components on the
  last axis.

  Args:
    array: The three-component vector field to be rotated/projected; must
      be NumPy-backed.
    rotator: The field defining the rotation direction; must be
      NumPy-backed.
    coords: Half-open 'lo:hi' slice string selecting which ``rotator``
      components form the direction vector. Defaults to '0:3'; use '3:6'
      to rotate along the magnetic field of a six-component EM field.
    inplace: mutate and return ``array`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A three-component dataset of the perpendicular component.

  Raises:
    ValueError: if either input is native modal (gkyl-backed), or the
      component counts do not match a three-component field.
  """
  _require_field_domain(array, "perprotate", _REASON)
  _require_field_domain(rotator, "perprotate", _REASON)
  grid, values = models.perprotate(array.grid, array.values, rotator.values,
      rotate_coords=coords)
  return array._result(grid, values, inplace=inplace, tag=tag, label=label)
