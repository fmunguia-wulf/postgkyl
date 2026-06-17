"""
Functions for for fetching (loading and computing) quantities in the
gk_quantities registry.

Each fetch function takes a list of loaded GData objects (matching the
corresponding 'files' entry in the registry) and returns (grid, values) for
the derived quantity.
"""
import numpy as np

from postgkyl.data import GData
from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops

def get_num_basis_from_gdata(gdata) -> int:
  from postgkyl.data.dg import get_num_basis
  ndim = gdata.get_num_dims()
  poly_order = int(gdata.ctx["poly_order"])
  basis_type = gdata.ctx["basis_type"]
  return get_num_basis(ndim, poly_order, basis_type)

def _empty_gdata_from_gdata(gdata) -> GData:
  """Allocate a zero-valued GData with the same grid/ctx as gdata."""
  out = GData(ctx=gdata.ctx)
  out.push(gdata.get_grid(), np.zeros_like(gdata.get_values()))
  return out

def _make_fetch_comp(comp: int):
  """Return a fetch function that extracts the comp-th physical component."""
  def fetch(gdatas, **kw):
    g = gdatas[0].get_grid()
    nb = get_num_basis_from_gdata(gdatas[0])
    v = gdatas[0].get_values()[..., comp*nb:(comp+1)*nb].copy()
    out = _empty_gdata_from_gdata(gdatas[0])
    out.push(g, v)
    return out
  # end
  fetch.__name__ = f"fetch_comp{comp}"
  return fetch

# Functions to extract specific components.
fetch_comp0 = _make_fetch_comp(0)
fetch_comp1 = _make_fetch_comp(1)
fetch_comp2 = _make_fetch_comp(2)
fetch_comp3 = _make_fetch_comp(3)

def fetch_upar_from_M0M1(gdatas):
  """
    Parallel drift speed upar = M1 / M0.
    gdatas = [M0, M1].
  """
  M0, M1 = gdatas
  dgops = GkeyllDGops()

  M0_inv = _empty_gdata_from_gdata(M0)
  upar   = _empty_gdata_from_gdata(M0)

  dgops.invert(0, M0_inv, 0, M0)
  dgops.multiply(0, upar, 0, M1, 0, M0_inv)

  return upar

def fetch_press_from_maxwellian(gdatas):
  """
    Pressure p = n * T.
    gdatas = [n, upar, temp].
  """
  bimax = gdatas[0]
  nb = get_num_basis_from_gdata(bimax)
  vals = bimax.get_values()

  # Build intermediate GData objects for n and T_combo
  press = GData(ctx=bimax.ctx)
  press.push(bimax.get_grid(), np.zeros_like(vals[..., :nb]))

  dgops = GkeyllDGops()
  dgops.multiply(0, press, 0, bimax, 2, bimax)

  return press

def fetch_press_from_bimaxwellian(gdatas):
  """
    Pressure p = n * (Tpar + 2*Tperp) / 3.
    gdatas = [n, upar, Tpar, Tperp].
  """
  bimax = gdatas[0]
  nb = get_num_basis_from_gdata(bimax)
  vals = bimax.get_values()

  Tpar_vals  = vals[..., 2*nb:3*nb]
  Tperp_vals = vals[..., 3*nb:4*nb]
  temp_vals = (Tpar + 2.0 * Tperp)/3.0

  # Build intermediate GData objects for n and T_combo
  temp = GData(ctx=gd.ctx)
  temp.push(bimax.get_grid(), temp_vals.copy())

  dgops = GkeyllDGops()
  press = _empty_gdata_from_gdata(temp)
  dgops.multiply(0, press, 0, bimax, 0, temp)

  return press
