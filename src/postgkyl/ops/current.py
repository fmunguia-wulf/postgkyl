"""The ``current`` verb — accumulate current from species moments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.accumulate_current import accumulate_current as _accumulate_current

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def current(data: "GData", *, qbym: bool = False, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Accumulate current (sum of charge x flow over species).

  With ``qbym=True`` the charge/mass ratio is used instead of the charge.
  """
  grid, values = _accumulate_current(data, qbym)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
