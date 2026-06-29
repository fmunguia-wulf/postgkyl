"""The ``integrate`` verb — integrate data over one or more axes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.calculus import integrate as _integrate_arrays

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def integrate(data: "GData", axis=None, *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Integrate data over one or more axes.

  Performs a cell-centered numeric integration (using the grid spacing as the
  measure) over the requested axes. Integrated axes are collapsed to a single
  cell whose coordinate is the axis mean. Works on non-uniform meshes.

  Args:
    data: GData
      The dataset to integrate.
    axis: int | tuple | str | None
      Axis or axes to integrate over. An integer single axis, a tuple of
      integer axes, a comma-separated string of axes (e.g. '0,2'), or an
      'i:j' slice string. When None, integrates over all dimensions.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData with the requested axes integrated out (or the mutated input
    when inplace=True).
  """
  grid, values = _integrate_arrays(data, axis)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
