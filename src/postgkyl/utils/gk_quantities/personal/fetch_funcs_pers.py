import postgkyl.utils.gkeyll_const as gkc
from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops
from postgkyl.utils.gk_quantities.fetch_funcs import _empty_gdata_from_gdata

## Add your personnal fetch functions below.# Fetch functions for personnal quantities

def _make_fetch_q_norm(name: str):
  """
  Return a fetch function for a heat flux normalized by the free-streaming
  estimate n*T*c_s:
    q_norm = q / (n*T*c_s).
  gdatas has (in this order):
    1. q: the heat flux to normalize (in W/m^2).
    2. M0: zeroth moment (density).
    3. temp: temperature (in Joules).
    4. c_s: sound speed (in m/s).
  """
  def fetch(gdatas, **kwargs):
    q, m0, temp, c_s = gdatas

    dgops = GkeyllDGops()

    # n*T*c_s.
    denom = _empty_gdata_from_gdata(m0)
    dgops.multiply(0, denom, 0, m0, 0, temp)
    dgops.multiply(0, denom, 0, denom, 0, c_s)

    denom_inv = _empty_gdata_from_gdata(m0)
    dgops.invert(0, denom_inv, 0, denom)

    out = _empty_gdata_from_gdata(m0)
    dgops.multiply(0, out, 0, q, 0, denom_inv)
    return out

  fetch.__name__ = f"fetch_q{name}_norm"
  return fetch

fetch_qpar_norm = _make_fetch_q_norm("par")
fetch_qperp_norm = _make_fetch_q_norm("perp")


def fetch_rho_e_over_lambda_d_sq(gdatas, **kwargs):
  """
  Electron larmor radius over Debye length, gamma parameter in GYRAZE (see eq. 9 of https://arxiv.org/2508.09067).
  (rho_e/lambda_d)^2 = 1/B^2 (m_e n_e/ eps0). Gdatas has:
    1. Bmag: magnetic field magnitude (bmag).
    2. M0: zeroth moment (density).
  We output the square of the quantity to avoid the square root operation.
  """
  bmag, m0 = gdatas
  me = gkc.GKYL_ELECTRON_MASS
  eps0 = gkc.GKYL_EPSILON0

  dgops = GkeyllDGops()

  bmag_sq = _empty_gdata_from_gdata(bmag)
  dgops.multiply(0, bmag_sq, 0, bmag, 0, bmag)

  bmag_inv_sq = _empty_gdata_from_gdata(bmag)
  dgops.invert(0, bmag_inv_sq, 0, bmag_sq)

  out = _empty_gdata_from_gdata(bmag)
  dgops.multiply(0, out, 0, bmag_inv_sq, 0, m0)

  out.set_values(out.get_values() * me / eps0)

  return out

def fetch_phi_norm(gdatas, **kwargs):
  """
  Normalized electrostatic potential.
  phi_norm = e*phi/T_e. Gdatas has:
    1. phi: electrostatic potential (phi).
    2. temp: temperature (temp).
  """
  phi, temp = gdatas
  e = gkc.GKYL_ELEMENTARY_CHARGE

  dgops = GkeyllDGops()

  temp_inv = _empty_gdata_from_gdata(temp)
  dgops.invert(0, temp_inv, 0, temp)

  out = _empty_gdata_from_gdata(phi)
  dgops.multiply(0, out, 0, phi, 0, temp_inv)

  out.set_values(out.get_values() * e)

  return out
