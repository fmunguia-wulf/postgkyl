"""
Registry of pre-named gyrokinetic quantities.

Each entry is an instance of the GkQuantity class.
"""

import postgkyl.gk.gk_quantities.fetch_funcs as ff
from .gkquantity import GkQuantity, GkQuantityRegistry

# Instance that will hold all available gyrokinetic quantities.
gk_quant_registry: GkQuantityRegistry = GkQuantityRegistry()

# ------------------- Register quantities -------------------

# -----------------------------------
# --- Scalar geometric quantities ---
# -----------------------------------

# Configuration space Jacobian (interior).
_geo_int_jacobgeo : GkQuantity = GkQuantity(
  name = "geo_int_jacobgeo",
  source = [["geo_int_jacobgeo"],],
  fetch_func = [ff.fetch_s0c0],
  label = r"$J$",
  is_geo = True
)
gk_quant_registry.register(_geo_int_jacobgeo)

# Reciprocal of configuration space Jacobian (interior).
_geo_int_jacobgeo_inv : GkQuantity = GkQuantity(
  name = "geo_int_jacobgeo_inv",
  source = [["geo_int_jacobgeo_inv"],],
  fetch_func = [ff.fetch_s0c0],
  label = r"$J^{-1}$",
  is_geo = True
)
gk_quant_registry.register(_geo_int_jacobgeo_inv)

# Total Jacobian (interior).
_geo_int_jacobtot : GkQuantity = GkQuantity(
  name = "geo_int_jacobtot",
  source = [["geo_int_jacobtot"],],
  fetch_func = [ff.fetch_s0c0],
  label = r"$J$",
  is_geo = True
)
gk_quant_registry.register(_geo_int_jacobtot)

# Reciprocal of Jacobian times bmag (interior).
_geo_int_jacobtot_inv : GkQuantity = GkQuantity(
  name = "geo_int_jacobtot_inv",
  source = [["geo_int_jacobtot_inv"],],
  fetch_func = [ff.fetch_s0c0],
  label = r"$(J B)^{-1}$",
  is_geo = True
)
gk_quant_registry.register(_geo_int_jacobtot_inv)

# Magnetic field magnitude (interior).
_geo_int_bmag : GkQuantity = GkQuantity(
  name = "geo_int_bmag",
  source = [["geo_int_bmag"],],
  fetch_func = [ff.fetch_s0c0],
  label = r"$B$ (T)",
  is_geo = True
)
gk_quant_registry.register(_geo_int_bmag)

# -----------------------------------
# --- Vector geometric quantities ---
# -----------------------------------

# Covariant components of magnetic field unit vector (interior).
_geo_int_b_i : GkQuantity = GkQuantity(
  name = "geo_int_b_i",
  source = [["geo_int_b_i"],],
  fetch_func = [ff.fetch_s0cAll],
  label = r"$b_%s$",
  is_vector = True,
  is_geo = True
)
gk_quant_registry.register(_geo_int_b_i)

# --------------------------------------------
# --- Field quantities (species-dependent) ---
# --------------------------------------------

# Electrostatic potential.
_field : GkQuantity = GkQuantity(
  name = "field",
  source = [["field"],],
  fetch_func = [ff.fetch_s0c0],
  label = r"$\phi$ (V)",
  is_time_dep = True,
)
gk_quant_registry.register(_field)

# ------------------------------------------
# --- Plasma moments (species-dependent) ---
# ------------------------------------------

# Zeroth velocity moment.
_M0 : GkQuantity = GkQuantity(
  name = "M0",
  source = [["M0"], ["M0M1M2"], ["M0M1M2parM2perp"], ["MaxwellianMoments"], ["BiMaxwellianMoments"], ["HamiltonianMoments"],],
  fetch_func = [ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0, ff.fetch_s0c0],
  label = r"$M_{0%s}$ (m$^{-3}$)",
  is_species_dep = True,
  is_time_dep = True
)
gk_quant_registry.register(_M0)

