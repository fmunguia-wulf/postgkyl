"""5-moment (Euler) primitive variables — density, velocity, pressure,
temperature, sound speed, Mach number.

Fluid moment data is laid out ``[rho, rho*vx, rho*vy, rho*vz, E, ...]``: the
first four components are shared with 10-moment/MHD data, and ``get_p``/
``get_ke``/``get_temp``/``get_sound``/``get_mach`` additionally accept
10-moment data (``num_moms=10``), inferring which layout applies from the
number of components when ``num_moms`` is not given.
"""

from __future__ import annotations

import numpy as np


def get_density(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the (mass) density from fluid moment data.

  The density is component 0 of the moment array.

  Args:
    grid: Nodal coordinate arrays, one per spatial dimension.
    values: Moment array whose last axis holds the conserved variables.

  Returns:
    ``(grid, values)`` with the density as a single trailing component.
  """
  return list(grid), values[..., 0, np.newaxis]


def get_vx(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the x velocity: x momentum (component 1) over density."""
  _, rho = get_density(grid, values)
  return list(grid), values[..., 1, np.newaxis] / rho


def get_vy(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the y velocity: y momentum (component 2) over density."""
  _, rho = get_density(grid, values)
  return list(grid), values[..., 2, np.newaxis] / rho


def get_vz(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the z velocity: z momentum (component 3) over density."""
  _, rho = get_density(grid, values)
  return list(grid), values[..., 3, np.newaxis] / rho


def get_vi(grid: list[np.ndarray],
    values: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
  """Extract the velocity vector ``(vx, vy, vz)``: momentum (1:4) over density."""
  _, rho = get_density(grid, values)
  return list(grid), values[..., 1:4] / rho


def _infer_num_moms(values: np.ndarray, num_moms: int | None) -> int:
  """Resolve the moment count, inferring it from the component count."""
  if num_moms is not None:
    return num_moms
  num_comps = values.shape[-1]
  if num_comps == 5:
    return 5
  if num_comps == 10:
    return 10
  raise ValueError(
      f"Number of components appears to be {num_comps:d}; it needs to be "
      "specified using 'num_moms' (5 or 10)")


def get_p(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, num_moms: int | None = None,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the scalar pressure from fluid moment data.

  For 5-moment data the pressure is the total energy minus the bulk kinetic
  energy, scaled by ``gas_gamma - 1``. For 10-moment data it is the trace of
  the pressure tensor over three: ``(P_xx + P_yy + P_zz) / 3``.

  Args:
    grid: Nodal coordinate arrays, one per spatial dimension.
    values: Moment array (5- or 10-moment).
    gas_gamma: Adiabatic index, used only for 5-moment data.
    num_moms: Number of moments (5 or 10); inferred from the component count
      when ``None``.

  Returns:
    ``(grid, values)`` holding the scalar pressure field.

  Raises:
    ValueError: If ``num_moms`` is ``None`` and cannot be inferred.
  """
  num_moms = _infer_num_moms(values, num_moms)

  if num_moms == 5:
    _, rho = get_density(grid, values)
    _, vx = get_vx(grid, values)
    _, vy = get_vy(grid, values)
    _, vz = get_vz(grid, values)
    out_values = (gas_gamma - 1) * (
        values[..., 4, np.newaxis] - 0.5 * rho * (vx**2 + vy**2 + vz**2))
  else:  # num_moms == 10
    # Trace of the pressure tensor, computed inline (rather than calling
    # models.ten_moment.get_pxx/get_pyy/get_pzz) to keep five_moment ->
    # ten_moment a one-way edge; ten_moment.get_pxx/pyy/pzz apply this same
    # M_ii - rho*v_i*v_i formula component-wise.
    _, rho = get_density(grid, values)
    _, vx = get_vx(grid, values)
    _, vy = get_vy(grid, values)
    _, vz = get_vz(grid, values)
    pxx = values[..., 4, np.newaxis] - rho * vx * vx
    pyy = values[..., 7, np.newaxis] - rho * vy * vy
    pzz = values[..., 9, np.newaxis] - rho * vz * vz
    out_values = (pxx + pyy + pzz) / 3.0

  return list(grid), out_values


def get_ke(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, num_moms: int | None = None,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the kinetic (bulk-flow) energy density from fluid moment data.

  For 5-moment data it is the total energy minus the thermal energy
  ``p / (gas_gamma - 1)``. For 10-moment data it is
  ``0.5 * rho * (vx**2 + vy**2 + vz**2)`` directly.

  Args:
    grid: Nodal coordinate arrays, one per spatial dimension.
    values: Moment array (5- or 10-moment).
    gas_gamma: Adiabatic index, used only for 5-moment data.
    num_moms: Number of moments (5 or 10); inferred from the component count
      when ``None``.

  Returns:
    ``(grid, values)`` holding the kinetic energy density field.
  """
  num_moms = _infer_num_moms(values, num_moms)

  if num_moms == 5:
    _, pr = get_p(grid, values, gas_gamma=gas_gamma, num_moms=num_moms)
    out_values = values[..., 4, np.newaxis] - pr / (gas_gamma - 1)
  else:  # num_moms == 10
    _, rho = get_density(grid, values)
    _, vx = get_vx(grid, values)
    _, vy = get_vy(grid, values)
    _, vz = get_vz(grid, values)
    out_values = 0.5 * rho * (vx**2 + vy**2 + vz**2)

  return list(grid), out_values


def get_temp(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, num_moms: int | None = None,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the temperature ``T = p / rho`` from fluid moment data."""
  _, rho = get_density(grid, values)
  _, pr = get_p(grid, values, gas_gamma=gas_gamma, num_moms=num_moms)
  return list(grid), pr / rho


def get_sound(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, num_moms: int | None = None,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the sound speed ``c_s = sqrt(gas_gamma * p / rho)``."""
  _, rho = get_density(grid, values)
  _, pr = get_p(grid, values, gas_gamma=gas_gamma, num_moms=num_moms)
  return list(grid), np.sqrt(gas_gamma * pr / rho)


def get_mach(grid: list[np.ndarray], values: np.ndarray, *,
    gas_gamma: float = 5.0 / 3, num_moms: int | None = None,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compute the sonic Mach number ``M = |v| / c_s``."""
  _, vx = get_vx(grid, values)
  _, vy = get_vy(grid, values)
  _, vz = get_vz(grid, values)
  _, cs = get_sound(grid, values, gas_gamma=gas_gamma, num_moms=num_moms)
  return list(grid), np.sqrt(vx**2 + vy**2 + vz**2) / cs
