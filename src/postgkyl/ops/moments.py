"""The moment verbs — extract primitive/derived variables from fluid moments.

``euler`` (5-moment), ``tenmoment`` (10-moment), and ``mhd`` dispatch on a
variable name to the corresponding :mod:`postgkyl.tools.prim_vars` function;
``velocity`` divides momentum by density.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import postgkyl.tools.prim_vars as pv

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def _euler_map(num_moms: int) -> dict:
  return {
      "density": lambda d, g, mu: pv.get_density(d),
      "xvel": lambda d, g, mu: pv.get_vx(d),
      "yvel": lambda d, g, mu: pv.get_vy(d),
      "zvel": lambda d, g, mu: pv.get_vz(d),
      "vel": lambda d, g, mu: pv.get_vi(d),
      "pressure": lambda d, g, mu: pv.get_p(d, gas_gamma=g, num_moms=num_moms),
      "ke": lambda d, g, mu: pv.get_ke(d, gas_gamma=g, num_moms=num_moms),
      "temp": lambda d, g, mu: pv.get_temp(d, gas_gamma=g, num_moms=num_moms),
      "sound": lambda d, g, mu: pv.get_sound(d, gas_gamma=g, num_moms=num_moms),
      "mach": lambda d, g, mu: pv.get_mach(d, gas_gamma=g, num_moms=num_moms),
  }


_EULER_VARS = _euler_map(5)

_TENMOMENT_VARS = _euler_map(10)
_TENMOMENT_VARS.update({
    "pressureTensor": lambda d, g, mu: pv.get_pij(d),
    "pxx": lambda d, g, mu: pv.get_pxx(d),
    "pxy": lambda d, g, mu: pv.get_pxy(d),
    "pxz": lambda d, g, mu: pv.get_pxz(d),
    "pyy": lambda d, g, mu: pv.get_pyy(d),
    "pyz": lambda d, g, mu: pv.get_pyz(d),
    "pzz": lambda d, g, mu: pv.get_pzz(d),
})

_MHD_VARS = {
    "density": lambda d, g, mu: pv.get_density(d),
    "xvel": lambda d, g, mu: pv.get_vx(d),
    "yvel": lambda d, g, mu: pv.get_vy(d),
    "zvel": lambda d, g, mu: pv.get_vz(d),
    "vel": lambda d, g, mu: pv.get_vi(d),
    "Bx": lambda d, g, mu: pv.get_mhd_Bx(d),
    "By": lambda d, g, mu: pv.get_mhd_By(d),
    "Bz": lambda d, g, mu: pv.get_mhd_Bz(d),
    "Bi": lambda d, g, mu: pv.get_mhd_Bi(d),
    "magpressure": lambda d, g, mu: pv.get_mhd_mag_p(d, mu_0=mu),
    "pressure": lambda d, g, mu: pv.get_mhd_p(d, gas_gamma=g, mu_0=mu),
    "temp": lambda d, g, mu: pv.get_mhd_temp(d, gas_gamma=g, mu_0=mu),
    "sound": lambda d, g, mu: pv.get_mhd_sound(d, gas_gamma=g, mu_0=mu),
    "mach": lambda d, g, mu: pv.get_mhd_mach(d, gas_gamma=g, mu_0=mu),
}


def _dispatch(name, table, data, variable, gas_gamma, mu_0, inplace, tag, label):
  try:
    fn = table[variable]
  except KeyError:
    raise ValueError(
        f"Unknown {name} variable '{variable}'. Choices: {sorted(table)}") from None
  # end
  grid, values = fn(data, gas_gamma, mu_0)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)


def euler(data: "GData", variable: str, *, gas_gamma: float = 5.0 / 3,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Five-moment (Euler) primitive/derived variable.

  Computes a primitive or derived fluid quantity from five-moment data
  (density, three momenta, energy). The quantity is selected by ``variable``.

  Args:
    data: GData
      Five-moment fluid data (components: rho, rho*ux, rho*uy, rho*uz, E).
    variable: str
      Which quantity to extract. One of: 'density', 'xvel', 'yvel', 'zvel',
      'vel' (the three-component velocity vector), 'pressure', 'ke' (kinetic
      energy), 'temp' (temperature), 'sound' (sound speed), or 'mach' (Mach
      number).
    gas_gamma: float
      Adiabatic index used for pressure-derived quantities. Defaults to 5/3.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the requested quantity (or the mutated input when
    inplace=True).

  Raises:
    ValueError: If ``variable`` is not one of the recognized choices.
  """
  return _dispatch("euler", _EULER_VARS, data, variable, gas_gamma, 1.0, inplace, tag, label)


