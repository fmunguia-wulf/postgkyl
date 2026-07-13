"""Gyrokinetic derived-quantity physics — the ``fetch_*`` functions behind the
quantity registry.

Ported from ``src_bak/postgkyl/gk/gk_quantities/fetch_funcs.py``. Every
``fetch_*`` there computed through ``GkeyllDGops`` -- a ``ctypes`` binding
that is dead in this tree (rule #2). Rewired here onto the new surface:
every fetch function **interpolates its inputs first**
(:meth:`~postgkyl.api.gdata.GData.interpolate`, the sanctioned "evaluation"
bridge -- REFACTOR_GKEYLL_FFI.md's field domain) and then computes with
plain NumPy on the interpolated values, exactly like every sibling equation
module (``five_moment``, ``ten_moment``, ``mhd``, ...). This is a deliberate
divergence from a literal "stay modal and call the weak kernels" port:
extracting one physical field's coefficients out of a *packed* multi-field
source file (``M0M1M2``, ``BiMaxwellianMoments``, ``HamiltonianMoments``, ...)
has no primitive reachable from this layer's allowed imports (``core``,
``ops``, ``numerics``, ``api`` -- not ``dg``/``gpython``; only ``ops.select``
could slice a component, and it unconditionally refuses gkyl-backed data).
Interpolating first sidesteps that gap entirely and matches the one
established working pattern in this codebase; see the layer-12 report for
the full trade-off discussion. Physical constants come from
``scipy.constants`` (rule #13), not a re-typed ``gk/gkeyll_const.py`` table.

Naming keys (matching ``src_bak`` so the registry mapping in ``registry.py``
stays recognizable):
  s#: source #, c#: component #, add/sub/mul/div: the combining operator,
  pos/neg: the plus/minus term of a curvilinear cross product.
"""

from __future__ import annotations

import operator
from typing import TYPE_CHECKING

import numpy as np
from scipy import constants

from postgkyl import ops

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def _get_ctx_val(gdata: "GDataState", key: str, **kwargs):
  """``gdata.ctx[key]``, falling back to ``kwargs[key]``, else raise."""
  if key in gdata.ctx:
    return gdata.ctx[key]
  # end
  if key in kwargs:
    return kwargs[key]
  # end
  raise KeyError(
      f"fetch function: context key '{key}' not found in the dataset; "
      f"pass it as an extra keyword argument (e.g. {key}=<value>).")
# end


def _ensure_interpolated(d: "GDataState") -> "GDataState":
  """Interpolate ``d`` onto the field domain unless it already is.

  Uses the ``ops.interpolate`` verb directly (rather than the fluent
  ``GData.interpolate()``) so this works on any ``GDataState``, not just the
  fluent subclass -- these functions receive whatever
  ``GkQuantity.get_src_gdata`` hands them.
  """
  if d.ctx.get("interpolated"):
    return d
  # end
  return ops.interpolate(d)
# end


def _component(d: "GDataState", comp: int | None) -> "GDataState":
  """Interpolate ``d`` and select physical component ``comp`` (all if None)."""
  interpolated = _ensure_interpolated(d)
  return interpolated if comp is None else ops.select(interpolated, comp=comp)
# end


# --------------------------------------------------- generic fetch factories
def _make_fetch_comp(icomp: int | None):
  """A fetch function that extracts the ``icomp``-th physical component."""
  def fetch(gdatas, **kwargs):
    return _component(gdatas[0], icomp)
  # end
  fetch.__name__ = f"fetch_comp{icomp}" if icomp is not None else "fetch_compAll"
  return fetch
# end


def _make_fetch_binop(si: int, ci: int, sj: int, cj: int, op):
  """A fetch function combining component ``ci`` of source ``si`` with
  component ``cj`` of source ``sj`` via ``op`` (both interpolated first)."""
  def fetch(gdatas, **kwargs):
    a = _component(gdatas[si], ci)
    b = _component(gdatas[sj], cj)
    return a._result(a.grid, op(a.values, b.values))
  # end
  fetch.__name__ = f"fetch_s{si}c{ci}_{op.__name__}_s{sj}c{cj}"
  return fetch
