"""The moment verbs — extract primitive/derived variables from fluid moments.

``euler`` (5-moment), ``tenmoment`` (10-moment), and ``mhd`` dispatch on a
variable name to the corresponding :mod:`postgkyl.models` function;
``velocity`` divides momentum by density directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import models
from ._guards import require_field_domain as _require_field_domain

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

_REASON = ("extracting primitive variables from raw DG coefficients would "
    "mix basis functions")


def _moment_table(num_moms: int) -> dict:
  """Variable-name -> ``(grid, values, gas_gamma, mu_0) -> (grid, values)``,
  fixed at a given moment count (5 or 10)."""
  return {
      "density": lambda g, v, gg, mu: models.get_density(g, v),
      "xvel": lambda g, v, gg, mu: models.get_vx(g, v),
      "yvel": lambda g, v, gg, mu: models.get_vy(g, v),
      "zvel": lambda g, v, gg, mu: models.get_vz(g, v),
      "vel": lambda g, v, gg, mu: models.get_vi(g, v),
      "pressure": lambda g, v, gg, mu: models.get_p(
          g, v, gas_gamma=gg, num_moms=num_moms),
      "ke": lambda g, v, gg, mu: models.get_ke(
          g, v, gas_gamma=gg, num_moms=num_moms),
      "temp": lambda g, v, gg, mu: models.get_temp(
          g, v, gas_gamma=gg, num_moms=num_moms),
      "sound": lambda g, v, gg, mu: models.get_sound(
          g, v, gas_gamma=gg, num_moms=num_moms),
      "mach": lambda g, v, gg, mu: models.get_mach(
          g, v, gas_gamma=gg, num_moms=num_moms),
  }


_EULER_VARS = _moment_table(5)

_TENMOMENT_VARS = _moment_table(10)
_TENMOMENT_VARS.update({
    "pressureTensor": lambda g, v, gg, mu: models.get_pij(g, v),
    "pxx": lambda g, v, gg, mu: models.get_pxx(g, v),
    "pxy": lambda g, v, gg, mu: models.get_pxy(g, v),
    "pxz": lambda g, v, gg, mu: models.get_pxz(g, v),
    "pyy": lambda g, v, gg, mu: models.get_pyy(g, v),
    "pyz": lambda g, v, gg, mu: models.get_pyz(g, v),
    "pzz": lambda g, v, gg, mu: models.get_pzz(g, v),
})

_MHD_VARS = {
    "density": lambda g, v, gg, mu: models.get_density(g, v),
    "xvel": lambda g, v, gg, mu: models.get_vx(g, v),
    "yvel": lambda g, v, gg, mu: models.get_vy(g, v),
    "zvel": lambda g, v, gg, mu: models.get_vz(g, v),
    "vel": lambda g, v, gg, mu: models.get_vi(g, v),
    "Bx": lambda g, v, gg, mu: models.get_mhd_Bx(g, v),
    "By": lambda g, v, gg, mu: models.get_mhd_By(g, v),
    "Bz": lambda g, v, gg, mu: models.get_mhd_Bz(g, v),
    "Bi": lambda g, v, gg, mu: models.get_mhd_Bi(g, v),
    "magpressure": lambda g, v, gg, mu: models.get_mhd_mag_p(g, v, mu_0=mu),
    "pressure": lambda g, v, gg, mu: models.get_mhd_p(g, v, gas_gamma=gg, mu_0=mu),
    "temp": lambda g, v, gg, mu: models.get_mhd_temp(g, v, gas_gamma=gg, mu_0=mu),
    "sound": lambda g, v, gg, mu: models.get_mhd_sound(g, v, gas_gamma=gg, mu_0=mu),
    "mach": lambda g, v, gg, mu: models.get_mhd_mach(g, v, gas_gamma=gg, mu_0=mu),
}


def _dispatch(name: str, table: dict, data: "GDataState", variable: str,
    gas_gamma: float, mu_0: float, inplace: bool, tag: str | None,
    label: str | None) -> "GDataState":
  _require_field_domain(data, name, _REASON)
  try:
    fn = table[variable]
  except KeyError:
    raise ValueError(
        f"Unknown {name} variable '{variable}'. Choices: {sorted(table)}") from None
  # end
  grid, values = fn(data.grid, data.values, gas_gamma, mu_0)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)


def euler(data: "GDataState", variable: str, *, gas_gamma: float = 5.0 / 3,
    inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Five-moment (Euler) primitive/derived variable.

  Computes a primitive or derived fluid quantity from five-moment data
  (density, three momenta, energy). The quantity is selected by ``variable``.

  Args:
    data: Five-moment fluid data (components: rho, rho*ux, rho*uy, rho*uz,
      E); must be NumPy-backed.
    variable: Which quantity to extract. One of: 'density', 'xvel', 'yvel',
      'zvel', 'vel' (the three-component velocity vector), 'pressure', 'ke'
      (kinetic energy), 'temp' (temperature), 'sound' (sound speed), or
      'mach' (Mach number).
    gas_gamma: Adiabatic index used for pressure-derived quantities.
    inplace: mutate and return ``data`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset of the requested quantity.

  Raises:
    ValueError: if ``data`` is native modal (gkyl-backed), or ``variable``
      is not one of the recognized choices.
  """
  return _dispatch("euler", _EULER_VARS, data, variable, gas_gamma, 1.0,
      inplace, tag, label)


