"""Postgkyl module for plasma related parameters."""

from __future__ import annotations

from typing import Tuple, TYPE_CHECKING
import numpy as np

from postgkyl.tools.mag_sq import mag_sq
from postgkyl.tools.prim_vars import get_density, get_temp, get_mhd_temp
from postgkyl.utils import input_parser

if TYPE_CHECKING:
  from postgkeyll import GData
# end


def get_magB(field: GData | Tuple[list, np.ndarray]) -> Tuple[list, np.ndarray]:
  """Compute the magnitude of the magnetic field |B|.

  The electromagnetic field data is assumed to store the three magnetic-field
  components in components 3, 4 and 5 (the Maxwell/EM field layout
  ``[Ex, Ey, Ez, Bx, By, Bz, ...]``).

  Args:
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data, either as a ``GData`` object or as a
      ``(grid, values)`` tuple, whose last-axis components 3:6 are
      ``(Bx, By, Bz)``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple where ``grid`` is the
    field grid and ``values`` is the scalar magnetic-field magnitude
    ``|B| = sqrt(Bx**2 + By**2 + Bz**2)``.
  """
  field_grid, field_values = input_parser(field)
  b_values = field_values[..., 3:6]
  _, mag_B_sq = mag_sq((field_grid, b_values))
  out_values = np.sqrt(mag_B_sq)

  return field_grid, out_values


def get_vt(species: GData | Tuple[list, np.ndarray], gas_gamma: float = 5.0/3.0,
    num_moms : int | None = None, mass: float = 1.0, mu_0: float = 1.0,
    sqrt2: bool = True, mhd: bool = False) -> Tuple[list, np.ndarray]:
  """Compute the thermal velocity v_th of a species.

  The thermal velocity is computed from the species temperature ``T`` and mass
  ``m`` as ``v_th = sqrt(T/m)``, optionally scaled by ``sqrt(2)``. The mass is
  taken from the data context (``species.ctx["mass"]``) when available,
  otherwise the ``mass`` argument is used.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species moment data, either as a ``GData`` object or a ``(grid, values)``
      tuple.
    gas_gamma: float
      Adiabatic index used when computing the temperature/pressure. Defaults to
      ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10) in the input data. If ``None`` it is inferred
      from the number of components.
    mass: float
      Particle mass used when no mass is found in the data context. Defaults to
      ``1.0``.
    mu_0: float
      Vacuum permeability, forwarded to the MHD temperature computation when
      ``mhd`` is ``True``. Defaults to ``1.0``.
    sqrt2: bool
      If ``True`` (default), multiply the result by ``sqrt(2)`` (i.e.
      ``v_th = sqrt(2 T/m)``).
    mhd: bool
      If ``True``, compute the temperature from MHD moments (subtracting the
      magnetic pressure); otherwise use the fluid moments. Defaults to
      ``False``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the thermal velocity field.
  """
  m = species.ctx["mass"] if species.ctx["mass"] else mass

  if mhd:
    out_grid, temp = get_mhd_temp(species, gas_gamma=gas_gamma, mu_0=mu_0)
  else:
    out_grid, temp = get_temp(species, gas_gamma=gas_gamma, num_moms=num_moms)
  # end
  out_values = np.sqrt(temp/m)
  if sqrt2:
    out_values *= np.sqrt(2.0)

  return out_grid, out_values


def get_vA(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    mu_0: float = 1.0) -> Tuple[list, np.ndarray]:
  """Compute the Alfven velocity v_A.

  The Alfven velocity is ``v_A = |B| / sqrt(mu_0 * rho)``, where ``|B|`` is the
  magnetic-field magnitude and ``rho`` is the mass density (fluid moment data
  already includes the mass factor in the density). The permeability is taken
  from the field context (``field.ctx["mu_0"]``) when available, otherwise the
  ``mu_0`` argument is used.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species moment data providing the mass density, as a ``GData`` object or
      a ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data providing the magnetic field, as a ``GData``
      object or a ``(grid, values)`` tuple.
    mu_0: float
      Vacuum permeability used when none is found in the field context.
      Defaults to ``1.0``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the Alfven velocity field.
  """
  mu = field.ctx["mu_0"] if field.ctx["mu_0"] else mu_0

  _, magB = get_magB(field)
  # Fluid data already has mass factor in density
  out_grid, rho = get_density(species)
  out_values = magB/np.sqrt(mu*rho)

  return out_grid, out_values


