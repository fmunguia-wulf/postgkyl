"""Energy-balance decomposition and current accumulation.

``energetics`` separates a two-species (electron + ion) fluid/field system
into its constituent energy components; ``accumulate_current`` scales a
single species' moment data by its charge (or charge-to-mass ratio) so that
several species can be summed into a total current.
"""

from __future__ import annotations

import numpy as np

from ..numerics import mag_sq
from .five_moment import get_ke, get_p


def energetics(elc_grid: list[np.ndarray], elc_values: np.ndarray,
    ion_grid: list[np.ndarray], ion_values: np.ndarray,
    field_grid: list[np.ndarray], field_values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, num_moms: int | None = None,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Separate a two-species plasma's energy into its constituent parts.

  Args:
    elc_grid: Electron moment grid.
    elc_values: Electron fluid moment array.
    ion_grid: Ion moment grid.
    ion_values: Ion fluid moment array.
    field_grid: EM field grid.
    field_values: EM field array laid out ``[Ex, Ey, Ez, Bx, By, Bz]``.
    gas_gamma: Adiabatic index, forwarded to the pressure/kinetic-energy
      calculation for both species.
    num_moms: Number of moments (5 or 10) for both species; inferred from
      the component count when ``None``.

  Returns:
    ``(grid, values)`` with a 7-component field:
    ``(electron thermal, electron kinetic, ion thermal, ion kinetic,
    electric, magnetic, total)``.
  """
  out = np.zeros(field_values.shape[:-1] + (7,))

  _, pre = get_p(elc_grid, elc_values, gas_gamma=gas_gamma, num_moms=num_moms)
  _, kee = get_ke(elc_grid, elc_values, gas_gamma=gas_gamma, num_moms=num_moms)
  _, pri = get_p(ion_grid, ion_values, gas_gamma=gas_gamma, num_moms=num_moms)
  _, kei = get_ke(ion_grid, ion_values, gas_gamma=gas_gamma, num_moms=num_moms)
  _, esq = mag_sq(field_grid, field_values, coords="0:3")
  _, bsq = mag_sq(field_grid, field_values, coords="3:6")

  out[..., 0] = np.squeeze(pre)
  out[..., 1] = np.squeeze(kee)
  out[..., 2] = np.squeeze(pri)
  out[..., 3] = np.squeeze(kei)
  out[..., 4] = np.squeeze(esq / 2.0)
  out[..., 5] = np.squeeze(bsq / 2.0)
  out[..., 6] = np.squeeze(pre + kee + pri + kei + esq / 2.0 + bsq / 2.0)

  return list(field_grid), out


def accumulate_current(grid: list[np.ndarray], values: np.ndarray, *,
    qbym: bool = False, charge: float | None = None, mass: float | None = None,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Scale a species' moment data into its contribution to the current.

  Args:
    grid: Species moment grid.
    values: Species moment array.
    qbym: If ``True``, scale by the charge-to-mass ratio ``charge / mass``
      (appropriate for fluid moment data, which already carries a mass
      factor in the density); otherwise scale by ``-1.0``.
    charge: Particle charge, required when ``qbym`` is ``True``.
    mass: Particle mass, required (and must be nonzero) when ``qbym`` is
      ``True``.

  Returns:
    ``(grid, values)`` holding the current contribution.
  """
  if qbym and mass and charge is not None:
    factor = charge / mass
  else:
    factor = -1.0

  return list(grid), factor * values
