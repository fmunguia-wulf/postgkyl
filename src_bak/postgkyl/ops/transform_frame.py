"""The ``transform_frame`` verb — shift a distribution function to a new frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.transform_frame import transform_frame as _transform_frame

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def transform_frame(distribution: "GData", bulk: "GData", *, cdim: int,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Shift a distribution function to a moving frame of reference.

  Shifts the velocity-space grid of ``distribution`` by the local ``bulk``
  velocity so the distribution is expressed in the frame co-moving with the
  bulk flow. The values are unchanged; only the velocity coordinates are
  offset. Supports 1, 2, or 3 configuration-space dimensions.

  Args:
    distribution: GData
      The particle distribution function to shift.
    bulk: GData
      The bulk (drift) velocity field; one component per velocity dimension.
    cdim: int
      Number of configuration-space dimensions. The remaining grid axes are
      treated as velocity-space dimensions.
    inplace: bool
      When True, mutate and return ``distribution``; otherwise return a new
      GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData with the same values on a velocity-shifted grid (or the mutated
    ``distribution`` when inplace=True).
  """
  grid, values = _transform_frame(distribution, bulk, cdim)
  return distribution._result(grid, values, inplace=inplace, tag=tag, label=label)
