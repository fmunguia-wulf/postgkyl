"""The ``energetics`` verb — decompose plasma energy components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import models
from ._guards import require_field_domain as _require_field_domain

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

_REASON = "decomposing energy from raw DG coefficients would mix basis functions"


def energetics(elc: "GDataState", ion: "GDataState", field: "GDataState", *,
    gas_gamma: float = 5.0 / 3, num_moms: int | None = None,
    inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Decompose energy (kinetic, thermal, EM) for a two-species plasma.

  Splits the plasma energy into its constituent parts for a two-species
  (electron/ion) plasma plus an EM field. The result carries the EM
  field's grid and metadata and has seven components, in order:

  0. electron thermal energy
  1. electron kinetic energy
  2. ion thermal energy
  3. ion kinetic energy
  4. electric field energy (|E|^2 / 2)
  5. magnetic field energy (|B|^2 / 2)
  6. total energy (sum of the above)

  Args:
    elc: Electron fluid moments (used to compute thermal pressure and
      kinetic energy); must be NumPy-backed.
    ion: Ion fluid moments (used to compute thermal pressure and kinetic
      energy); must be NumPy-backed.
    field: EM field whose components 0:3 are the electric field and 3:6
      are the magnetic field; its grid/metadata are carried to the output.
      Must be NumPy-backed.
    gas_gamma: Adiabatic index, forwarded to the pressure/kinetic-energy
      calculation for both species.
    num_moms: Number of moments (5 or 10) for both species; inferred from
      the component count when ``None``.
    inplace: mutate and return ``field`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A seven-component dataset of the energy decomposition.

  Raises:
    ValueError: if any input is native modal (gkyl-backed).
  """
  _require_field_domain(elc, "energetics", _REASON)
  _require_field_domain(ion, "energetics", _REASON)
  _require_field_domain(field, "energetics", _REASON)
  grid, values = models.energetics(elc.grid, elc.values, ion.grid, ion.values,
      field.grid, field.values, gas_gamma=gas_gamma, num_moms=num_moms)
  return field._result(grid, values, inplace=inplace, tag=tag, label=label)