def get_omegaC(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    mass: float = 1.0, charge: float = 1.0) -> Tuple[list, np.ndarray]:
  """Compute the cyclotron (gyro) frequency omega_c.

  The cyclotron frequency is ``omega_c = |q| * |B| / m``. Mass and charge are
  taken from the species context (``species.ctx["mass"]`` /
  ``species.ctx["charge"]``) when available, otherwise the ``mass`` and
  ``charge`` arguments are used.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species data providing the mass and charge, as a ``GData`` object or a
      ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data providing the magnetic field, as a ``GData``
      object or a ``(grid, values)`` tuple.
    mass: float
      Particle mass used when none is found in the species context. Defaults to
      ``1.0``.
    charge: float
      Particle charge used when none is found in the species context. Defaults
      to ``1.0``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the cyclotron frequency field.
  """
  m = species.ctx["mass"] if species.ctx["mass"] else mass
  q = species.ctx["charge"] if species.ctx["charge"] else charge

  out_grid, magB = get_magB(field)
  out_values = abs(q)*magB/m

  return out_grid, out_values


def get_omegaP(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    mass: float = 1.0, charge: float = 1.0, epsilon_0: float = 1.0) -> Tuple[list, np.ndarray]:
  """Compute the plasma frequency omega_p.

  The plasma frequency is ``omega_p = sqrt(q**2 * n / (m**2 * epsilon_0))``,
  where the number density ``n`` is obtained from the density divided by the
  mass implicitly through ``rho`` (fluid density already carries the mass
  factor, hence the ``q**2/m**2`` grouping). Mass and charge are taken from the
  species context when available; the permittivity is taken from the field
  context (``field.ctx["epsilon_0"]``) when available.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species data providing density, mass, and charge, as a ``GData`` object
      or a ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data providing the permittivity from its context,
      as a ``GData`` object or a ``(grid, values)`` tuple.
    mass: float
      Particle mass used when none is found in the species context. Defaults to
      ``1.0``.
    charge: float
      Particle charge used when none is found in the species context. Defaults
      to ``1.0``.
    epsilon_0: float
      Vacuum permittivity used when none is found in the field context.
      Defaults to ``1.0``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the plasma frequency field.
  """
  m = species.ctx["mass"] if species.ctx["mass"] else mass
  q = species.ctx["charge"] if species.ctx["charge"] else charge
  epsilon = field.ctx["epsilon_0"] if field.ctx["epsilon_0"] else epsilon_0

  # Fluid data already has mass factor in density
  out_grid, rho = get_density(species)
  qbym2 = q**2/m**2
  out_values = np.sqrt(qbym2*rho/epsilon)

  return out_grid, out_values


def get_d(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    mass: float = 1.0, charge: float = 1.0, epsilon_0: float = 1.0,
    mu_0 : float = 1.0) -> Tuple[list, np.ndarray]:
  """Compute the inertial (skin-depth) length d.

  The inertial length is ``d = c / omega_p``, where the speed of light is
  ``c = 1 / sqrt(epsilon_0 * mu_0)`` and ``omega_p`` is the plasma frequency.
  The permittivity and permeability are taken from the field context
  (``field.ctx["epsilon_0"]`` / ``field.ctx["mu_0"]``) when available.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species data providing density, mass, and charge, as a ``GData`` object
      or a ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data providing the permittivity and permeability,
      as a ``GData`` object or a ``(grid, values)`` tuple.
    mass: float
      Particle mass used when none is found in the species context. Defaults to
      ``1.0``.
    charge: float
      Particle charge used when none is found in the species context. Defaults
      to ``1.0``.
    epsilon_0: float
      Vacuum permittivity used when none is found in the field context.
      Defaults to ``1.0``.
    mu_0: float
      Vacuum permeability used when none is found in the field context.
      Defaults to ``1.0``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the inertial length field.
  """
  epsilon = field.ctx["epsilon_0"] if field.ctx["epsilon_0"] else epsilon_0
  mu = field.ctx["mu_0"] if field.ctx["mu_0"] else mu_0

  out_grid, omegaP = get_omegaP(species=species, field=field, mass=mass, charge=charge,
    epsilon_0=epsilon_0)
  light_speed = 1.0/np.sqrt(epsilon*mu)
  out_values = light_speed/omegaP

  return out_grid, out_values


