"""
Functions for for fetching (loading and computing) quantities in the
gk_quantities registry.

Each fetch function takes a list of loaded GData objects (matching the
corresponding 'files' entry in the registry) and returns (grid, values) for
the derived quantity.

Naming keys for some fetch functions below:
  s#: source #
  c#: component #
  add: plus
  sub: minus
  mul: times
  div: divided by
  pow#: raised to the power of #

"""
import numpy as np
import operator

from postgkyl.data import GData
from postgkyl.data.dg import get_num_basis
from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops
import postgkyl.utils.gkeyll_const as gkc

def _get_ctx_val(gdata : GData, key : str, **kwargs):
  if key in gdata.ctx:
    return gdata.ctx[key]
  elif key in kwargs:
    return kwargs[key]
  else:
    raise KeyError(f"fetch function: context key '{key}' not found in GData. Pass it as '--extra {key}=<value>'.")

def _get_num_basis_from_gdata(gdata) -> int:
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

def _make_fetch_comp(icomp: int):
  """Return a fetch function that extracts the comp-th physical component."""
  def fetch(gdatas, **kw):
    g = gdatas[0].get_grid()
    nb = _get_num_basis_from_gdata(gdatas[0])
    comp = [icomp,icomp] if icomp is not None else [0,int(gdatas[0].get_num_comps()/nb)]
    v = gdatas[0].get_values()[..., comp[0]*nb:(comp[1]+1)*nb].copy()
    out = GData(ctx=gdatas[0].ctx)
    out.push(g, v)
    return out
  # end
  fetch.__name__ = f"fetch_comp{icomp}" if icomp is not None else f"fetch_compAll"
  return fetch

def _make_fetch_sick_addsub_sjcl(si: int, ck: int, sj: int, cl: int, op):
  """
  Return a fetch function that does:
    (k-th component of the i-th source) op (l-th component of the j-th source)
  """
  def fetch(gdatas, **kwargs):
    gd_l = gdatas[si]
    gd_r = gdatas[sj]

    nb_l = _get_num_basis_from_gdata(gd_l)
    nb_r = _get_num_basis_from_gdata(gd_r)
    if not nb_l == nb_r:
      raise ValueError(f"Datasets have different basis")

    vals_l = gd_l.get_values()
    vals_r = gd_r.get_values()
  
    out = GData(ctx=gdl.ctx)
    out.push(gd_l.get_grid(), op(vals_l,vals_r))
  
    return out
  # end
  fetch.__name__ = f"fetch_s{si}c{ck}_mul_s{sj}c{cl}"
  return fetch

def _make_fetch_sick_mul_sjcl(si: int, ck: int, sj: int, cl: int):
  """
  Return a fetch function that multiplies the k-th component of the i-th
  source/dataset by the l-th component of the j-th source.
  """
  def fetch(gdatas, **kwargs):
    gd_l = gdatas[si]
    gd_r = gdatas[sj]

    nb_l = _get_num_basis_from_gdata(gd_l)
    nb_r = _get_num_basis_from_gdata(gd_r)
    if not nb_l == nb_r:
      raise ValueError(f"Datasets have different basis")

    vals_l = gd_l.get_values()
    out_shape = list(vals_l.shape)
    out_shape[-1] = nb_l
  
    out = GData(ctx=gd_l.ctx)
    out.push(gd_l.get_grid(), np.zeros(out_shape, dtype=vals_l.dtype))
  
    dgops = GkeyllDGops()
    dgops.multiply(0, out, ck, gd_l, cl, gd_r)
  
    return out
  # end
  fetch.__name__ = f"fetch_s{si}c{ck}_mul_s{sj}c{cl}"
  return fetch

