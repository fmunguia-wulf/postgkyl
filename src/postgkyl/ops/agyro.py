"""The ``agyro`` verbs — measures of pressure-tensor agyrotropy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.pressure_diagnostics import get_agyro, get_gkyl_10m_agyro

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def agyro(pressure: "GData", bfield: "GData", *, measure: str = "frobenius",
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Agyrotropy from a pressure tensor and an EM field.

  ``measure`` is 'frobenius' (Frobenius norm of the agyrotropic tensor) or
  'swisdak' (Swisdak 2015).
  """
  grid, values = get_agyro(pressure, bfield, measure=measure)
  return pressure._result(grid, values, inplace=inplace, tag=tag, label=label)


def mom_agyro(species: "GData", field: "GData", *, measure: str = "frobenius",
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Agyrotropy from 10-moment species data and an EM field."""
  grid, values = get_gkyl_10m_agyro(species, field, measure=measure)
  return species._result(grid, values, inplace=inplace, tag=tag, label=label)
