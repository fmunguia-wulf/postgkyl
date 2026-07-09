"""Plasma parameters: field magnitude, thermal/Alfven velocity, cyclotron and
plasma frequency, inertial length, Debye length, gyroradius, plasma beta.

The old ``postgkeyll.tools.params`` functions read ``mass``/``charge``/
``mu_0``/``epsilon_0`` from a ``GData.ctx`` dict, falling back to a keyword
argument when the context held nothing. Resolving that context is an
``ops``-layer (layer 08) concern — these are pure functions, so the physical
scalars are plain keyword-only arguments with no ctx and no fallback chain.
A consequence of dropping the GData/ctx duality is that a few old parameters
were never anything but ctx lookups (unused otherwise) and are dropped here
because keeping them would misstate what the function actually needs
(Doctrine IV): ``get_omegaC`` no longer takes ``species`` (only ``field``
values were ever used), ``get_omegaP``/``get_d``/``get_lambdaD`` no longer
take ``field`` (only ``species`` values were ever used), and ``get_rho``
drops the never-referenced ``epsilon_0`` parameter.
"""

from __future__ import annotations

import numpy as np

from ..numerics import mag_sq
from .five_moment import get_density, get_temp
from .mhd import get_mhd_temp


def get_magB(field_grid: list[np.ndarray],
    field_values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the magnitude of the magnetic field ``|B|``.

  Args:
    field_grid: EM field grid.
    field_values: EM field array laid out ``[Ex, Ey, Ez, Bx, By, Bz, ...]``;
      components 3:6 are used.

  Returns:
    ``(grid, values)`` holding ``|B| = sqrt(Bx**2 + By**2 + Bz**2)``.
  """
  b_values = field_values[..., 3:6]
  _, mag_B_sq = mag_sq(field_grid, b_values)
  return list(field_grid), np.sqrt(mag_B_sq)


def get_vt(species_grid: list[np.ndarray], species_values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3.0, num_moms: int | None = None,
    mass: float = 1.0, mu_0: float = 1.0, sqrt2: bool = True,
    mhd: bool = False) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the thermal velocity ``v_th = sqrt(2 T/m)`` (or ``sqrt(T/m)``
  when ``sqrt2`` is ``False``) of a species.

  Args:
    species_grid: Species moment grid.
    species_values: Species moment array (5- or 10-moment, or MHD when
      ``mhd=True``).
    gas_gamma: Adiabatic index used when computing the temperature/pressure.
    num_moms: Number of moments (5 or 10); inferred when ``None``.
    mass: Particle mass.
    mu_0: Vacuum permeability, forwarded to the MHD temperature when
      ``mhd=True``.
    sqrt2: If ``True`` (default), scale the result by ``sqrt(2)``.
    mhd: If ``True``, compute the temperature from MHD moments; otherwise
      use the fluid moments.

  Returns:
    ``(grid, values)`` holding the thermal velocity field.
  """
  if mhd:
    out_grid, temp = get_mhd_temp(species_grid, species_values,
        gas_gamma=gas_gamma, mu_0=mu_0)
  else:
    out_grid, temp = get_temp(species_grid, species_values,
        gas_gamma=gas_gamma, num_moms=num_moms)

  out_values = np.sqrt(temp / mass)
  if sqrt2:
    out_values = out_values * np.sqrt(2.0)

  return out_grid, out_values


def get_vA(species_grid: list[np.ndarray], species_values: np.ndarray,
    field_grid: list[np.ndarray], field_values: np.ndarray, *,
    mu_0: float = 1.0) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the Alfven velocity ``v_A = |B| / sqrt(mu_0 * rho)``.

  Fluid moment data already includes the mass factor in the density.
  """
  _, magB = get_magB(field_grid, field_values)
  out_grid, rho = get_density(species_grid, species_values)
  return out_grid, magB / np.sqrt(mu_0 * rho)


def get_omegaC(field_grid: list[np.ndarray], field_values: np.ndarray, *,
    mass: float = 1.0, charge: float = 1.0,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the cyclotron (gyro) frequency ``omega_c = |q| * |B| / m``."""
  out_grid, magB = get_magB(field_grid, field_values)
  return out_grid, abs(charge) * magB / mass


def get_omegaP(species_grid: list[np.ndarray], species_values: np.ndarray, *,
    mass: float = 1.0, charge: float = 1.0, epsilon_0: float = 1.0,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the plasma frequency
  ``omega_p = sqrt(q**2 * n / (m**2 * epsilon_0))``.

  Fluid moment data already includes the mass factor in the density.
  """
  out_grid, rho = get_density(species_grid, species_values)
  qbym2 = charge**2 / mass**2
  return out_grid, np.sqrt(qbym2 * rho / epsilon_0)


def get_d(species_grid: list[np.ndarray], species_values: np.ndarray, *,
    mass: float = 1.0, charge: float = 1.0, epsilon_0: float = 1.0,
    mu_0: float = 1.0) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the inertial (skin-depth) length ``d = c / omega_p``, with
  ``c = 1 / sqrt(epsilon_0 * mu_0)``."""
  out_grid, omegaP = get_omegaP(species_grid, species_values, mass=mass,
      charge=charge, epsilon_0=epsilon_0)
  light_speed = 1.0 / np.sqrt(epsilon_0 * mu_0)
  return out_grid, light_speed / omegaP


def get_lambdaD(species_grid: list[np.ndarray], species_values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3.0, num_moms: int | None = None,
    mass: float = 1.0, charge: float = 1.0, epsilon_0: float = 1.0,
    mu_0: float = 1.0, sqrt2: bool = True,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the Debye length ``lambda_D = v_th / omega_p``.

  When ``sqrt2`` is ``True`` the extra ``sqrt(2)`` factor carried by
  ``v_th`` is divided back out, so the conventional Debye length is
  returned.
  """
  _, omegaP = get_omegaP(species_grid, species_values, mass=mass,
      charge=charge, epsilon_0=epsilon_0)
  out_grid, vt = get_vt(species_grid, species_values, gas_gamma=gas_gamma,
      num_moms=num_moms, mass=mass, mu_0=mu_0, sqrt2=sqrt2)
  out_values = vt / omegaP
  if sqrt2:
    out_values = out_values / np.sqrt(2.0)

  return out_grid, out_values


def get_rho(species_grid: list[np.ndarray], species_values: np.ndarray,
    field_grid: list[np.ndarray], field_values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3.0, num_moms: int | None = None,
    mass: float = 1.0, charge: float = 1.0, mu_0: float = 1.0,
    sqrt2: bool = True) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the gyroradius (Larmor radius) ``rho = v_th / omega_c``.

  When ``sqrt2`` is ``False`` the result is multiplied by ``sqrt(2)`` so the
  gyroradius stays consistent with a ``sqrt(2)``-scaled thermal velocity.
  """
  _, omegaC = get_omegaC(field_grid, field_values, mass=mass, charge=charge)
  out_grid, vt = get_vt(species_grid, species_values, gas_gamma=gas_gamma,
      num_moms=num_moms, mass=mass, mu_0=mu_0, sqrt2=sqrt2)

  out_values = vt / omegaC
  if not sqrt2:
    out_values = out_values * np.sqrt(2.0)

  return out_grid, out_values


def get_beta(species_grid: list[np.ndarray], species_values: np.ndarray,
    field_grid: list[np.ndarray], field_values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3.0, num_moms: int | None = None,
    mass: float = 1.0, mu_0: float = 1.0, sqrt2: bool = True,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the plasma beta ``v_th**2 / v_A**2``.

  When ``sqrt2`` is ``False`` the result is multiplied by ``2`` to account
  for the missing ``sqrt(2)`` factor in the thermal velocity.
  """
  _, v_A = get_vA(species_grid, species_values, field_grid, field_values,
      mu_0=mu_0)
  out_grid, vt = get_vt(species_grid, species_values, gas_gamma=gas_gamma,
      num_moms=num_moms, mass=mass, mu_0=mu_0, sqrt2=sqrt2)
  out_values = vt**2 / v_A**2
  if not sqrt2:
    out_values = out_values * 2.0

  return out_grid, out_values
