"""The ``energetics`` verb — decompose plasma energy components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.energetics import energetics as _energetics

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def energetics(elc: "GData", ion: "GData", field: "GData", *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Decompose energy (kinetic, thermal, EM) for a two-species plasma.

  Returns a 7-component dataset carrying the EM field's grid/metadata.
  """
  grid, values = _energetics(elc, ion, field)
  return field._result(grid, values, inplace=inplace, tag=tag, label=label)
