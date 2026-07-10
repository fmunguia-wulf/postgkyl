"""The ``agyro`` verbs — measures of pressure-tensor agyrotropy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import models
from ._guards import require_field_domain as _require_field_domain

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

_REASON = "computing agyrotropy from raw DG coefficients would mix basis functions"


def agyro(pressure: "GDataState", bfield: "GDataState", *,
    measure: str = "frobenius", inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Agyrotropy from a pressure tensor and an EM field.

  Measures how far the pressure tensor departs from gyrotropy about the
  local magnetic field. The field's first three components are used as the
  magnetic field direction.

  Args:
    pressure: Six-component symmetric pressure tensor (Pxx, Pxy, Pxz, Pyy,
      Pyz, Pzz); must be NumPy-backed.
    bfield: Magnetic field whose first three components are (Bx, By, Bz);
      must be NumPy-backed.
    measure: 'frobenius' (Frobenius norm of the agyrotropic part of the
      pressure tensor) or 'swisdak' (the Q measure of Swisdak 2015).
      Case-insensitive.
    inplace: mutate and return ``pressure`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A single-component dataset of the agyrotropy.

  Raises:
    ValueError: if either input is native modal (gkyl-backed), or
      ``measure`` is not 'frobenius' or 'swisdak'.
  """
  _require_field_domain(pressure, "agyro", _REASON)
  _require_field_domain(bfield, "agyro", _REASON)
  grid, values = models.get_agyro(pressure.grid, pressure.values,
      bfield.grid, bfield.values, measure=measure)
  return pressure._result(grid, values, inplace=inplace, tag=tag, label=label)


def mom_agyro(species: "GDataState", field: "GDataState", *,
    measure: str = "frobenius", inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Agyrotropy from 10-moment species data and an EM field.

  Convenience wrapper that first forms the pressure tensor from raw
  10-moment species data and extracts the magnetic field (components 3:6)
  from a Gkeyll EM field, then computes the agyrotropy.

  Args:
    species: Raw 10-moment fluid data for a single species (density,
      momentum, and the six pressure-tensor moments); must be NumPy-backed.
    field: Gkeyll EM field whose components 3:6 are the magnetic field (Bx,
      By, Bz); must be NumPy-backed.
    measure: 'frobenius' (Frobenius norm of the agyrotropic part of the
      pressure tensor) or 'swisdak' (the Q measure of Swisdak 2015).
      Case-insensitive.
    inplace: mutate and return ``species`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A single-component dataset of the agyrotropy.

  Raises:
    ValueError: if either input is native modal (gkyl-backed), or
      ``measure`` is not 'frobenius' or 'swisdak'.
  """
  _require_field_domain(species, "mom_agyro", _REASON)
  _require_field_domain(field, "mom_agyro", _REASON)
  grid, values = models.get_gkyl_10m_agyro(species.grid, species.values,
      field.grid, field.values, measure=measure)
  return species._result(grid, values, inplace=inplace, tag=tag, label=label)