def _make_fetch_sick_div_sjcl(si: int, ck: int, sj: int, cl: int):
  """
  Return a fetch function that divides the k-th component of the i-th
  source/dataset by the l-th component of the j-th source.
  """
  def fetch(gdatas, **kwargs):
    gd_l = gdatas[si]
    gd_r = gdatas[sj]

    nb_l = _get_num_basis_from_gdata(gd_l)
    nb_r = _get_num_basis_from_gdata(gd_r)
    if not nb_l == nb_r:
      raise ValueError(f"Datasets have different basis")

    vals_l = gd_l.get_values()
    out_shape = list(vals_l.shape)
    out_shape[-1] = nb_l
  
    out = GData(ctx=gd_l.ctx)
    out.push(gd_l.get_grid(), np.zeros(out_shape, dtype=vals_l.dtype))

    dgops = GkeyllDGops()
    dgops.invert(0, out, cl, gd_r)
    dgops.multiply(0, out, ck, gd_l, 0, out)
  
    return out
  # end
  fetch.__name__ = f"fetch_s{si}c{ck}_div_s{sj}c{cl}"
  return fetch

def _b_cross_grad_div_B_component(scalar, jacobtot_inv, b_i, comp):
  """
  The comp-th component of the cross product b x grad(f)
    (b x grad f)_k / B = epsilon_{ijk} * b_i * d(f)/dx^j / (J B)
  where epsilon_{ijk} is the Levi-Civitta tensor, f is a scalar field
  and b_i are the covariant components of a vector field.

  Note: the 1/Jacobian factor of the curvilinear cross product is NOT
  included here and must be applied by the caller.

  Inputs:
    scalar: scalar field f to be differentiated.
    jacobtot_inv: inverse of the Jacobian of the total coordinate transformation.
    b_i:    covariant components of the vector field b.
    comp:   component k of the cross product to compute (0-index, < 3).
  """
  cdim = scalar.get_num_dims()

  # Components of the quantities in the cross product AxB.
  diff_dir_pos = bi_c_pos = 0
  diff_dir_neg = bi_c_neg = 0
  calc_term = [True,True] # Whether to compute pos and neg term in component of AxB.
  if comp == 0:
    diff_dir_neg = bi_c_pos = 1
    diff_dir_pos = bi_c_neg = cdim-1
    if cdim < 3:
      calc_term = [True,False]
    # end
  elif comp == 1:
    bi_c_pos = 2
    bi_c_neg = 0
    diff_dir_neg = cdim-1
    diff_dir_pos = 0
    if cdim == 1:
      calc_term = [False,True]
    # end
  elif comp == 2:
    diff_dir_neg = bi_c_pos = 0
    diff_dir_pos = bi_c_neg = 1
    if cdim == 1:
      calc_term = [False,False]
    elif cdim == 2:
      calc_term = [False,True]
    # end
  else:
    raise KeyError("_b_cross_grad_component: component must be >= 0 and < 3.")

  buff = _empty_gdata_from_gdata(scalar) # Positive term in AxB.
  out = _empty_gdata_from_gdata(scalar) # Negative term in AxB.

  dgops = GkeyllDGops()
  lower, upper = scalar.get_bounds()
  cells = scalar.get_num_cells()
  if calc_term[0]:
    # Compute derivatives of the scalar field.
    dx = (upper[diff_dir_pos] - lower[diff_dir_pos])/cells[diff_dir_pos]
    dgops.differentiate(diff_dir_pos, 1,  dx, 0, buff, 0, scalar)
    # Multiply by b_i.
    dgops.multiply(0, buff, bi_c_pos, b_i, 0, buff)

  if calc_term[1]:
    # Compute derivatives of the scalar field.
    dx = (upper[diff_dir_neg] - lower[diff_dir_neg])/cells[diff_dir_neg]
    dgops.differentiate(diff_dir_neg, 1, -dx, 0, out , 0, scalar)
    # Multiply by b_i.
    dgops.multiply(0, out , bi_c_neg, b_i, 0, out )

  # Add the two terms to form the comp-th component of b x grad(f).
  out.set_values(buff.get_values() + out.get_values())

  # Divide by the Jacobian factor of the curvilinear cross product.
  dgops.multiply(0, out, 0, out, 0, jacobtot_inv)

  return out

# Functions to extract a components.
fetch_s0cAll = _make_fetch_comp(None)
fetch_s0c0 = _make_fetch_comp(0)
fetch_s0c1 = _make_fetch_comp(1)
fetch_s0c2 = _make_fetch_comp(2)
fetch_s0c3 = _make_fetch_comp(3)

# Functions to add two components.
fetch_s0c0_add_s1c0 = _make_fetch_sick_addsub_sjcl(0,0,1,0,operator.add)
fetch_s0c2_add_s0c3 = _make_fetch_sick_addsub_sjcl(0,2,0,3,operator.add)

