"""Registry of pre-named gyrokinetic quantities.

Each entry maps a quantity name to a dict with:
  - source: list of file combinations to try.
  - fetch_func: corresponding fetch function for each file combo.
  - label: default matplotlib label ('%s' is replaced by species name)
"""

import postgkyl.utils.gk_quantities.fetch_funcs as ff

# List of geometry files written out by the GK solver.
gk_geo_files = [
  "geo_corn_bmag",
  "geo_corn_bmag_inv",
  "geo_corn_mapc2p",
  "geo_corn_mc2nu_pos",
  "geo_corn_mc2nu_pos_deflated",
  "geo_corn_nodes",
  "geo_int_B3",
  "geo_int_b_i",
  "geo_int_bcart",
  "geo_int_bioverJB",
  "geo_int_bmag",
  "geo_int_cmag",
  "geo_int_dualcurlbhat",
  "geo_int_dualcurlbhatoverB",
  "geo_int_dxdz",
  "geo_int_dzdx",
  "geo_int_eps2",
  "geo_int_g_ij",
  "geo_int_g_ij_neut",
  "geo_int_gij",
  "geo_int_gij_neut",
  "geo_int_gxxj",
  "geo_int_gxyj",
  "geo_int_gxzj",
  "geo_int_gyyj",
  "geo_int_jacobgeo",
  "geo_int_jacobgeo_inv",
  "geo_int_jacobtot",
  "geo_int_jacobtot_inv",
  "geo_int_mapc2p",
  "geo_int_nodes",
  "geo_int_normals",
  "geo_int_qprofile",
  "geo_int_rtg33inv",
  "geo_surf0_B3",
  "geo_surf0_b_i",
  "geo_surf0_bimpactangle",
  "geo_surf0_bmag",
  "geo_surf0_cmag",
  "geo_surf0_deltats",
  "geo_surf0_jacobgeo",
  "geo_surf0_jacobtot_inv",
  "geo_surf0_lenr",
  "geo_surf0_normals",
  "geo_surf0_normcurlbhat",
]

# List of quantities that do not depend on species and are written every frame.
gk_conf_frame_files = [
  "field", # Electrostatic potential.
  "apar", # Parallel component of the magnetic field vector.
]

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

# ExB drift
_ExB_vel = {
  "source"    : [["geo_int_jacobtot_inv","geo_int_b_i","field"],],
  "fetch_func": [ff.fetch_ExB_vel],
  "label"     : r"$v_{E,%d}$ (m/s)",
}

# Magnetic field magnitude (from evaluation at interior).
_geo_int_bmag = {
  "source"    : [["geo_int_bmag"],],
  "fetch_func": [ff.fetch_s0c0],
  "label"     : r"$B$ (T)",
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
  "ExB_vel" : _ExB_vel,
  "bmag" : _geo_int_bmag,
}