def get_lambdaD(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    gas_gamma: float = 5.0/3.0, num_moms: int | None = None,
    mass: float = 1.0, charge: float = 1.0, epsilon_0: float = 1.0,
    mu_0 : float = 1.0, sqrt2: float = True) -> Tuple[list, np.ndarray]:
  """Compute the Debye length lambda_D.

  The Debye length is ``lambda_D = v_th / omega_p``, where ``v_th`` is the
  thermal velocity and ``omega_p`` is the plasma frequency. When ``sqrt2`` is
  ``True`` the extra ``sqrt(2)`` factor introduced into ``v_th`` is divided back
  out so the result remains the conventional Debye length.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species data, as a ``GData`` object or a ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data providing the permittivity, as a ``GData``
      object or a ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index used when computing the temperature. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10) in the input data. If ``None`` it is inferred
      from the number of components.
    mass: float
      Particle mass used when none is found in the species context. Defaults to
      ``1.0``.
    charge: float
      Particle charge used when none is found in the species context. Defaults
      to ``1.0``.
    epsilon_0: float
      Vacuum permittivity used when none is found in the field context.
      Defaults to ``1.0``.
    mu_0: float
      Vacuum permeability, forwarded to the thermal velocity computation.
      Defaults to ``1.0``.
    sqrt2: float
      If truthy (default), divide out the ``sqrt(2)`` factor carried by the
      thermal velocity so the standard Debye length is returned.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the Debye length field.
  """
  _, omegaP = get_omegaP(species=species, field=field, mass=mass, charge=charge,
    epsilon_0=epsilon_0)
  out_grid, vt = get_vt(species=species, gas_gamma=gas_gamma, num_moms=num_moms,
      mass=mass, mu_0=mu_0, sqrt2=sqrt2)
  out_values = vt / omegaP
  if sqrt2:
    out_values /= np.sqrt(2.0)
  # end

  return out_grid, out_values


def get_rho(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    gas_gamma: float = 5.0/3.0, num_moms: int | None = None,
    mass: float = 1.0, charge: float = 1.0, epsilon_0: float = 1.0,
    mu_0 : float = 1.0, sqrt2: float = True) -> Tuple[list, np.ndarray]:
  """Compute the gyroradius (Larmor radius) rho.

  The gyroradius is ``rho = v_th / omega_c``, where ``v_th`` is the thermal
  velocity and ``omega_c`` is the cyclotron frequency. When ``sqrt2`` is
  ``False`` the result is multiplied by ``sqrt(2)`` so that the gyroradius is
  defined consistently with a ``sqrt(2)``-scaled thermal velocity.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species data, as a ``GData`` object or a ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data providing the magnetic field, as a ``GData``
      object or a ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index used when computing the temperature. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10) in the input data. If ``None`` it is inferred
      from the number of components.
    mass: float
      Particle mass used when none is found in the species context. Defaults to
      ``1.0``.
    charge: float
      Particle charge used when none is found in the species context. Defaults
      to ``1.0``.
    epsilon_0: float
      Vacuum permittivity (accepted for signature consistency). Defaults to
      ``1.0``.
    mu_0: float
      Vacuum permeability, forwarded to the thermal velocity computation.
      Defaults to ``1.0``.
    sqrt2: float
      Controls the ``sqrt(2)`` thermal-velocity convention; when ``False`` the
      result is multiplied by ``sqrt(2)``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the gyroradius field.
  """
  _, omegaC = get_omegaC(species=species, field=field, mass=mass, charge=charge)
  out_grid, vt = get_vt(species=species, gas_gamma=gas_gamma, num_moms=num_moms,
      mass=mass, mu_0=mu_0, sqrt2=sqrt2)

  out_values = vt/omegaC
  if not sqrt2:
    out_values *= np.sqrt(2.0)
  # end

  return out_grid, out_values


def get_beta(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    gas_gamma: float = 5.0/3.0, num_moms: int | None = None,
    mass: float = 1.0, mu_0 : float = 1.0, sqrt2: float = True) -> Tuple[list, np.ndarray]:
  """Compute the plasma beta.

  The plasma beta is computed as the ratio ``v_th**2 / v_A**2``, where ``v_th``
  is the thermal velocity and ``v_A`` is the Alfven velocity. When ``sqrt2`` is
  ``False`` the result is multiplied by ``2`` to account for the missing
  ``sqrt(2)`` factor in the thermal velocity.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Species data providing temperature and density, as a ``GData`` object or
      a ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data providing the magnetic field, as a ``GData``
      object or a ``(grid, values)`` tuple.
    gas_gamma: float
      Adiabatic index used when computing the temperature. Defaults to ``5/3``.
    num_moms: int | None
      Number of moments (5 or 10) in the input data. If ``None`` it is inferred
      from the number of components.
    mass: float
      Particle mass used when none is found in the species context. Defaults to
      ``1.0``.
    mu_0: float
      Vacuum permeability used for the Alfven velocity. Defaults to ``1.0``.
    sqrt2: float
      Controls the ``sqrt(2)`` thermal-velocity convention; when ``False`` the
      result is multiplied by ``2``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the plasma beta field.
  """
  _, v_A = get_vA(species=species, field=field, mu_0=mu_0)
  out_grid, vt = get_vt(species=species, gas_gamma=gas_gamma, num_moms=num_moms,
      mass=mass, mu_0=mu_0, sqrt2=sqrt2)
  out_values = vt**2 / v_A**2
  if not sqrt2:
    out_values *= 2.0

  return out_grid, out_values
