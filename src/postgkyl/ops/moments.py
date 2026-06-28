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
  """Five-moment primitive/derived variable (density, vel, pressure, ke, ...)."""
  return _dispatch("euler", _EULER_VARS, data, variable, gas_gamma, 1.0, inplace, tag, label)


def tenmoment(data: "GData", variable: str, *, gas_gamma: float = 5.0 / 3,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Ten-moment primitive/derived variable (adds pressureTensor, pxx..pzz)."""
  return _dispatch("tenmoment", _TENMOMENT_VARS, data, variable, gas_gamma, 1.0,
      inplace, tag, label)


def mhd(data: "GData", variable: str, *, gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Ideal-MHD primitive/derived variable (density, vel, B*, pressure, ...)."""
  return _dispatch("mhd", _MHD_VARS, data, variable, gas_gamma, mu_0, inplace, tag, label)


def velocity(density: "GData", momentum: "GData", *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Velocity from density and momentum moments (momentum / density)."""
  values = momentum.get_values() / density.get_values()
  return density._result(density.get_grid(), values, inplace=inplace, tag=tag, label=label)
