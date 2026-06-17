"""Registry of pre-named gyrokinetic quantities.

Each entry maps a quantity name to a dict with:
  - files: list of file combinations to try.
  - fetch_func: corresponding fetch function for each file combo.
  - scale_func: default scaling function for each file combo.
  - label: default matplotlib label ('%s' is replaced by species name)
"""

from postgkyl.util.gk_quantities.fetch_funcs as ff
from postgkyl.util.gk_quantities.scale_funcs import scale_disabled

gk_quant_registry: dict = {
  # Density.
  "den": {
    "files":      [["MaxwellianMoments"], ["BiMaxwellianMoments"], ["M0"]],
    "fetch_func": [fetch_comp0, fetch_comp0, fetch_comp0],
    "scale_func": [scale_disabled, scale_disabled, scale_disabled],
    "label":      r"$n_{%s}$ (m$^{-3}$)",
  },
  # Parallel drift speed.
  "upar": {
    "files":      [["MaxwellianMoments"], ["BiMaxwellianMoments"], ["M0", "M1"]],
    "fetch_func": [fetch_comp1, fetch_comp1, fetch_upar_from_M0M1],
    "scale_func": [scale_disabled, scale_disabled, scale_disabled],
    "label":      r"$u_{\parallel %s}$ (m/s)",
  },
  # Parallel temperature.
  "Tpar": {
    "files":      [["BiMaxwellianMoments"]],
    "fetch_func": [fetch_comp2],
    "scale_func": [scale_massDe],
    "label":      r"$T_{\parallel %s}$ (J)",
  },
  # Perpendicular temperature.
  "Tperp": {
    "files":      [["BiMaxwellianMoments"]],
    "fetch_func": [fetch_comp3],
    "scale_func": [scale_massDe],
    "label":      r"$T_{\perp %s}$ (J)",
  },
  # Pressure.
  "press": {
    "files":      [["MaxwellianMoments"], ["BiMaxwellianMoments"]],
    "fetch_func": [fetch_press_from_maxwellian, fetch_press_from_bimaxwellian],
    "scale_func": [scale_disabled, scale_disabled],
    "label":      r"$p_{%s}$ (Pa)",
  },
}
