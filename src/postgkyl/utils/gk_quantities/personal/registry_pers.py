## You can add your personnal quantities below.

from ..gkquantity import GkQuantity
from ..registry import (
  gk_quant_registry,
  _geo_int_bmag,
  _M0,
  _field,
  _temp,
  _vt,
  _qpar,
  _qperp,
  _qpar_fluid,
  _qperp_fluid,
)
from . import fetch_funcs_pers as ff

# -----------------------------
# --- Normalized quantities ---
# -----------------------------

# Square of electron larmor radius over Debye length.
_rho_e_over_lambda_d_sq : GkQuantity = GkQuantity(
  name = "rho_e_over_lambda_d_sq",
  source = [[_geo_int_bmag, _M0],],
  fetch_func = [ff.fetch_rho_e_over_lambda_d_sq],
  label = r"$(\rho_e/\lambda_d)^2$",
  is_time_dep = True,
  is_species_dep = False,
)
gk_quant_registry.register(_rho_e_over_lambda_d_sq)

# Normalized elctrostatic potential.
_phi_norm : GkQuantity = GkQuantity(
  name = "phi_norm",
  source = [[_field, _temp],],
  fetch_func = [ff.fetch_phi_norm],
  label = r"$e\phi/T_{%s}$",
  is_time_dep = True,
  is_species_dep = False,
)
gk_quant_registry.register(_phi_norm)

# Normalized parallel heatflux.
_qpar_norm : GkQuantity = GkQuantity(
  name = "qpar_norm",
  source = [[_qpar, _M0, _temp, _vt],],
  fetch_func = [ff.fetch_qpar_norm],
  label = r"$q_{\parallel %s}/(n T v_{th})$",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_qpar_norm)

# Normalized perpendicular heatflux.
_qperp_norm : GkQuantity = GkQuantity(
  name = "qperp_norm",
  source = [[_qperp, _M0, _temp, _vt],],
  fetch_func = [ff.fetch_qperp_norm],
  label = r"$q_{\perp %s}/(n T v_{th})$",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_qperp_norm)

# Normalized parallel fluid-frame heatflux.
_qpar_fluid_norm : GkQuantity = GkQuantity(
  name = "qpar_fluid_norm",
  source = [[_qpar_fluid, _M0, _temp, _vt],],
  fetch_func = [ff.fetch_qpar_norm],
  label = r"$q_{\parallel %s}^{fluid}/(n T v_{t})$",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_qpar_fluid_norm)

# Normalized perpendicular fluid-frame heatflux.
_qperp_fluid_norm : GkQuantity = GkQuantity(
  name = "qperp_fluid_norm",
  source = [[_qperp_fluid, _M0, _temp, _vt],],
  fetch_func = [ff.fetch_qperp_norm],
  label = r"$q_{\perp %s}^{fluid}/(n T v_{t})$",
  is_time_dep = True,
  is_species_dep = True,
)
gk_quant_registry.register(_qperp_fluid_norm)