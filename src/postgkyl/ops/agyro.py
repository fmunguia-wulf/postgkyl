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

  Measures how far the pressure tensor departs from gyrotropy about the local
  magnetic field. The field's first three components are used as the magnetic
  field direction.

  Args:
    pressure: GData
      Six-component symmetric pressure tensor (Pxx, Pxy, Pxz, Pyy, Pyz, Pzz).
    bfield: GData
      Magnetic field whose first three components are (Bx, By, Bz).
    measure: str
      Agyrotropy measure: 'frobenius' (Frobenius norm of the agyrotropic part
      of the pressure tensor) or 'swisdak' (the Q measure of Swisdak 2015).
      Case-insensitive. Defaults to 'frobenius'.
    inplace: bool
      When True, mutate and return ``pressure``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new single-component GData of the agyrotropy (or the mutated
    ``pressure`` when inplace=True).

  Raises:
    ValueError: If ``measure`` is not 'frobenius' or 'swisdak'.
  """
  grid, values = get_agyro(pressure, bfield, measure=measure)
  return pressure._result(grid, values, inplace=inplace, tag=tag, label=label)


def mom_agyro(species: "GData", field: "GData", *, measure: str = "frobenius",
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Agyrotropy from 10-moment species data and an EM field.

  Convenience wrapper that first forms the pressure tensor from raw 10-moment
  species data and extracts the magnetic field (components 3:6) from a Gkeyll
  EM field, then computes the agyrotropy.

  Args:
    species: GData
      Raw 10-moment fluid data for a single species (density, momentum, and
      the six pressure-tensor moments).
    field: GData
      Gkeyll EM field whose components 3:6 are the magnetic field (Bx, By, Bz).
    measure: str
      Agyrotropy measure: 'frobenius' (Frobenius norm of the agyrotropic part
      of the pressure tensor) or 'swisdak' (the Q measure of Swisdak 2015).
      Case-insensitive. Defaults to 'frobenius'.
    inplace: bool
      When True, mutate and return ``species``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new single-component GData of the agyrotropy (or the mutated ``species``
    when inplace=True).

  Raises:
    ValueError: If ``measure`` is not 'frobenius' or 'swisdak'.
  """
  grid, values = get_gkyl_10m_agyro(species, field, measure=measure)
  return species._result(grid, values, inplace=inplace, tag=tag, label=label)
