"""The ``magsq`` verb — magnitude squared of a vector field."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.mag_sq import mag_sq as _mag_sq

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def magsq(data: "GData", *, coords: str = "0:3", inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Magnitude squared of a vector field.

  Computes the sum of squares of the selected components, returning a scalar
  (single-component) field. The components are assumed to live on the last
  axis.

  Args:
    data: GData
      The dataset holding the vector field.
    coords: str
      Half-open 'lo:hi' slice string selecting which components to square and
      sum. Defaults to '0:3' (the first three components).
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new single-component GData of the magnitude squared (or the mutated input
    when inplace=True).
  """
  grid, values = _mag_sq(data, coords=coords)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
