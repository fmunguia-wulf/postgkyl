from __future__ import annotations

import numpy as np
from typing import Tuple, TYPE_CHECKING

from postgkyl.utils import input_parser
if TYPE_CHECKING:
  from postgkeyll import GData
# end


def get_density(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the (mass) density from fluid moment data.

  The density is component 0 of the moment array.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the density field (with a trailing singleton component axis).
  """
  grid, in_values = input_parser(in_mom)
  out_values = in_values[..., 0, np.newaxis]

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_vx(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the x velocity component from fluid moment data.

  The velocity is the x momentum (component 1) divided by the density.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the x velocity field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  out_values = in_values[..., 1, np.newaxis] / rho

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_vy(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the y velocity component from fluid moment data.

  The velocity is the y momentum (component 2) divided by the density.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the y velocity field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  out_values = in_values[..., 2, np.newaxis] / rho

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_vz(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the z velocity component from fluid moment data.

  The velocity is the z momentum (component 3) divided by the density.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the z velocity field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  out_values = in_values[..., 3, np.newaxis] / rho

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_vi(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the velocity vector (vx, vy, vz) from fluid moment data.

  Each component is the corresponding momentum (components 1:4) divided by the
  density.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the three-component velocity field ``(vx, vy, vz)``.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  out_values = in_values[..., 1:4] / rho

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_pxx(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the xx component of the pressure tensor from 10-moment data.

  Computed by subtracting the bulk-flow (ram) contribution from the second
  moment: ``P_xx = M_xx - rho * vx * vx`` (component 4 of the moment array).

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``P_xx`` field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  _, vx = get_vx(in_mom)
  out_values = in_values[..., 4, np.newaxis] - rho*vx*vx

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_pxy(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the xy component of the pressure tensor from 10-moment data.

  Computed by subtracting the bulk-flow contribution from the second moment:
  ``P_xy = M_xy - rho * vx * vy`` (component 5 of the moment array).

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``P_xy`` field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  _, vx = get_vx(in_mom)
  _, vy = get_vy(in_mom)
  out_values = in_values[..., 5, np.newaxis] - rho*vx*vy

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_pxz(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the xz component of the pressure tensor from 10-moment data.

  Computed by subtracting the bulk-flow contribution from the second moment:
  ``P_xz = M_xz - rho * vx * vz`` (component 6 of the moment array).

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``P_xz`` field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  _, vx = get_vx(in_mom)
  _, vz = get_vz(in_mom)
  out_values = in_values[..., 6, np.newaxis] - rho*vx*vz

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_pyy(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the yy component of the pressure tensor from 10-moment data.

  Computed by subtracting the bulk-flow contribution from the second moment:
  ``P_yy = M_yy - rho * vy * vy`` (component 7 of the moment array).

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``P_yy`` field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  _, vy = get_vy(in_mom)
  out_values = in_values[..., 7, np.newaxis] - rho*vy*vy

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_pyz(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the yz component of the pressure tensor from 10-moment data.

  Computed by subtracting the bulk-flow contribution from the second moment:
  ``P_yz = M_yz - rho * vy * vz`` (component 8 of the moment array).

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``P_yz`` field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  _, vy = get_vy(in_mom)
  _, vz = get_vz(in_mom)
  out_values = in_values[..., 8, np.newaxis] - rho*vy*vz

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_pzz(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the zz component of the pressure tensor from 10-moment data.

  Computed by subtracting the bulk-flow contribution from the second moment:
  ``P_zz = M_zz - rho * vz * vz`` (component 9 of the moment array).

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``P_zz`` field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  _, vz = get_vz(in_mom)
  out_values = in_values[..., 9, np.newaxis] - rho*vz*vz

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_pij(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the full symmetric pressure tensor from 10-moment data.

  Packs the six independent components in the order
  ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``, each computed by subtracting the
  bulk-flow contribution from the corresponding second moment.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and a
    six-component array ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``.
  """
  grid, in_values = input_parser(in_mom)
  out_values = np.zeros(in_values[..., 4:10].shape)

  _, pxx = get_pxx(in_mom)
  _, pxy = get_pxy(in_mom)
  _, pxz = get_pxz(in_mom)
  _, pyy = get_pyy(in_mom)
  _, pyz = get_pyz(in_mom)
  _, pzz = get_pzz(in_mom)

  out_values[..., 0] = np.squeeze(pxx)
  out_values[..., 1] = np.squeeze(pxy)
  out_values[..., 2] = np.squeeze(pxz)
  out_values[..., 3] = np.squeeze(pyy)
  out_values[..., 4] = np.squeeze(pyz)
  out_values[..., 5] = np.squeeze(pzz)

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_p(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    num_moms: int | None = None,
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the scalar pressure from fluid moment data.

  For 5-moment data the pressure is obtained from the total energy minus the
  bulk kinetic energy, scaled by ``gas_gamma - 1``. For 10-moment data it is the
  trace of the pressure tensor over three: ``(P_xx + P_yy + P_zz) / 3``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index, used only for 5-moment data. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10). If ``None`` it is inferred from the number
      of components; a ``ValueError`` is raised if it cannot be determined.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the scalar pressure field.
  """
  grid, in_values = input_parser(in_mom)
  num_comps = in_values.shape[-1]
  if num_moms is None:
    if num_comps == 5:
      num_moms = 5
    elif num_comps == 10:
      num_moms = 10
    else:
      raise ValueError(f"Number of components appears to be {num_comps:d}; it needs to be specified using 'num_moms' (5 or 10)")
    # end
  # end

  if num_moms == 5:
    _, rho = get_density(in_mom)
    _, vx = get_vx(in_mom)
    _, vy = get_vy(in_mom)
    _, vz = get_vz(in_mom)
    out_values = (gas_gamma - 1) * (
        in_values[..., 4, np.newaxis] - 0.5*rho*(vx**2 + vy**2 + vz**2)
    )
  else: # num_moms == 10:
    _, pxx = get_pxx(in_mom)
    _, pyy = get_pyy(in_mom)
    _, pzz = get_pzz(in_mom)
    out_values = (pxx + pyy + pzz) / 3.0
  # end

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_ke(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    num_moms: int | None = None,
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the kinetic (bulk-flow) energy density from fluid moment data.

  For 5-moment data the kinetic energy is the total energy minus the thermal
  energy ``p / (gas_gamma - 1)``. For 10-moment data it is computed directly as
  ``0.5 * rho * (vx**2 + vy**2 + vz**2)``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index, used only for 5-moment data. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10). If ``None`` it is inferred from the number
      of components; a ``ValueError`` is raised if it cannot be determined.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the kinetic energy density field.
  """
  grid, in_values = input_parser(in_mom)
  num_comps = in_values.shape[-1]
  if num_moms is None:
    if num_comps == 5:
      num_moms = 5
    elif num_comps == 10:
      num_moms = 10
    else:
      raise ValueError(f"Number of components appears to be {num_comps:d}; (5 or 10)")
    # end
  # end

  if num_moms == 5:
    _, pr = get_p(in_mom, gas_gamma=gas_gamma, num_moms=num_moms)
    out_values = in_values[..., 4, np.newaxis] - pr / (gas_gamma - 1)
  else: #  num_moms == 10:
    _, rho = get_density(in_mom)
    _, vx = get_vx(in_mom)
    _, vy = get_vy(in_mom)
    _, vz = get_vz(in_mom)
    out_values = 0.5*rho*(vx**2 + vy**2 + vz**2)
  # end

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_temp(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    num_moms: int | None = None,
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the temperature from fluid moment data.

  The temperature is the scalar pressure divided by the density,
  ``T = p / rho``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index used when computing the pressure. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10). If ``None`` it is inferred from the number
      of components.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the temperature field.
  """
  grid, rho = get_density(in_mom)
  _, pr = get_p(in_mom, gas_gamma=gas_gamma, num_moms=num_moms)
  out_values = pr/rho

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_sound(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    num_moms: int | None = None,
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the sound speed from fluid moment data.

  The sound speed is ``c_s = sqrt(gas_gamma * p / rho)``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10). If ``None`` it is inferred from the number
      of components.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the sound speed field.
  """
  grid, rho = get_density(in_mom)
  _, pr = get_p(in_mom, gas_gamma=gas_gamma, num_moms=num_moms)
  out_values = np.sqrt(gas_gamma*pr / rho)

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mach(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    num_moms: int | None = None,
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the sonic Mach number from fluid moment data.

  The Mach number is the bulk flow speed divided by the sound speed,
  ``M = |v| / c_s``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input fluid moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index used when computing the sound speed. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10). If ``None`` it is inferred from the number
      of components.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the Mach number field.
  """
  grid, vx = get_vx(in_mom)
  _, vy = get_vy(in_mom)
  _, vz = get_vz(in_mom)
  _, cs = get_sound(in_mom, gas_gamma=gas_gamma, num_moms=num_moms)
  out_values = np.sqrt(vx**2 + vy**2 + vz**2) / cs

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_Bx(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the x magnetic-field component from MHD moment data.

  The x magnetic field is stored in component 5 of the MHD state vector
  ``[rho, rho*vx, rho*vy, rho*vz, E, Bx, By, Bz]``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``Bx`` field.
  """
  grid, in_values = input_parser(in_mom)
  out_values = in_values[..., 5, np.newaxis]

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_By(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the y magnetic-field component from MHD moment data.

  The y magnetic field is stored in component 6 of the MHD state vector.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``By`` field.
  """
  grid, in_values = input_parser(in_mom)
  out_values = in_values[..., 6, np.newaxis]

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_Bz(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the z magnetic-field component from MHD moment data.

  The z magnetic field is stored in component 7 of the MHD state vector.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the ``Bz`` field.
  """
  grid, in_values = input_parser(in_mom)
  out_values = in_values[..., 7, np.newaxis]

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_Bi(in_mom: GData | Tuple[list, np.ndarray],
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Extract the magnetic-field vector (Bx, By, Bz) from MHD moment data.

  The three magnetic-field components are stored in components 5:8 of the MHD
  state vector.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the three-component magnetic field ``(Bx, By, Bz)``.
  """
  grid, in_values = input_parser(in_mom)
  out_values = in_values[..., 5:8]

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_mag_p(in_mom: GData | Tuple[list, np.ndarray], mu_0: float = 1.0,
    out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the magnetic pressure from MHD moment data.

  The magnetic pressure is ``p_B = 0.5 * (Bx**2 + By**2 + Bz**2) / mu_0``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    mu_0: float
      Vacuum permeability. Defaults to ``1.0``.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the magnetic pressure field.
  """
  grid, Bx = get_mhd_Bx(in_mom)
  _, By = get_mhd_By(in_mom)
  _, Bz = get_mhd_Bz(in_mom)
  out_values = 0.5 * (Bx**2 + By**2 + Bz**2) / mu_0

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_p(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    mu_0: float = 1.0, out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the thermal (gas) pressure from MHD moment data.

  The thermal pressure is obtained from the total energy with the bulk kinetic
  energy and magnetic pressure subtracted, scaled by ``gas_gamma - 1``:
  ``p = (gas_gamma - 1) * (E - 0.5*rho*|v|**2 - p_B)``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index. Defaults to ``5/3``.
    mu_0: float
      Vacuum permeability, used for the magnetic pressure. Defaults to ``1.0``.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the thermal pressure field.
  """
  grid, in_values = input_parser(in_mom)
  _, rho = get_density(in_mom)
  _, vx = get_vx(in_mom)
  _, vy = get_vy(in_mom)
  _, vz = get_vz(in_mom)
  _, mag_p = get_mhd_mag_p(in_mom, mu_0=mu_0)

  out_values = (gas_gamma - 1)*(in_values[..., 4, np.newaxis] - 0.5*rho*(vx**2 + vy**2 + vz**2) - mag_p)

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_temp(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    mu_0: float = 1.0, out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the temperature from MHD moment data.

  The temperature is the thermal pressure divided by the density,
  ``T = p / rho``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index used when computing the thermal pressure. Defaults to
      ``5/3``.
    mu_0: float
      Vacuum permeability, used for the magnetic pressure. Defaults to ``1.0``.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the temperature field.
  """
  grid, rho = get_density(in_mom)
  _, pr = get_mhd_p(in_mom, gas_gamma=gas_gamma, mu_0=mu_0)
  out_values = pr / rho

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_sound(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    mu_0: float = 1.0, out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the sound speed from MHD moment data.

  The sound speed is ``c_s = sqrt(gas_gamma * p / rho)`` using the thermal
  pressure.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index. Defaults to ``5/3``.
    mu_0: float
      Vacuum permeability, used for the magnetic pressure. Defaults to ``1.0``.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the sound speed field.
  """
  grid, rho = get_density(in_mom)
  _, pr = get_mhd_p(in_mom, gas_gamma=gas_gamma, mu_0=mu_0)

  out_values = np.sqrt(gas_gamma*pr/rho)

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values


def get_mhd_mach(in_mom: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3,
    mu_0: float = 1.0, out_mom: GData | None = None) -> Tuple[list, np.ndarray]:
  """Compute the sonic Mach number from MHD moment data.

  The Mach number is the bulk flow speed divided by the (gas) sound speed,
  ``M = |v| / c_s``.

  Args:
    in_mom: GData | Tuple[list, np.ndarray]
      Input MHD moment data, either as a ``GData`` object or a
      ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index used when computing the sound speed. Defaults to ``5/3``.
    mu_0: float
      Vacuum permeability, used for the magnetic pressure. Defaults to ``1.0``.
    out_mom: GData | None
      Optional output ``GData`` to push the result into via ``out_mom.push``.
      Defaults to ``None``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the Mach number field.
  """
  grid, vx = get_vx(in_mom)
  _, vy = get_vy(in_mom)
  _, vz = get_vz(in_mom)
  _, cs = get_mhd_sound(in_mom, gas_gamma=gas_gamma, mu_0=mu_0)
  out_values = np.sqrt(vx**2 + vy**2 + vz**2) / cs

  if out_mom:
    out_mom.push(grid, out_values)
  # end
  return grid, out_values