# end


# Extract a single component.
fetch_s0cAll = _make_fetch_comp(None)
fetch_s0c0 = _make_fetch_comp(0)
fetch_s0c1 = _make_fetch_comp(1)
fetch_s0c2 = _make_fetch_comp(2)
fetch_s0c3 = _make_fetch_comp(3)

# Combine components across (possibly different) sources.
fetch_s0c0_add_s1c0 = _make_fetch_binop(0, 0, 1, 0, operator.add)
fetch_s0c2_add_s0c3 = _make_fetch_binop(0, 2, 0, 3, operator.add)
fetch_s0c0_sub_s1c0 = _make_fetch_binop(0, 0, 1, 0, operator.sub)
fetch_s0c0_mul_s1c0 = _make_fetch_binop(0, 0, 1, 0, operator.mul)
fetch_s0c0_mul_s0c1 = _make_fetch_binop(0, 0, 0, 1, operator.mul)
fetch_s1c0_div_s0c0 = _make_fetch_binop(1, 0, 0, 0, operator.truediv)


# ------------------------------------------------------------------ moments
def fetch_M1_from_H(gdatas, **kwargs):
  """M1 from the Hamiltonian moments: ``mass**-1 * (comp0 * comp1)``."""
  hmom = _ensure_interpolated(gdatas[0])
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  values = hmom.values[..., 0, np.newaxis] * hmom.values[..., 1, np.newaxis]
  return hmom._result(hmom.grid, values / mass)
# end


def fetch_Tpar_from_BiMax(gdatas, **kwargs):
  """Tpar from BiMaxwellian moments: ``mass * comp2``."""
  Tpar = fetch_s0c2(gdatas)
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  return Tpar._result(Tpar.grid, mass * Tpar.values)
# end


def fetch_Tpar_from_M0_M1_M2par(gdatas, **kwargs):
  """``upar*M1 + M0*Tpar/m = M2par`` => ``Tpar = m*(M2par - upar*M1)/M0``."""
  m0, m1, m2par = (_ensure_interpolated(g) for g in gdatas)
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  upar = m1.values / m0.values
  values = mass * (m2par.values - upar * m1.values) / m0.values
  return m0._result(m0.grid, values)
# end


def fetch_Tperp_from_BiMax(gdatas, **kwargs):
  """Tperp from BiMaxwellian moments: ``mass * comp3``."""
  Tperp = fetch_s0c3(gdatas)
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  return Tperp._result(Tperp.grid, mass * Tperp.values)
# end


def fetch_Tperp_from_M0_M2perp(gdatas, **kwargs):
  """``Tperp = 0.5 * mass * (M2perp / M0)``."""
  Tperp = fetch_s1c0_div_s0c0(gdatas)
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  return Tperp._result(Tperp.grid, 0.5 * mass * Tperp.values)
# end


def fetch_temp_from_Max(gdatas, **kwargs):
  """temp from Maxwellian moments: ``mass * comp2``."""
  temp = fetch_s0c2(gdatas)
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  return temp._result(temp.grid, mass * temp.values)
# end


def fetch_temp_from_Tpar_Tperp(gdatas, **kwargs):
  """``temp = (Tpar + 2*Tperp) / 3``."""
  Tpar, Tperp = (_ensure_interpolated(g) for g in gdatas)
  values = (Tpar.values + 2.0 * Tperp.values) / 3.0
  return Tpar._result(Tpar.grid, values)
# end


def fetch_press_from_Max(gdatas, **kwargs):
  """Pressure from Maxwellian moments: ``press = mass * comp0 * comp2``."""
  maxmom = _ensure_interpolated(gdatas[0])
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  values = mass * maxmom.values[..., 0, np.newaxis] * maxmom.values[..., 2, np.newaxis]
  return maxmom._result(maxmom.grid, values)
# end


