"""The ``integrate`` verb — integrate data over one or more axes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.calculus import integrate as _integrate_arrays

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def integrate(data: "GData", axis=None, *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Integrate data over ``axis`` (int, tuple, or 'i,j'/'i:j' string).

  When ``axis`` is None, integrates over all dimensions. Returns a new
  ``GData`` by default; pass ``inplace=True`` to mutate ``data``.
  """
  grid, values = _integrate_arrays(data, axis)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
