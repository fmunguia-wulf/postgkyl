"""The gyrokinetic quantity registry — populated from ``quantities.py``.

Ported from ``src_bak/postgkyl/gk/gk_quantities/registry.py``. Each entry
names its preferred source combinations (in order) and the fetch function
for each; :func:`~postgkyl.diagnostics.gyrokinetics.quantity.GkQuantity.
get_avail_source` picks the first combination whose files are actually
present on disk.
"""

from __future__ import annotations

from . import quantities as ff
from .quantity import GkQuantity, GkQuantityRegistry

gk_quant_registry = GkQuantityRegistry()

# ----------------------------------------- scalar geometric quantities (geo)
_geo_int_jacobgeo = GkQuantity(
    name="geo_int_jacobgeo", source=[["geo_int_jacobgeo"]],
    fetch_func=[ff.fetch_s0c0], label=r"$J$", is_geo=True)
gk_quant_registry.register(_geo_int_jacobgeo)

_geo_int_jacobgeo_inv = GkQuantity(
    name="geo_int_jacobgeo_inv", source=[["geo_int_jacobgeo_inv"]],
    fetch_func=[ff.fetch_s0c0], label=r"$J^{-1}$", is_geo=True)
gk_quant_registry.register(_geo_int_jacobgeo_inv)

_geo_int_jacobtot = GkQuantity(
    name="geo_int_jacobtot", source=[["geo_int_jacobtot"]],
    fetch_func=[ff.fetch_s0c0], label=r"$J$", is_geo=True)
gk_quant_registry.register(_geo_int_jacobtot)

_geo_int_jacobtot_inv = GkQuantity(
    name="geo_int_jacobtot_inv", source=[["geo_int_jacobtot_inv"]],
    fetch_func=[ff.fetch_s0c0], label=r"$(J B)^{-1}$", is_geo=True)
gk_quant_registry.register(_geo_int_jacobtot_inv)

_geo_int_bmag = GkQuantity(
    name="geo_int_bmag", source=[["geo_int_bmag"]],
    fetch_func=[ff.fetch_s0c0], label=r"$B$ (T)", is_geo=True)
gk_quant_registry.register(_geo_int_bmag)

# ----------------------------------------- vector geometric quantities (geo)
_geo_int_b_i = GkQuantity(
    name="geo_int_b_i", source=[["geo_int_b_i"]],
    fetch_func=[ff.fetch_s0cAll], label=r"$b_%s$", is_vector=True, is_geo=True)
gk_quant_registry.register(_geo_int_b_i)

# ------------------------------------------------------------------- field
_field = GkQuantity(
    name="field", source=[["field"]], fetch_func=[ff.fetch_s0c0],
    label=r"$\phi$ (V)", is_time_dep=True)
gk_quant_registry.register(_field)

# --------------------------------------------------- plasma moments (per-sp)
_M0 = GkQuantity(
    name="M0",
    source=[["M0"], ["M0M1M2"], ["M0M1M2parM2perp"], ["MaxwellianMoments"],
        ["BiMaxwellianMoments"], ["HamiltonianMoments"]],
    fetch_func=[ff.fetch_s0c0] * 6,
    label=r"$M_{0%s}$ (m$^{-3}$)", is_species_dep=True, is_time_dep=True)
gk_quant_registry.register(_M0)

