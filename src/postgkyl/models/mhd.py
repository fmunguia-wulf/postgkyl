"""MHD primitive variables — B field, pressure, temperature, sound speed,
Mach number.

MHD moment data is laid out ``[rho, mx, my, mz, E, Bx, By, Bz]``: components
0:4 are shared with the 5-moment layout (density and momentum), so density
and velocity come from :mod:`postgkyl.models.five_moment`.
"""

from __future__ import annotations

import numpy as np

from .five_moment import get_density, get_vx, get_vy, get_vz


def get_mhd_Bx(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the x magnetic-field component (component 5 of MHD data)."""
  return list(grid), values[..., 5, np.newaxis]


def get_mhd_By(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the y magnetic-field component (component 6 of MHD data)."""
  return list(grid), values[..., 6, np.newaxis]


def get_mhd_Bz(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the z magnetic-field component (component 7 of MHD data)."""
  return list(grid), values[..., 7, np.newaxis]


def get_mhd_Bi(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the magnetic-field vector ``(Bx, By, Bz)`` (components 5:8)."""
  return list(grid), values[..., 5:8]


def get_mhd_mag_p(grid: list[np.ndarray], values: np.ndarray, *,
    mu_0: float = 1.0) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the magnetic pressure
  ``p_B = 0.5 * (Bx**2 + By**2 + Bz**2) / mu_0``."""
  _, Bx = get_mhd_Bx(grid, values)
  _, By = get_mhd_By(grid, values)
  _, Bz = get_mhd_Bz(grid, values)
  return list(grid), 0.5 * (Bx**2 + By**2 + Bz**2) / mu_0


def get_mhd_p(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the thermal (gas) pressure.

  ``p = (gas_gamma - 1) * (E - 0.5*rho*|v|**2 - p_B)``.
  """
  _, rho = get_density(grid, values)
  _, vx = get_vx(grid, values)
  _, vy = get_vy(grid, values)
  _, vz = get_vz(grid, values)
  _, mag_p = get_mhd_mag_p(grid, values, mu_0=mu_0)

  out_values = (gas_gamma - 1) * (
      values[..., 4, np.newaxis] - 0.5 * rho * (vx**2 + vy**2 + vz**2) - mag_p)
  return list(grid), out_values


def get_mhd_temp(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the temperature ``T = p / rho``."""
  _, rho = get_density(grid, values)
  _, pr = get_mhd_p(grid, values, gas_gamma=gas_gamma, mu_0=mu_0)
  return list(grid), pr / rho


def get_mhd_sound(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the sound speed ``c_s = sqrt(gas_gamma * p / rho)``."""
  _, rho = get_density(grid, values)
  _, pr = get_mhd_p(grid, values, gas_gamma=gas_gamma, mu_0=mu_0)
  return list(grid), np.sqrt(gas_gamma * pr / rho)


def get_mhd_mach(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the sonic Mach number ``M = |v| / c_s``."""
  _, vx = get_vx(grid, values)
  _, vy = get_vy(grid, values)
  _, vz = get_vz(grid, values)
  _, cs = get_mhd_sound(grid, values, gas_gamma=gas_gamma, mu_0=mu_0)
  return list(grid), np.sqrt(vx**2 + vy**2 + vz**2) / cs