def tenmoment(data: "GDataState", variable: str, *, gas_gamma: float = 5.0 / 3,
    inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Ten-moment primitive/derived variable.

  Computes a primitive or derived fluid quantity from ten-moment data
  (density, three momenta, and the six independent pressure-tensor moments).
  Supports all the five-moment quantities plus the full pressure tensor and
  its individual components.

  Args:
    data: Ten-moment fluid data (components: rho, rho*ux, rho*uy, rho*uz,
      then the six second moments); must be NumPy-backed.
    variable: Which quantity to extract. One of: 'density', 'xvel', 'yvel',
      'zvel', 'vel', 'pressure', 'ke', 'temp', 'sound', 'mach',
      'pressureTensor' (the six-component symmetric tensor), or its
      individual components 'pxx', 'pxy', 'pxz', 'pyy', 'pyz', 'pzz'.
    gas_gamma: Adiabatic index used for pressure-derived quantities.
    inplace: mutate and return ``data`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset of the requested quantity.

  Raises:
    ValueError: if ``data`` is native modal (gkyl-backed), or ``variable``
      is not one of the recognized choices.
  """
  return _dispatch("tenmoment", _TENMOMENT_VARS, data, variable, gas_gamma,
      1.0, inplace, tag, label)


def mhd(data: "GDataState", variable: str, *, gas_gamma: float = 5.0 / 3,
    mu_0: float = 1.0, inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Ideal-MHD primitive/derived variable.

  Computes a primitive or derived quantity from ideal-MHD conserved
  variables (density, three momenta, total energy, and the three
  magnetic-field components). Magnetic and pressure quantities use the
  permeability ``mu_0``.

  Args:
    data: Ideal-MHD data (components: rho, rho*ux, rho*uy, rho*uz, E, Bx,
      By, Bz); must be NumPy-backed.
    variable: Which quantity to extract. One of: 'density', 'xvel', 'yvel',
      'zvel', 'vel', 'Bx', 'By', 'Bz', 'Bi' (the three-component magnetic
      field), 'magpressure' (magnetic pressure), 'pressure' (thermal
      pressure), 'temp', 'sound', or 'mach'.
    gas_gamma: Adiabatic index used for pressure-derived quantities.
    mu_0: Vacuum permeability used for magnetic-pressure and pressure
      calculations.
    inplace: mutate and return ``data`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset of the requested quantity.

  Raises:
    ValueError: if ``data`` is native modal (gkyl-backed), or ``variable``
      is not one of the recognized choices.
  """
  return _dispatch("mhd", _MHD_VARS, data, variable, gas_gamma, mu_0,
      inplace, tag, label)


def velocity(density: "GDataState", momentum: "GDataState", *,
    inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Velocity from separate density and momentum moments.

  Computes the flow velocity by dividing the ``momentum`` moments by the
  ``density`` moment, component-wise. The two inputs are assumed to share
  the same grid; the result carries the ``density`` dataset's grid.

  Args:
    density: Number/mass density moment (single component); the divisor.
      Must be NumPy-backed.
    momentum: Momentum moment(s) to divide by the density. Must be
      NumPy-backed.
    inplace: mutate and return ``density`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset of the velocity.

  Raises:
    ValueError: if either input is native modal (gkyl-backed).
  """
  _require_field_domain(density, "velocity", _REASON)
  _require_field_domain(momentum, "velocity", _REASON)
  values = momentum.values / density.values
  return density._result(density.grid, values, inplace=inplace, tag=tag,
      label=label)