# First velocity moment.
_M1 : GkQuantity = GkQuantity(
  name = "M1",
  source = [["M1"], ["M0M1M2"], ["M0M1M2parM2perp"], ["MaxwellianMoments"], ["BiMaxwellianMoments"], ["HamiltonianMoments"],],
  fetch_func = [ff.fetch_s0c0, ff.fetch_s0c1, ff.fetch_s0c1, ff.fetch_s0c0_mul_s0c1, ff.fetch_s0c0_mul_s0c1, ff.fetch_M1_from_H],
  label = r"$M_{1%s}$ (m$^{-2}$/s)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_M1)

# Second parallel velocity moment.
_M2par : GkQuantity = GkQuantity(
  name = "M2par",
  source = [["M2par"], ["M0M1M2parM2perp"], ["M2","M2perp"]],
  fetch_func = [ff.fetch_s0c0, ff.fetch_s0c2, ff.fetch_s0c0_sub_s1c0],
  label = r"$M_{2\parallel%s}$ (m$^{-1}$/s$^2$)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_M2par)

# Second perpendicular velocity moment.
_M2perp : GkQuantity = GkQuantity(
  name = "M2perp",
  source = [["M2perp"], ["M0M1M2parM2perp"], ["M2","M2par"]],
  fetch_func = [ff.fetch_s0c0, ff.fetch_s0c3, ff.fetch_s0c0_sub_s1c0],
  label = r"$M_{2\perp%s}$ (m$^{-1}$/s$^2$)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_M2perp)

# Second velocity moment.
_M2 : GkQuantity = GkQuantity(
  name = "M2",
  source = [["M2"], ["M0M1M2"], ["M0M1M2parM2perp"], [_M2par,_M2perp],],
  fetch_func = [ff.fetch_s0c0, ff.fetch_s0c2, ff.fetch_s0c2_add_s0c3, ff.fetch_s0c0_add_s1c0,],
  label = r"$M_{2%s}$ (m$^{-1}$/s$^2$)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_M2)

# Parallel drift speed.
_upar : GkQuantity = GkQuantity(
  name = "upar",
  source = [["MaxwellianMoments"], ["BiMaxwellianMoments"], [_M0, _M1]],
  fetch_func = [ff.fetch_s0c1, ff.fetch_s0c1, ff.fetch_s1c0_div_s0c0],
  label = r"$u_{\parallel %s}$ (m/s)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_upar)

# Parallel temperature.
_Tpar : GkQuantity = GkQuantity(
  name = "Tpar",
  source = [["BiMaxwellianMoments"],[_M0,_M1,_M2par],],
  fetch_func = [ff.fetch_Tpar_from_BiMax, ff.fetch_Tpar_from_M0_M1_M2par],
  label = r"$T_{\parallel %s}$ (J)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_Tpar)

# Perpendicular temperature.
_Tperp : GkQuantity = GkQuantity(
  name = "Tperp",
  source = [["BiMaxwellianMoments"], [_M0,_M2perp]],
  fetch_func = [ff.fetch_Tperp_from_BiMax, ff.fetch_Tperp_from_M0_M2perp],
  label = r"$T_{\perp %s}$ (J)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_Tperp)

# ---------------------------------------------------
# --- Combined plasma moments (species-dependent) ---
# ---------------------------------------------------

# Temperature.
_temp : GkQuantity = GkQuantity(
  name = "temp",
  source = [["MaxwellianMoments"], [_Tpar,_Tperp]],
  fetch_func = [ff.fetch_temp_from_Max, ff.fetch_temp_from_Tpar_Tperp],
  label = r"$T_{%s}$ (J)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_temp)

# Pressure.
_press : GkQuantity = GkQuantity(
  name = "press",
  source = [["MaxwellianMoments"], ["BiMaxwellianMoments"], [_M0,_temp]],
  fetch_func = [ff.fetch_press_from_Max, ff.fetch_press_from_BiMax, ff.fetch_s0c0_mul_s1c0],
  label = r"$p_{%s}$ (Pa)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_press)

# Parallel pressure.
_presspar : GkQuantity = GkQuantity(
  name = "presspar",
  source = [[_M0,_Tpar]],
  fetch_func = [ff.fetch_press_p],
  label = r"$p_{\parallel %s}$ (Pa)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_presspar)

# Perpendicular pressure.
_pressperp : GkQuantity = GkQuantity(
  name = "pressperp",
  source = [[_M0,_Tperp]],
  fetch_func = [ff.fetch_press_p],
  label = r"$p_{\perp %s}$ (Pa)",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_pressperp)

# Plasma beta.
_beta : GkQuantity = GkQuantity(
  name = "beta",
  source = [[_geo_int_bmag,_press],],
  fetch_func = [ff.fetch_beta_from_bmag_press],
  label = r"$\beta_{%s}$",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_beta)

# ------------------------
# --- Drift velocities ---
# ------------------------

# ExB drift velocity.
_ExB_vel : GkQuantity = GkQuantity(
  name = "ExB_vel",
  source = [[_geo_int_jacobtot_inv,_geo_int_bmag,_geo_int_b_i,_field],],
  fetch_func = [ff.fetch_ExB_vel],
  label = r"$v_{E,%s}$ (m/s)",
  is_time_dep = True,
  is_vector = True
)
gk_quant_registry.register(_ExB_vel)

# Grad B drift velocity.
_gradB_vel : GkQuantity = GkQuantity(
  name = "gradB_vel",
  source = [[_geo_int_jacobtot_inv,_geo_int_bmag,_geo_int_b_i, _Tperp]],
  fetch_func= [ff.fetch_gradB_vel],
  label = r"$v_{\nabla B,%s}$ (m/s)",
  is_time_dep = True,
  is_species_dep = True,
  is_vector = True
)
gk_quant_registry.register(_gradB_vel)

# Diamagnetic drift velocity.
_diamag_vel : GkQuantity = GkQuantity(
  name = "diamag_vel",
  source = [[_geo_int_jacobtot_inv,_geo_int_bmag,_geo_int_b_i, _M0, _pressperp]],
  fetch_func= [ff.fetch_diamag_vel],
  label = r"$v_{dia,%s}$ (m/s)",
  is_time_dep = True,
  is_species_dep = True,
  is_vector = True
)
gk_quant_registry.register(_diamag_vel)