# Functions to subtract two components.
fetch_s0c0_sub_s1c0 = _make_fetch_sick_addsub_sjcl(0,0,1,0,operator.sub)

# Functions to multiply two components.
fetch_s0c0_mul_s1c0 = _make_fetch_sick_mul_sjcl(0,0,1,0)
fetch_s0c0_mul_s0c1 = _make_fetch_sick_mul_sjcl(0,0,0,1)

# Functions to divide two components.
fetch_s1c0_div_s0c0 = _make_fetch_sick_div_sjcl(1,0,0,0)

# ------------------------------------------
# --- Plasma moments (species-dependent) ---
# ------------------------------------------

def fetch_M1_from_H(gdatas, **kwargs):
  """
  M1 from the Hamiltonian moments (Hmom).
  """
  hmom = gdatas[0]
  mass = _get_ctx_val(hmom, "mass", **kwargs)
  nb = _get_num_basis_from_gdata(hmom)
  vals = hmom.get_values()

  m1 = GData(ctx=hmom.ctx)
  m1.push(hmom.get_grid(), np.zeros_like(vals[..., :nb]))

  dgops = GkeyllDGops()
  dgops.multiply(0, m1, 0, hmom, 1, hmom)

  m1.set_values(m1.get_values() / mass)
  return m1

def fetch_Tpar_from_BiMax(gdatas, **kwargs):
  """
  Tpar from BiMaxwellian moments.
  """
  Tpar = fetch_s0c2(gdatas)

  bimax = gdatas[0]
  mass = _get_ctx_val(bimax, "mass", **kwargs)
  Tpar.set_values(mass * Tpar.get_values())
  return Tpar

def fetch_Tpar_from_M0_M1_M2par(gdatas, **kwargs):
  """
  upar*M1 + M0*Tpar/m = M2par.
  Tpar = m * (M2par - upar*M1) / M0.
  """
  m0, m1, m2par = gdatas
  dgops = GkeyllDGops()

  m0_inv = _empty_gdata_from_gdata(m0)
  upar   = _empty_gdata_from_gdata(m0)
  Tpar   = _empty_gdata_from_gdata(m0)

  dgops.invert(0, m0_inv, 0, m0)
  dgops.multiply(0, upar, 0, m1, 0, m0_inv)
  dgops.multiply(0, upar, 0, upar, 0, m1)

  m2par_val = m2par.get_values()
  um1_val = upar.get_values()
  
  mass = _get_ctx_val(m0, "mass", **kwargs)
  Tpar.set_values(mass * (m2par_val - um1_val))
  dgops.multiply(0, Tpar, 0, Tpar, 0, m0_inv)
  return Tpar

def fetch_Tperp_from_BiMax(gdatas, **kwargs):
  """
  Tperp from BiMaxwellian moments.
  """
  Tperp = fetch_s0c3(gdatas)

  bimax = gdatas[0]
  mass = _get_ctx_val(bimax, "mass", **kwargs)
  Tperp.set_values(mass * Tperp.get_values())
  return Tperp

def fetch_Tperp_from_M0_M2perp(gdatas, **kwargs):
  """
  Tperp = 0.5 * mass * (M2perp / M0).
  """
  Tperp = fetch_s1c0_div_s0c0(gdatas)

  m0 = gdatas[0]
  mass = _get_ctx_val(m0, "mass", **kwargs)
  Tperp.set_values(0.5 * mass * Tperp.get_values())
  return Tperp

def fetch_temp_from_Max(gdatas, **kwargs):
  """
  temp from Maxwellian moments.
  """
  temp = fetch_s0c2(gdatas)

  maxmom = gdatas[0]
  mass = _get_ctx_val(maxmom, "mass", **kwargs)
  temp.set_values(mass * temp.get_values())
  return temp

def fetch_temp_from_Tpar_Tperp(gdatas, **kwargs):
  """
  temp = (Tpar + 2*Tperp) / 3.
  """
  Tpar, Tperp = gdatas

  temp = _empty_gdata_from_gdata(Tpar)

  Tpar_val  = Tpar.get_values()
  Tperp_val = Tperp.get_values()
  
  temp.set_values((Tpar_val + 2.0*Tperp_val)/3.0)
  return temp