def fetch_press_from_BiMax(gdatas, **kwargs):
  """Pressure from BiMaxwellian moments: ``press = comp0 * mass*(Tpar+2Tperp)/3``."""
  bimax = _ensure_interpolated(gdatas[0])
  mass = _get_ctx_val(gdatas[0], "mass", **kwargs)
  Tpar_vals = bimax.values[..., 2, np.newaxis]
  Tperp_vals = bimax.values[..., 3, np.newaxis]
  temp_vals = mass * (Tpar_vals + 2.0 * Tperp_vals) / 3.0
  values = bimax.values[..., 0, np.newaxis] * temp_vals
  return bimax._result(bimax.grid, values)
# end


def fetch_press_p(gdatas, **kwargs):
  """Perpendicular/parallel pressure in J/m^3: ``p_p = n * T_p``."""
  m0, Tp = (_ensure_interpolated(g) for g in gdatas)
  return m0._result(m0.grid, m0.values * Tp.values)
# end


def fetch_beta_from_bmag_press(gdatas, **kwargs):
  """``beta = 2*mu_0*press / bmag**2``."""
  bmag, press = (_ensure_interpolated(g) for g in gdatas)
  values = 2.0 * constants.mu_0 * press.values / bmag.values ** 2
  return bmag._result(bmag.grid, values)
# end


# ------------------------------------------------------------ drift speeds
def _b_cross_grad_div_b_component(scalar: "GDataState", jacobtot_inv: "GDataState",
    b_i: "GDataState", comp: int) -> "GDataState":
  """The ``comp``-th component of ``b x grad(f) / (J B)``.

  ``(b x grad f)_k / B = epsilon_{ijk} * b_i * d(f)/dx^j / (J B)``, where
  ``epsilon_{ijk}`` is the Levi-Civita tensor, ``f`` a scalar field, ``b_i``
  the covariant components of a vector field. The gradient is the numerical
  (post-``interpolate()``) one (``ops.differentiate``); see
  ``differentiate-decision.md`` -- an exact modal derivative needs a shim
  addition out of scope for this layer.

  Args:
    scalar: Scalar field ``f`` to differentiate; interpolated internally.
    jacobtot_inv: Inverse of the total-coordinate-transformation Jacobian.
    b_i: Covariant components of the unit vector field ``b``.
    comp: 0-based component ``k`` of the cross product (``< 3``).

  Raises:
    KeyError: if ``comp`` is not 0, 1, or 2.
  """
  f = _ensure_interpolated(scalar)
  cdim = f.num_dims

  diff_dir_pos = bi_c_pos = 0
  diff_dir_neg = bi_c_neg = 0
  calc_term = [True, True]
  if comp == 0:
    diff_dir_neg = bi_c_pos = 1
    diff_dir_pos = bi_c_neg = cdim - 1
    if cdim < 3:
      calc_term = [True, False]
  # end
    # end
  elif comp == 1:
    bi_c_pos, bi_c_neg = 2, 0
    diff_dir_neg, diff_dir_pos = cdim - 1, 0
    if cdim == 1:
      calc_term = [False, True]
  # end
    # end
  elif comp == 2:
    diff_dir_neg = bi_c_pos = 0
    diff_dir_pos = bi_c_neg = 1
    if cdim == 1:
      calc_term = [False, False]
    # end
    elif cdim == 2:
      calc_term = [False, True]
  # end
    # end
  else:
    raise KeyError("comp must be 0, 1, or 2.")
  # end

  b_i_i = _ensure_interpolated(b_i)
  jacobtot_inv_i = _ensure_interpolated(jacobtot_inv)

  pos_term = np.zeros_like(f.values)
  neg_term = np.zeros_like(f.values)
  if calc_term[0]:
    d_pos = ops.differentiate(f, direction=diff_dir_pos)
    pos_term = d_pos.values * b_i_i.values[..., bi_c_pos, np.newaxis]
  # end
  if calc_term[1]:
    d_neg = ops.differentiate(f, direction=diff_dir_neg)
    neg_term = -d_neg.values * b_i_i.values[..., bi_c_neg, np.newaxis]
  # end

  values = (pos_term + neg_term) * jacobtot_inv_i.values
  return f._result(f.grid, values)
