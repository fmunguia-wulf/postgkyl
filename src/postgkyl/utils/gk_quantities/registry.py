"""Registry of pre-named gyrokinetic quantities.

Each entry maps a quantity name to a dict with:
  - source: list of file combinations to try.
  - fetch_func: corresponding fetch function for each file combo.
  - label: default matplotlib label ('%s' is replaced by species name)
"""

import postgkyl.utils.gk_quantities.fetch_funcs as ff

# Zeroth velocity moment.
_M0 = {
  "source"     : [["M0"], ["M0M1M2"], ["M0M1M2parM2perp"], ["MaxwellianMoments"], ["BiMaxwellianMoments"], ["HamiltonianMoments"],],
  "fetch_func" : [ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0],
  "label"      : r"$M_{0%s}$ (m$^{-3}$)",
}

# First velocity moment.
_M1 = {
  "source"     : [["M1"], ["M0M1M2"], ["M0M1M2parM2perp"], ["MaxwellianMoments"], ["BiMaxwellianMoments"], ["HamiltonianMoments"],],
  "fetch_func" : [ff.fetch_s0c0, ff.fetch_s0c1, ff.fetch_s0c1, ff.fetch_s0c0_mul_s0c1, ff.fetch_s0c0_mul_s0c1, ff.fetch_M1_from_H],
  "label"      : r"$M_{1%s}$ (m$^{-2}$/s)",
}

# Second parallel velocity moment.
_M2par = {
  "source"     : [["M2par"], ["M0M1M2parM2perp"], ["M2","M2perp"]],
  "fetch_func" : [ff.fetch_s0c0, ff.fetch_s0c2, ff.fetch_s0c0_sub_s1c0],
  "label"      : r"$M_{2\parallel%s}$ (m$^{-1}$/s$^2$)",
}

# Second perpendicular velocity moment.
_M2perp = {
  "source"     : [["M2perp"], ["M0M1M2parM2perp"], ["M2","M2par"]],
  "fetch_func" : [ff.fetch_s0c0, ff.fetch_s0c3, ff.fetch_s0c0_sub_s1c0],
  "label"      : r"$M_{2\perp%s}$ (m$^{-1}$/s$^2$)",
}

# Second velocity moment.
_M2 = {
  "source"     : [["M2"], ["M0M1M2"], ["M0M1M2parM2perp"], [_M2par,_M2perp],],
  "fetch_func" : [ff.fetch_s0c0, ff.fetch_s0c2, ff.fetch_s0c2_add_s0c3, ff.fetch_s0c0_add_s1c0,],
  "label"      : r"$M_{2%s}$ (m$^{-1}$/s$^2$)",
}

# Parallel drift speed.
_upar = {
  "source"    : [["MaxwellianMoments"], ["BiMaxwellianMoments"], [_M0, _M1]],
  "fetch_func": [ff.fetch_s0c1, ff.fetch_s0c1, ff.fetch_s1c0_div_s0c0],
  "label"     : r"$u_{\parallel %s}$ (m/s)",
}

# Parallel temperature.
_Tpar = {
  "source"    : [["BiMaxwellianMoments"],[_M0,_M1,_M2par],],
  "fetch_func": [ff.fetch_Tpar_from_BiMax, ff.fetch_Tpar_from_M0_M1_M2par],
  "label"     : r"$T_{\parallel %s}$ (J)",
}

# Perpendicular temperature.
_Tperp = {
  "source"    : [["BiMaxwellianMoments"], [_M0,_M2perp]],
  "fetch_func": [ff.fetch_Tperp_from_BiMax, ff.fetch_Tperp_from_M0_M2perp],
  "label"     : r"$T_{\perp %s}$ (J)",
}

# Temperature.
_temp = {
  "source"    : [["MaxwellianMoments"], [_Tpar,_Tperp]],
  "fetch_func": [ff.fetch_temp_from_Max, ff.fetch_temp_from_Tpar_Tperp],
  "label"     : r"$T_{%s}$ (J)",
}

# Pressure.
_press = {
  "source"    : [["MaxwellianMoments"], ["BiMaxwellianMoments"], [_M0,_temp]],
  "fetch_func": [ff.fetch_press_from_Max, ff.fetch_press_from_BiMax, ff.fetch_s0c0_mul_s1c0],
  "label"     : r"$p_{%s}$ (Pa)",
}

gk_quant_registry: dict = {
  "M0" : _M0,
  "M1" : _M1,
  "M2par" : _M2par,
  "M2perp" : _M2perp,
  "M2" : _M2,
  "den": _M0,
  "upar": _upar,
  "Tpar": _Tpar,
  "Tperp": _Tperp,
  "temp" : _temp,
  "press" : _press,
}
