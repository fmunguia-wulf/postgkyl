"""The ``transform_frame`` verb — shift a distribution function to a new frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import models
from ._guards import require_field_domain as _require_field_domain

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

_REASON = "shifting the grid of raw DG coefficients has no basis-space meaning"


def transform_frame(distribution: "GDataState", bulk: "GDataState", *,
    cdim: int, inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Shift a distribution function to a moving frame of reference.

  Shifts the velocity-space grid of ``distribution`` by the local ``bulk``
  velocity so the distribution is expressed in the frame co-moving with
  the bulk flow. The values are unchanged; only the velocity coordinates
  are offset. Supports 1, 2, or 3 configuration-space dimensions.

  Args:
    distribution: The particle distribution function to shift; must be
      NumPy-backed.
    bulk: The bulk (drift) velocity field; one component per velocity
      dimension. Must be NumPy-backed.
    cdim: Number of configuration-space dimensions. The remaining grid
      axes are treated as velocity-space dimensions.
    inplace: mutate and return ``distribution`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset with the same values on a velocity-shifted grid.

  Raises:
    ValueError: if either input is native modal (gkyl-backed).
  """
  _require_field_domain(distribution, "transform_frame", _REASON)
  _require_field_domain(bulk, "transform_frame", _REASON)
  grid, values = models.transform_frame(distribution.grid, distribution.values,
      bulk.values, cdim)
  return distribution._result(grid, values, inplace=inplace, tag=tag,
      label=label)