# ---------------------------------------------------
# --- Combined plasma moments (species-dependent) ---
# ---------------------------------------------------

def fetch_press_from_Max(gdatas, **kwargs):
  """
  Pressure from Maxwellian moments.
  press = den * temp.
  """
  maxmom = gdatas[0]
  nb = _get_num_basis_from_gdata(maxmom)
  vals = maxmom.get_values()[..., :nb]
  
  press = GData(ctx=maxmom.ctx)
  press.push(maxmom.get_grid(), np.zeros_like(vals))

  dgops = GkeyllDGops()
  dgops.multiply(0, press, 0, maxmom, 2, maxmom)

  mass = _get_ctx_val(maxmom, "mass", **kwargs)
  press.set_values(mass * press.get_values())
  return press

def fetch_press_from_BiMax(gdatas, **kwargs):
  """
  Pressure from BiMaxwellian moments.
  press = den * (Tpar + 2*Tperp) / 3.
  """
  bimax = gdatas[0]
  nb = _get_num_basis_from_gdata(bimax)
  vals = bimax.get_values()

  mass = _get_ctx_val(bimax, "mass", **kwargs)
  Tpar_vals  = vals[..., 2*nb:3*nb]
  Tperp_vals = vals[..., 3*nb:4*nb]
  temp_vals  = mass*(Tpar_vals + 2.0 * Tperp_vals)/3.0

  press = GData(ctx=bimax.ctx)
  press.push(bimax.get_grid(), temp_vals.copy())

  dgops = GkeyllDGops()
  dgops.multiply(0, press, 0, bimax, 0, press)

  return press

def fetch_press_p(gdatas, **kwargs):
  """
  Perpendicular/parallel pressure in J/m^3.
  p_p = n * T_p.
  """
  m0 = gdatas[0]
  Tp = gdatas[1]
  
  dgops = GkeyllDGops()
  press_p = _empty_gdata_from_gdata(m0)
  dgops.multiply(0, press_p, 0, m0, 0, Tp)

  return press_p

def fetch_beta_from_bmag_press(gdatas, **kwargs):
  """
  beta = 2*mu_0*press/bmag^2
  """
  bmag, press = gdatas

  dgops = GkeyllDGops()

  bmag_sq = _empty_gdata_from_gdata(bmag)
  out = _empty_gdata_from_gdata(bmag)

  dgops.multiply(0, bmag_sq, 0, bmag, 0, bmag)

  dgops.invert(0, out, 0, bmag_sq)
  dgops.multiply(0, out, 0, press, 0, out)

  out_val = out.get_values()
  
  mu0 = gkc.GKYL_MU0
  out.set_values(2.0*mu0*out_val)
  return out

# ------------------------
# --- Drift velocities ---
# ------------------------

def fetch_ExB_vel(gdatas, **kwargs):
  """
  A component of the ExB drift velocity
    v_{E,k} = epsilon_{ijk}/(J B) * b_i * d(phi)/dx^j
  where epsilon_{ijk} is the Levi-Civitta tensor
  and gdatas has (in this order):
    1/(J*B): jacobtot_inv.
    b_i: covariant components of the magnetic field unit vector.
    phi: electrostatic potential.

  The k-th component is selected by the 'dir' optional argument.
  """
  if "dir" not in kwargs:
    raise KeyError("fetch_ExB_vel: select the j-th component with '--extra dir=j' (0-index).")

  jacobtot_inv = gdatas[0]
  bmag = gdatas[1]
  b_i = gdatas[2]
  phi = gdatas[3]

  # k-th component of b x grad(phi)/B.
  out = _b_cross_grad_div_B_component(phi, jacobtot_inv, b_i, kwargs["dir"])

  return out

