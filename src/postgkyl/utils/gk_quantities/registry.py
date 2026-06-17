"""Registry of pre-named gyrokinetic quantities.

Each entry maps a quantity name to a dict with:
  - source: list of file combinations to try.
  - fetch_func: corresponding fetch function for each file combo.
  - scale_func: default scaling function for each file combo.
  - label: default matplotlib label ('%s' is replaced by species name)
"""

import postgkyl.utils.gk_quantities.fetch_funcs as ff
import postgkyl.utils.gk_quantities.scale_funcs as sf

gk_quant_registry: dict = {
  # Density.
  "den": {
    "source":      [["MaxwellianMoments"], ["BiMaxwellianMoments"], ["M0"]],
    "fetch_func": [ff.fetch_comp0, ff.fetch_comp0, ff.fetch_comp0],
    "scale_func": [sf.scale_disabled, sf.scale_disabled, sf.scale_disabled],
    "label":      r"$n_{%s}$ (m$^{-3}$)",
  },
  # Parallel drift speed.
  "upar": {
    "source":      [["MaxwellianMoments"], ["BiMaxwellianMoments"], ["M0", "M1"]],
    "fetch_func": [ff.fetch_comp1, ff.fetch_comp1, ff.fetch_upar_from_M0M1],
    "scale_func": [sf.scale_disabled, sf.scale_disabled, sf.scale_disabled],
    "label":      r"$u_{\parallel %s}$ (m/s)",
  },
  # Parallel temperature.
  "Tpar": {
    "source":      [["BiMaxwellianMoments"]],
    "fetch_func": [ff.fetch_comp2],
    "scale_func": [sf.scale_massDev],
    "label":      r"$T_{\parallel %s}$ (J)",
  },
  # Perpendicular temperature.
  "Tperp": {
    "source":      [["BiMaxwellianMoments"]],
    "fetch_func": [ff.fetch_comp3],
    "scale_func": [sf.scale_massDev],
    "label":      r"$T_{\perp %s}$ (J)",
  },
  # Pressure.
  "press": {
    "source":      [["MaxwellianMoments"], ["BiMaxwellianMoments"]],
    "fetch_func": [ff.fetch_press_from_maxwellian, ff.fetch_press_from_bimaxwellian],
    "scale_func": [sf.scale_disabled, sf.scale_disabled],
    "label":      r"$p_{%s}$ (Pa)",
  },
}