def tenmoment(data: "GData", variable: str, *, gas_gamma: float = 5.0 / 3,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Ten-moment primitive/derived variable.

  Computes a primitive or derived fluid quantity from ten-moment data
  (density, three momenta, and the six independent pressure-tensor moments).
  Supports all the five-moment quantities plus the full pressure tensor and
  its individual components.

  Args:
    data: GData
      Ten-moment fluid data (components: rho, rho*ux, rho*uy, rho*uz, then the
      six second moments).
    variable: str
      Which quantity to extract. One of: 'density', 'xvel', 'yvel', 'zvel',
      'vel', 'pressure', 'ke', 'temp', 'sound', 'mach', 'pressureTensor' (the
      six-component symmetric tensor), or its individual components 'pxx',
      'pxy', 'pxz', 'pyy', 'pyz', 'pzz'.
    gas_gamma: float
      Adiabatic index used for pressure-derived quantities. Defaults to 5/3.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the requested quantity (or the mutated input when
    inplace=True).

  Raises:
    ValueError: If ``variable`` is not one of the recognized choices.
  """
  return _dispatch("tenmoment", _TENMOMENT_VARS, data, variable, gas_gamma, 1.0,
      inplace, tag, label)


def mhd(data: "GData", variable: str, *, gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Ideal-MHD primitive/derived variable.

  Computes a primitive or derived quantity from ideal-MHD conserved variables
  (density, three momenta, total energy, and the three magnetic-field
  components). Magnetic and pressure quantities use the permeability ``mu_0``.

  Args:
    data: GData
      Ideal-MHD data (components: rho, rho*ux, rho*uy, rho*uz, E, Bx, By, Bz).
    variable: str
      Which quantity to extract. One of: 'density', 'xvel', 'yvel', 'zvel',
      'vel', 'Bx', 'By', 'Bz', 'Bi' (the three-component magnetic field),
      'magpressure' (magnetic pressure), 'pressure' (thermal pressure),
      'temp', 'sound', or 'mach'.
    gas_gamma: float
      Adiabatic index used for pressure-derived quantities. Defaults to 5/3.
    mu_0: float
      Vacuum permeability used for magnetic-pressure and pressure
      calculations. Defaults to 1.0.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the requested quantity (or the mutated input when
    inplace=True).

  Raises:
    ValueError: If ``variable`` is not one of the recognized choices.
  """
  return _dispatch("mhd", _MHD_VARS, data, variable, gas_gamma, mu_0, inplace, tag, label)


def velocity(density: "GData", momentum: "GData", *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Velocity from separate density and momentum moments.

  Computes the flow velocity by dividing the ``momentum`` moments by the
  ``density`` moment, component-wise. The two inputs are assumed to share the
  same grid; the result carries the ``density`` dataset's grid.

  Args:
    density: GData
      Number/mass density moment (single component); the divisor.
    momentum: GData
      Momentum moment(s) to divide by the density.
    inplace: bool
      When True, mutate and return ``density``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the velocity (or the mutated ``density`` when inplace=True).
  """
  values = momentum.get_values() / density.get_values()
  return density._result(density.get_grid(), values, inplace=inplace, tag=tag, label=label)