def fetch_gradB_vel(gdatas, **kwargs):
  """
  A component of the grad-B drift velocity
    v_gradB,k = Tperp/(q B) * epsilon_{ijk} * b_i * d(B)/dx^j / (J B)
  where epsilon_{ijk} is the Levi-Civitta tensor, q the species charge,
  and gdatas has (in this order):
    1/(J*B): inv. total Jacobian (jacobtot_inv).
    B: magnetic field magnitude (bmag).
    b_i: covariant components of the magnetic field unit vector.
    Tperp: perpendicular temperature (in Joules).

  The k-th component is selected by the 'dir' optional argument.
  """
  if "dir" not in kwargs:
    raise KeyError("fetch_gradB_vel: select the j-th component with '--extra dir=j' (0-index).")

  jacobtot_inv = gdatas[0]
  bmag = gdatas[1]
  b_i = gdatas[2]
  Tperp = gdatas[3]

  # k-th component of b x grad(B)/B.
  out = _b_cross_grad_div_B_component(bmag, jacobtot_inv, b_i, kwargs["dir"])

  dgops = GkeyllDGops()
  # Multiply by Tperp.
  dgops.multiply(0, out, 0, Tperp, 0, out)

  # Divide by B.
  denom_inv = _empty_gdata_from_gdata(bmag)
  dgops.invert(0, denom_inv, 0, bmag)
  dgops.multiply(0, out, 0, out, 0, denom_inv)

  # Divide by the species charge.
  charge = _get_ctx_val(Tperp, "charge", **kwargs)
  out.set_values(out.get_values()/charge)

  return out

def fetch_diamag_vel(gdatas, **kwargs):
  """
  A component of the diamagnetic drift velocity
    v_diamag,k = 1 / (q n) epsilon_{ijk} b_i * d(pperp)/dx^j / (J B)
  where epsilon_{ijk} is the Levi-Civitta tensor, q the species charge,
  and gdatas has (in this order):
    1/(J*B): inv. total Jacobian (jacobtot_inv).
    B: magnetic field magnitude (bmag).
    b_i: covariant components of the magnetic field unit vector.
    m0: zeroth moment (density).
    p_perp: perpendicular pressure (in Joules/m^3).
  The k-th component is selected by the 'dir' optional argument.
  """
  if "dir" not in kwargs:
    raise KeyError("fetch_diamag_vel: select the j-th component with '--extra dir=j' (0-index).")

  jacobtot_inv = gdatas[0]
  bmag = gdatas[1]
  b_i = gdatas[2]
  m0 = gdatas[3]
  pressperp = gdatas[4]

  # k-th component of b x grad(p) / B.
  out = _b_cross_grad_div_B_component(pressperp, jacobtot_inv, b_i, kwargs["dir"])

  dgops = GkeyllDGops()
  # Divide by n
  denom_inv = _empty_gdata_from_gdata(bmag)
  dgops.invert(0, denom_inv, 0, m0)
  dgops.multiply(0, out, 0, out, 0, denom_inv)

  # Divide by the species charge.
  charge = _get_ctx_val(pressperp, "charge", **kwargs)
  out.set_values(out.get_values()/charge)

  return out

# -------------------------------------------------------------------------
# --- Custom loaders (loader_func signature: path, name, species, frame) ---
# -------------------------------------------------------------------------

def load_distf(path: str, name: str, species: str, frame: int, **extra) -> GData:
  """
  Loader for the registry 'distf' quantity. Wraps load_gk_distf with defaults
  tailored to registry use: never interpolate (interp=0) and convert velocity
  coordinates (c2p_vel) on by default.

  Defaults can be overridden via --extra, e.g.:
    -e suffix=source      use <name>-<species>_source_<frame>.gkyl as input
    -e c2p_vel=0          disable velocity-space mapping
    -e mc2nu=1            apply non-uniform -> field-aligned position mapping
    -e mapc2p=1           apply position-space -> Cartesian/cylindrical mapping
    -e block=2            load only the 2nd block of a multi-block file
  """
  from postgkyl.commands.gk_distf import load_gk_distf
  from postgkyl.utils.gk_utils import dict_get_bool

  prefix = path.rstrip("/") + "/" + name

  return load_gk_distf(
    name=prefix, species=species, frame=int(frame),
    suffix=str(extra.get("suffix", "")),
    use_c2p_vel=dict_get_bool(extra, "c2p_vel", True),
    use_mc2nu=dict_get_bool(extra, "mc2nu", False),
    use_mapc2p=dict_get_bool(extra, "mapc2p", False),
    block_idx=extra.get("block", None),
    interp=0,  # registry distf always works with non-interpolated DG data
  )