_M1 = GkQuantity(
    name="M1",
    source=[["M1"], ["M0M1M2"], ["M0M1M2parM2perp"], ["MaxwellianMoments"],
        ["BiMaxwellianMoments"], ["HamiltonianMoments"]],
    fetch_func=[ff.fetch_s0c0, ff.fetch_s0c1, ff.fetch_s0c1,
        ff.fetch_s0c0_mul_s0c1, ff.fetch_s0c0_mul_s0c1, ff.fetch_M1_from_H],
    label=r"$M_{1%s}$ (m$^{-2}$/s)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_M1)

_M2par = GkQuantity(
    name="M2par", source=[["M2par"], ["M0M1M2parM2perp"], ["M2", "M2perp"]],
    fetch_func=[ff.fetch_s0c0, ff.fetch_s0c2, ff.fetch_s0c0_sub_s1c0],
    label=r"$M_{2\parallel%s}$ (m$^{-1}$/s$^2$)", is_time_dep=True,
    is_species_dep=True)
gk_quant_registry.register(_M2par)

_M2perp = GkQuantity(
    name="M2perp", source=[["M2perp"], ["M0M1M2parM2perp"], ["M2", "M2par"]],
    fetch_func=[ff.fetch_s0c0, ff.fetch_s0c3, ff.fetch_s0c0_sub_s1c0],
    label=r"$M_{2\perp%s}$ (m$^{-1}$/s$^2$)", is_time_dep=True,
    is_species_dep=True)
gk_quant_registry.register(_M2perp)

_M2 = GkQuantity(
    name="M2",
    source=[["M2"], ["M0M1M2"], ["M0M1M2parM2perp"], [_M2par, _M2perp]],
    fetch_func=[ff.fetch_s0c0, ff.fetch_s0c2, ff.fetch_s0c2_add_s0c3,
        ff.fetch_s0c0_add_s1c0],
    label=r"$M_{2%s}$ (m$^{-1}$/s$^2$)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_M2)

_upar = GkQuantity(
    name="upar",
    source=[["MaxwellianMoments"], ["BiMaxwellianMoments"], [_M0, _M1]],
    fetch_func=[ff.fetch_s0c1, ff.fetch_s0c1, ff.fetch_s1c0_div_s0c0],
    label=r"$u_{\parallel %s}$ (m/s)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_upar)

_Tpar = GkQuantity(
    name="Tpar", source=[["BiMaxwellianMoments"], [_M0, _M1, _M2par]],
    fetch_func=[ff.fetch_Tpar_from_BiMax, ff.fetch_Tpar_from_M0_M1_M2par],
    label=r"$T_{\parallel %s}$ (J)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_Tpar)

_Tperp = GkQuantity(
    name="Tperp", source=[["BiMaxwellianMoments"], [_M0, _M2perp]],
    fetch_func=[ff.fetch_Tperp_from_BiMax, ff.fetch_Tperp_from_M0_M2perp],
    label=r"$T_{\perp %s}$ (J)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_Tperp)

# ------------------------------------------- combined plasma moments (per-sp)
_temp = GkQuantity(
    name="temp", source=[["MaxwellianMoments"], [_Tpar, _Tperp]],
    fetch_func=[ff.fetch_temp_from_Max, ff.fetch_temp_from_Tpar_Tperp],
    label=r"$T_{%s}$ (J)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_temp)

_press = GkQuantity(
    name="press",
    source=[["MaxwellianMoments"], ["BiMaxwellianMoments"], [_M0, _temp]],
    fetch_func=[ff.fetch_press_from_Max, ff.fetch_press_from_BiMax,
        ff.fetch_s0c0_mul_s1c0],
    label=r"$p_{%s}$ (Pa)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_press)

_presspar = GkQuantity(
    name="presspar", source=[[_M0, _Tpar]], fetch_func=[ff.fetch_press_p],
    label=r"$p_{\parallel %s}$ (Pa)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_presspar)

_pressperp = GkQuantity(
    name="pressperp", source=[[_M0, _Tperp]], fetch_func=[ff.fetch_press_p],
    label=r"$p_{\perp %s}$ (Pa)", is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_pressperp)

_beta = GkQuantity(
    name="beta", source=[[_geo_int_bmag, _press]],
    fetch_func=[ff.fetch_beta_from_bmag_press], label=r"$\beta_{%s}$",
    is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_beta)

# ----------------------------------------------------------- drift speeds
_ExB_vel = GkQuantity(
    name="ExB_vel",
    source=[[_geo_int_jacobtot_inv, _geo_int_bmag, _geo_int_b_i, _field]],
    fetch_func=[ff.fetch_ExB_vel], label=r"$v_{E,%s}$ (m/s)",
    is_time_dep=True, is_vector=True)
gk_quant_registry.register(_ExB_vel)

_gradB_vel = GkQuantity(
    name="gradB_vel",
    source=[[_geo_int_jacobtot_inv, _geo_int_bmag, _geo_int_b_i, _Tperp]],
    fetch_func=[ff.fetch_gradB_vel], label=r"$v_{\nabla B,%s}$ (m/s)",
    is_time_dep=True, is_species_dep=True, is_vector=True)
gk_quant_registry.register(_gradB_vel)

_diamag_vel = GkQuantity(
    name="diamag_vel",
    source=[[_geo_int_jacobtot_inv, _geo_int_bmag, _geo_int_b_i, _M0, _pressperp]],
    fetch_func=[ff.fetch_diamag_vel], label=r"$v_{dia,%s}$ (m/s)",
    is_time_dep=True, is_species_dep=True, is_vector=True)
gk_quant_registry.register(_diamag_vel)

# ------------------------------------------------------------- phase space
_distf = GkQuantity(
    name="distf", source=[[""]], fetch_func=[ff.load_distf], label=r"$f_{%s}$",
    is_time_dep=True, is_species_dep=True)
gk_quant_registry.register(_distf)
