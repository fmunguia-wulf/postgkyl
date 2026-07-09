"""10-moment pressure tensor and field-aligned pressure diagnostics.

10-moment fluid data is laid out ``[rho, mx, my, mz, Pxx, Pxy, Pxz, Pyy, Pyz,
Pzz]``; the pressure tensor components below subtract the bulk-flow (ram)
contribution from the raw second moments. ``get_p_par``/``get_p_perp``/
``get_agyro`` then take an already-built 6-component pressure tensor
(``P_xx, P_xy, P_xz, P_yy, P_yz, P_zz``) and a 3-component magnetic field.
"""

from __future__ import annotations

import numpy as np

from ..numerics import mag_sq
from .five_moment import get_density, get_vx, get_vy, get_vz


def get_pxx(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """``P_xx = M_xx - rho * vx * vx`` (component 4 of 10-moment data)."""
  _, rho = get_density(grid, values)
  _, vx = get_vx(grid, values)
  return list(grid), values[..., 4, np.newaxis] - rho * vx * vx


def get_pxy(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """``P_xy = M_xy - rho * vx * vy`` (component 5 of 10-moment data)."""
  _, rho = get_density(grid, values)
  _, vx = get_vx(grid, values)
  _, vy = get_vy(grid, values)
  return list(grid), values[..., 5, np.newaxis] - rho * vx * vy


def get_pxz(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """``P_xz = M_xz - rho * vx * vz`` (component 6 of 10-moment data)."""
  _, rho = get_density(grid, values)
  _, vx = get_vx(grid, values)
  _, vz = get_vz(grid, values)
  return list(grid), values[..., 6, np.newaxis] - rho * vx * vz


def get_pyy(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """``P_yy = M_yy - rho * vy * vy`` (component 7 of 10-moment data)."""
  _, rho = get_density(grid, values)
  _, vy = get_vy(grid, values)
  return list(grid), values[..., 7, np.newaxis] - rho * vy * vy


def get_pyz(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """``P_yz = M_yz - rho * vy * vz`` (component 8 of 10-moment data)."""
  _, rho = get_density(grid, values)
  _, vy = get_vy(grid, values)
  _, vz = get_vz(grid, values)
  return list(grid), values[..., 8, np.newaxis] - rho * vy * vz


def get_pzz(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """``P_zz = M_zz - rho * vz * vz`` (component 9 of 10-moment data)."""
  _, rho = get_density(grid, values)
  _, vz = get_vz(grid, values)
  return list(grid), values[..., 9, np.newaxis] - rho * vz * vz


def get_pij(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Full symmetric pressure tensor, packed
  ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``."""
  out_values = np.zeros(values[..., 4:10].shape)
  _, pxx = get_pxx(grid, values)
  _, pxy = get_pxy(grid, values)
  _, pxz = get_pxz(grid, values)
  _, pyy = get_pyy(grid, values)
  _, pyz = get_pyz(grid, values)
  _, pzz = get_pzz(grid, values)

  out_values[..., 0] = np.squeeze(pxx)
  out_values[..., 1] = np.squeeze(pxy)
  out_values[..., 2] = np.squeeze(pxz)
  out_values[..., 3] = np.squeeze(pyy)
  out_values[..., 4] = np.squeeze(pyz)
  out_values[..., 5] = np.squeeze(pzz)

  return list(grid), out_values


def get_p_par(p_grid: list[np.ndarray], p_values: np.ndarray,
    b_grid: list[np.ndarray], b_values: np.ndarray,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the pressure parallel to the magnetic field.

  Projects the pressure tensor onto the magnetic-field direction:
  ``p_par = (b . P . b) / |B|**2``.

  Args:
    p_grid: Pressure-tensor grid.
    p_values: 6-component pressure tensor
      ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``.
    b_grid: Magnetic-field grid.
    b_values: 3-component magnetic field ``(Bx, By, Bz)``.

  Returns:
    ``(grid, values)`` holding the parallel pressure field.
  """
  p_xx = p_values[..., 0, np.newaxis]
  p_xy = p_values[..., 1, np.newaxis]
  p_xz = p_values[..., 2, np.newaxis]
  p_yy = p_values[..., 3, np.newaxis]
  p_yz = p_values[..., 4, np.newaxis]
  p_zz = p_values[..., 5, np.newaxis]

  b_x = b_values[..., 0, np.newaxis]
  b_y = b_values[..., 1, np.newaxis]
  b_z = b_values[..., 2, np.newaxis]

  grid, mag_b_sq = mag_sq(b_grid, b_values)

  out = (b_x * b_x * p_xx + b_y * b_y * p_yy + b_z * b_z * p_zz
      + 2.0 * (b_x * b_y * p_xy + b_x * b_z * p_xz + b_y * b_z * p_yz)
      ) / mag_b_sq
  return grid, out


def get_gkyl_10m_p_par(species_grid: list[np.ndarray], species_values: np.ndarray,
    field_grid: list[np.ndarray], field_values: np.ndarray,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the parallel pressure directly from raw 10-moment species and
  EM field data (whose components 3:6 are ``(Bx, By, Bz)``)."""
  p_grid, p_values = get_pij(species_grid, species_values)
  b_values = field_values[..., 3:6]
  return get_p_par(p_grid, p_values, field_grid, b_values)


def get_p_perp(p_grid: list[np.ndarray], p_values: np.ndarray,
    b_grid: list[np.ndarray], b_values: np.ndarray,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the pressure perpendicular to the magnetic field.

  Uses the trace of the pressure tensor and the parallel pressure:
  ``p_perp = (P_xx + P_yy + P_zz - p_par) / 2``.
  """
  p_xx = p_values[..., 0, np.newaxis]
  p_yy = p_values[..., 3, np.newaxis]
  p_zz = p_values[..., 5, np.newaxis]

  grid, p_par = get_p_par(p_grid, p_values, b_grid, b_values)

  return grid, (p_xx + p_yy + p_zz - p_par) / 2.0


def get_gkyl_10m_p_perp(species_grid: list[np.ndarray], species_values: np.ndarray,
    field_grid: list[np.ndarray], field_values: np.ndarray,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the perpendicular pressure directly from raw 10-moment species
  and EM field data (whose components 3:6 are ``(Bx, By, Bz)``)."""
  p_grid, p_values = get_pij(species_grid, species_values)
  b_values = field_values[..., 3:6]
  return get_p_perp(p_grid, p_values, field_grid, b_values)


def get_agyro(p_grid: list[np.ndarray], p_values: np.ndarray,
    b_grid: list[np.ndarray], b_values: np.ndarray, *,
    measure: str = "swisdak") -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the agyrotropy of the pressure tensor.

  The ``'swisdak'`` measure uses the tensor invariants and parallel pressure
  as in Appendix A of Swisdak (2015). The ``'frobenius'`` measure is the
  Frobenius norm of the non-gyrotropic part of the pressure tensor,
  normalized by the gyrotropic part.

  Args:
    p_grid: Pressure-tensor grid.
    p_values: 6-component pressure tensor
      ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``.
    b_grid: Magnetic-field grid.
    b_values: 3-component magnetic field ``(Bx, By, Bz)``.
    measure: ``'swisdak'`` (default) or ``'frobenius'`` (case-insensitive).

  Returns:
    ``(grid, values)`` holding the agyrotropy field.

  Raises:
    ValueError: If ``measure`` is neither ``'swisdak'`` nor ``'frobenius'``.
  """
  p_xx = p_values[..., 0, np.newaxis]
  p_xy = p_values[..., 1, np.newaxis]
  p_xz = p_values[..., 2, np.newaxis]
  p_yy = p_values[..., 3, np.newaxis]
  p_yz = p_values[..., 4, np.newaxis]
  p_zz = p_values[..., 5, np.newaxis]

  b_x = b_values[..., 0, np.newaxis]
  b_y = b_values[..., 1, np.newaxis]
  b_z = b_values[..., 2, np.newaxis]

  grid, mag_b_sq = mag_sq(b_grid, b_values)
  _, p_par = get_p_par(p_grid, p_values, b_grid, b_values)
  _, p_perp = get_p_perp(p_grid, p_values, b_grid, b_values)

  measure_lower = measure.lower()
  if measure_lower == "swisdak":
    I1 = p_xx + p_yy + p_zz
    I2 = (p_xx * p_yy + p_xx * p_zz + p_yy * p_zz
        - (p_xy * p_xy + p_xz * p_xz + p_yz * p_yz))
    # Tensor algebra of Appendix A of Swisdak 2015.
    out = np.sqrt(1 - 4 * I2 / ((I1 - p_par) * (I1 + 3 * p_par)))
  elif measure_lower == "frobenius":
    p_ixx = p_xx - (p_par * b_x * b_x / mag_b_sq
        + p_perp * (1 - b_x * b_x / mag_b_sq))
    p_ixy = p_xy - (p_par * b_x * b_y / mag_b_sq
        + p_perp * (0 - b_x * b_y / mag_b_sq))
    p_ixz = p_xz - (p_par * b_x * b_z / mag_b_sq
        + p_perp * (0 - b_x * b_z / mag_b_sq))
    p_iyy = p_yy - (p_par * b_y * b_y / mag_b_sq
        + p_perp * (1 - b_y * b_y / mag_b_sq))
    p_iyz = p_yz - (p_par * b_y * b_z / mag_b_sq
        + p_perp * (0 - b_y * b_z / mag_b_sq))
    p_izz = p_zz - (p_par * b_z * b_z / mag_b_sq
        + p_perp * (1 - b_z * b_z / mag_b_sq))
    out = (np.sqrt(p_ixx**2 + 2 * p_ixy**2 + 2 * p_ixz**2 + p_iyy**2
        + 2 * p_iyz**2 + p_izz**2)
        / np.sqrt(2 * p_perp**2 + 4 * p_par * p_perp))
  else:
    raise ValueError(
        f"Measure specified is {measure_lower:s}; it needs to be either "
        "'swisdak' or 'frobenius'")

  return grid, out


def get_gkyl_10m_agyro(species_grid: list[np.ndarray], species_values: np.ndarray,
    field_grid: list[np.ndarray], field_values: np.ndarray, *,
    measure: str = "swisdak") -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the agyrotropy directly from raw 10-moment species and EM field
  data (whose components 3:6 are ``(Bx, By, Bz)``)."""
  p_grid, p_values = get_pij(species_grid, species_values)
  b_values = field_values[..., 3:6]
  return get_agyro(p_grid, p_values, field_grid, b_values, measure=measure)