# end


def fetch_ExB_vel(gdatas, **kwargs):
  """``v_{E,k} = epsilon_{ijk}/(J B) * b_i * d(phi)/dx^j`` (``dir`` selects k).

  ``gdatas``: ``(jacobtot_inv, bmag, b_i, phi)``.
  """
  if "dir" not in kwargs:
    raise KeyError("fetch_ExB_vel: select the k-th component with dir=<int>.")
  # end
  jacobtot_inv, _bmag, b_i, phi = gdatas
  return _b_cross_grad_div_b_component(phi, jacobtot_inv, b_i, kwargs["dir"])
# end


def fetch_gradB_vel(gdatas, **kwargs):
  """``v_gradB,k = Tperp/(q B) * epsilon_{ijk} * b_i * d(B)/dx^j / (J B)``.

  ``gdatas``: ``(jacobtot_inv, bmag, b_i, Tperp)``.
  """
  if "dir" not in kwargs:
    raise KeyError("fetch_gradB_vel: select the k-th component with dir=<int>.")
  # end
  jacobtot_inv, bmag, b_i, Tperp = gdatas
  out = _b_cross_grad_div_b_component(bmag, jacobtot_inv, b_i, kwargs["dir"])
  bmag_i = _ensure_interpolated(bmag)
  Tperp_i = _ensure_interpolated(Tperp)
  charge = _get_ctx_val(Tperp, "charge", **kwargs)
  values = out.values * Tperp_i.values / bmag_i.values / charge
  return out._result(out.grid, values)
# end


def fetch_diamag_vel(gdatas, **kwargs):
  """``v_diamag,k = 1/(q n) epsilon_{ijk} b_i * d(pperp)/dx^j / (J B)``.

  ``gdatas``: ``(jacobtot_inv, bmag, b_i, m0, pressperp)``.
  """
  if "dir" not in kwargs:
    raise KeyError("fetch_diamag_vel: select the k-th component with dir=<int>.")
  # end
  jacobtot_inv, bmag, b_i, m0, pressperp = gdatas
  out = _b_cross_grad_div_b_component(pressperp, jacobtot_inv, b_i, kwargs["dir"])
  m0_i = _ensure_interpolated(m0)
  charge = _get_ctx_val(pressperp, "charge", **kwargs)
  values = out.values / m0_i.values / charge
  return out._result(out.grid, values)
# end


# --------------------------------------------------------- phase space (f)
def load_distf(gdatas, **kwargs):
  """Loader for the registry ``distf`` quantity: wraps
  :func:`~postgkyl.diagnostics.gyrokinetics.distf.load_gk_distf` with
  defaults tailored to registry use (never interpolate further, convert
  velocity coordinates by default). Extra keyword overrides (via
  ``**extra`` on :func:`~postgkyl.diagnostics.gyrokinetics.load_quantity.
  load_gk_quantity`): ``suffix``, ``c2p_vel``, ``mc2nu``, ``mapc2p``,
  ``block``.
  """
  from .distf import load_gk_distf
  from .utils import dict_get_bool

  prefix = kwargs.get("path", "").rstrip("/") + "/" + kwargs.get("name", "")
  extra = {k: v for k, v in kwargs.items()
           if k not in ("path", "name", "species", "frame")}

  return load_gk_distf(
      name=prefix, species=kwargs.get("species", ""),
      frame=int(kwargs.get("frame", 0)),
      suffix=str(extra.get("suffix", "")),
      use_c2p_vel=dict_get_bool(extra, "c2p_vel", True),
      use_mc2nu=dict_get_bool(extra, "mc2nu", False),
      use_mapc2p=dict_get_bool(extra, "mapc2p", False),
      block_idx=extra.get("block", None),
      num_interp=0,
  )
# end
