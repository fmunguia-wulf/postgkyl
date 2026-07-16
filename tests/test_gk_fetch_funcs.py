"""Postgkyl module for testing the gk_quantities fetch functions numerically.

``test_gk_load_quantity`` drives every registered quantity end to end, but it
only asserts that a dataset comes out the other side: an algebra error in a
fetch function would pass it silently. This module closes that gap by checking
the fetch functions against a case whose moments are known in closed form, a
*shifted Maxwellian* with density n, parallel drift u and temperature T (mass m,
two perpendicular velocity dimensions)::

  M0     = n                     M2par  = n*(u^2 + T/m)
  M1     = n*u                   M2perp = n*(2T/m)
                                 M3par  = n*(u^3 + 3*u*T/m)
                                 M3perp = n*u*(2T/m)

The sharpest check available is that a Maxwellian carries *no* heat flux in the
fluid frame, so ``qpar_fluid``/``qperp_fluid`` must cancel to round-off. Because
"is zero" is also what a badly broken function returns, each vanishing check is
paired with a perturbed case that must come out nonzero and equal to a known
value.

The DG fields here are constant within each cell, which makes every weak DG
operation (multiply, invert) exact, so the expected values are matched to
near-machine precision rather than to a loose tolerance.
"""
import numpy as np
import pytest

import postgkyl.utils.gk_quantities.fetch_funcs as ff
from postgkyl.data import GData

# Synthetic DG dataset parameters: 1D, p1 serendipity (num_basis = 2).
_POLY_ORDER = 1
_BASIS_TYPE = "serendipity"
_NUM_BASIS = 2
_NUM_CELLS = 4
_NUM_DIMS = 1

# Value of the 0th (constant) modal basis function: the cell average of a DG
# field is its 0th coefficient times _PSI0.
_PSI0 = 2.0**(-0.5*_NUM_DIMS)

# Shifted-Maxwellian parameters. Deliberately not round numbers, and of
# realistic magnitude, so that a wrong formula cannot coincidentally agree.
_MASS = 3.343e-27  # Deuterium.
_DENS = 2.7e19
_UPAR = 1.3e4
_TEMP = 9.5e-18
_VT_SQ = _TEMP/_MASS  # Thermal speed squared, T/m.

# Probe whether the gkylsoft DG-operator library is available; fetch functions
# that use weak multiply/invert are skipped if it is not.
try:
  from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops
  GkeyllDGops()
  _DGOPS_AVAILABLE = True
except Exception:  # noqa: BLE001 - any failure means the lib is unusable here
  _DGOPS_AVAILABLE = False

_needs_dgops = pytest.mark.skipif(
  not _DGOPS_AVAILABLE, reason="requires the gkylsoft DG library")


def _const_gdata(comp_avgs, mass: float = _MASS) -> GData:
  """Return a DG field that is constant in space, with the given cell averages.

  ``comp_avgs`` is a scalar for a single-component field, or a sequence of one
  cell average per physical component. Only the 0th modal coefficient of each
  component is nonzero, which makes the weak DG operations exact.
  """
  avgs = np.atleast_1d(np.asarray(comp_avgs, dtype=float))
  values = np.zeros((_NUM_CELLS, _NUM_BASIS*avgs.size))
  for comp, avg in enumerate(avgs):
    values[:, comp*_NUM_BASIS] = avg/_PSI0

  gdata = GData(ctx={"poly_order": _POLY_ORDER, "basis_type": _BASIS_TYPE,
                     "mass": mass, "charge": 1.0})
  gdata.push([np.linspace(0.0, 1.0, _NUM_CELLS + 1)], values)
  return gdata


def _cell_avg(gdata: GData, comp: int = 0) -> np.ndarray:
  """Cell averages of the comp-th physical component of a DG field."""
  return gdata.get_values()[:, comp*_NUM_BASIS]*_PSI0


# Moments of the shifted Maxwellian, as single-component DG fields.
def _m0():
  return _const_gdata(_DENS)

def _m1():
  return _const_gdata(_DENS*_UPAR)

def _m2par():
  return _const_gdata(_DENS*(_UPAR**2 + _VT_SQ))

def _m2perp():
  return _const_gdata(_DENS*2.0*_VT_SQ)

def _m3par():
  return _const_gdata(_DENS*(_UPAR**3 + 3.0*_UPAR*_VT_SQ))

def _m3perp():
  return _const_gdata(_DENS*_UPAR*2.0*_VT_SQ)

def _temp():
  return _const_gdata(_TEMP)


class TestMoments:
  """Primitive quantities recovered from the Maxwellian's raw moments."""

  @_needs_dgops
  def test_upar_from_M0_M1(self):
    """upar = M1/M0 must return the drift speed the moments were built with."""
    upar = ff.fetch_s1c0_div_s0c0([_m0(), _m1()])
    assert np.allclose(_cell_avg(upar), _UPAR, rtol=1e-12)

  @_needs_dgops
  def test_Tpar_from_M0_M1_M2par(self):
    """Tpar = m*(M2par - upar*M1)/M0 must return T for a Maxwellian."""
    Tpar = ff.fetch_Tpar_from_M0_M1_M2par([_m0(), _m1(), _m2par()])
    assert np.allclose(_cell_avg(Tpar), _TEMP, rtol=1e-10)

  @_needs_dgops
  def test_Tperp_from_M0_M2perp(self):
    """Tperp = m*M2perp/(2*M0) must return T for a Maxwellian."""
    Tperp = ff.fetch_Tperp_from_M0_M2perp([_m0(), _m2perp()])
    assert np.allclose(_cell_avg(Tperp), _TEMP, rtol=1e-12)

  def test_temp_from_Tpar_Tperp(self):
    """An isotropic (Tpar = Tperp = T) split must average back to T."""
    temp = ff.fetch_temp_from_Tpar_Tperp([_temp(), _temp()])
    assert np.allclose(_cell_avg(temp), _TEMP, rtol=1e-14)

  def test_M2_is_M2par_plus_M2perp(self):
    M2 = ff.fetch_s0c0_add_s1c0([_m2par(), _m2perp()])
    expected = _DENS*(_UPAR**2 + _VT_SQ) + _DENS*2.0*_VT_SQ
    assert np.allclose(_cell_avg(M2), expected, rtol=1e-12)

  def test_M3_is_M3par_plus_M3perp(self):
    M3 = ff.fetch_s0c0_add_s1c0([_m3par(), _m3perp()])
    expected = _DENS*(_UPAR**3 + 3.0*_UPAR*_VT_SQ) + _DENS*_UPAR*2.0*_VT_SQ
    assert np.allclose(_cell_avg(M3), expected, rtol=1e-12)

  def test_add_selects_the_requested_components(self):
    """fetch_s0c2_add_s0c3 must add components 2 and 3, not whole arrays."""
    gdata = _const_gdata([2.0, 3.0, 4.0, 5.0])
    out = ff.fetch_s0c2_add_s0c3([gdata])
    assert out.get_values().shape[-1] == _NUM_BASIS, "output must be single-component"
    assert np.allclose(_cell_avg(out), 4.0 + 5.0, rtol=1e-14)

  @_needs_dgops
  def test_press_p(self):
    """p = n*T."""
    press = ff.fetch_press_p([_m0(), _temp()])
    assert np.allclose(_cell_avg(press), _DENS*_TEMP, rtol=1e-12)


class TestMaxwellianMomentSources:
  """Quantities read out of the packed Maxwellian/BiMaxwellian moment files.

  Those files store [n, upar, T/m] and [n, upar, Tpar/m, Tperp/m], so these
  tests pin down both the component indexing and the mass normalization.
  """

  def test_Tpar_from_BiMax(self):
    bimax = _const_gdata([_DENS, _UPAR, _VT_SQ, _VT_SQ])
    Tpar = ff.fetch_Tpar_from_BiMax([bimax])
    assert np.allclose(_cell_avg(Tpar), _TEMP, rtol=1e-12)

  def test_Tperp_from_BiMax(self):
    bimax = _const_gdata([_DENS, _UPAR, _VT_SQ, _VT_SQ])
    Tperp = ff.fetch_Tperp_from_BiMax([bimax])
    assert np.allclose(_cell_avg(Tperp), _TEMP, rtol=1e-12)

  def test_temp_from_Max(self):
    maxmom = _const_gdata([_DENS, _UPAR, _VT_SQ])
    temp = ff.fetch_temp_from_Max([maxmom])
    assert np.allclose(_cell_avg(temp), _TEMP, rtol=1e-12)

  @_needs_dgops
  def test_press_from_Max(self):
    maxmom = _const_gdata([_DENS, _UPAR, _VT_SQ])
    press = ff.fetch_press_from_Max([maxmom])
    assert np.allclose(_cell_avg(press), _DENS*_TEMP, rtol=1e-12)

  @_needs_dgops
  def test_press_from_BiMax(self):
    bimax = _const_gdata([_DENS, _UPAR, _VT_SQ, _VT_SQ])
    press = ff.fetch_press_from_BiMax([bimax])
    assert np.allclose(_cell_avg(press), _DENS*_TEMP, rtol=1e-12)


class TestHeatFluxes:
  """Lab-frame energy fluxes and fluid-frame heat fluxes."""

  def test_qpar_lab_frame(self):
    """qpar = (m/2)*M3par."""
    qpar = ff.fetch_qpar([_m3par()])
    expected = 0.5*_MASS*_DENS*(_UPAR**3 + 3.0*_UPAR*_VT_SQ)
    assert np.allclose(_cell_avg(qpar), expected, rtol=1e-12)

  def test_qperp_lab_frame(self):
    """qperp = (m/2)*M3perp, which is n*u*T for a Maxwellian."""
    qperp = ff.fetch_qperp([_m3perp()])
    assert np.allclose(_cell_avg(qperp), _DENS*_UPAR*_TEMP, rtol=1e-12)

  @_needs_dgops
  def test_qpar_fluid_vanishes_for_a_maxwellian(self):
    """A Maxwellian carries no parallel heat flux in the fluid frame.

    The three terms of (m/2)*[M3par - 3*u*M2par + 2*u^2*M1] cancel exactly, so
    the residual is compared against the size of an individual term rather than
    against an absolute zero.
    """
    qpar_fluid = ff.fetch_qpar_fluid([_m0(), _m1(), _m2par(), _m3par()])
    term_scale = 0.5*_MASS*_DENS*abs(_UPAR)**3
    assert np.all(np.abs(_cell_avg(qpar_fluid))/term_scale < 1e-10)

  @_needs_dgops
  def test_qperp_fluid_vanishes_for_a_maxwellian(self):
    qperp_fluid = ff.fetch_qperp_fluid([_m0(), _m1(), _m2perp(), _m3perp()])
    term_scale = 0.5*_MASS*_DENS*abs(_UPAR)*2.0*_VT_SQ
    assert np.all(np.abs(_cell_avg(qperp_fluid))/term_scale < 1e-10)

  @_needs_dgops
  def test_qpar_fluid_tracks_a_skewed_distribution(self):
    """Guard against the vanishing tests passing for a function that is just 0.

    Skewing M3par away from its Maxwellian value by dM3 is a pure heat-flux
    perturbation, so the fluid-frame flux must become exactly (m/2)*dM3.
    """
    delta_m3 = 0.05*_DENS*_UPAR**3
    m3par_skewed = _const_gdata(_DENS*(_UPAR**3 + 3.0*_UPAR*_VT_SQ) + delta_m3)

    qpar_fluid = ff.fetch_qpar_fluid([_m0(), _m1(), _m2par(), m3par_skewed])
    assert np.allclose(_cell_avg(qpar_fluid), 0.5*_MASS*delta_m3, rtol=1e-8)

  @_needs_dgops
  def test_qperp_fluid_tracks_a_skewed_distribution(self):
    delta_m3 = 0.05*_DENS*_UPAR*2.0*_VT_SQ
    m3perp_skewed = _const_gdata(_DENS*_UPAR*2.0*_VT_SQ + delta_m3)

    qperp_fluid = ff.fetch_qperp_fluid([_m0(), _m1(), _m2perp(), m3perp_skewed])
    assert np.allclose(_cell_avg(qperp_fluid), 0.5*_MASS*delta_m3, rtol=1e-8)


class TestSoundSpeed:
  """c_s = sqrt(T/m_i)."""

  @_needs_dgops
  def test_c_s(self):
    c_s = ff.fetch_c_s([_temp()], mass_i=_MASS)
    assert np.allclose(_cell_avg(c_s), np.sqrt(_VT_SQ), rtol=1e-12)

  @_needs_dgops
  def test_c_s_uses_the_ion_mass_not_the_species_mass(self):
    """The species' own mass in ctx must not be used in place of mass_i."""
    mass_i = 100.0*_MASS
    c_s = ff.fetch_c_s([_temp()], mass_i=mass_i)
    assert np.allclose(_cell_avg(c_s), np.sqrt(_TEMP/mass_i), rtol=1e-12)

  def test_c_s_without_mass_i_is_an_error(self):
    """mass_i is not a species file attribute, so it must be asked for."""
    with pytest.raises(KeyError, match="mass_i"):
      ff.fetch_c_s([_temp()])

  # In case we want to throw an error for negative sqrt.
  # def test_c_s_of_a_negative_temperature_is_an_error(self):
  #   """A negative cell average must be reported, not turned into a NaN."""
  #   with pytest.raises(ValueError, match="negative cell average"):
  #     ff.fetch_c_s([_const_gdata(-_TEMP)], mass_i=_MASS)


class TestNormalizedHeatFluxes:
  """q_norm = q/(n*T*c_s)."""

  @_needs_dgops
  def test_qpar_norm(self):
    qpar = ff.fetch_qpar([_m3par()])
    c_s = ff.fetch_c_s([_temp()], mass_i=_MASS)

    qpar_norm = ff.fetch_qpar_norm([qpar, _m0(), _temp(), c_s])

    qpar_exact = 0.5*_MASS*_DENS*(_UPAR**3 + 3.0*_UPAR*_VT_SQ)
    expected = qpar_exact/(_DENS*_TEMP*np.sqrt(_VT_SQ))
    assert np.allclose(_cell_avg(qpar_norm), expected, rtol=1e-10)

  @_needs_dgops
  def test_qperp_norm(self):
    qperp = ff.fetch_qperp([_m3perp()])
    c_s = ff.fetch_c_s([_temp()], mass_i=_MASS)

    qperp_norm = ff.fetch_qperp_norm([qperp, _m0(), _temp(), c_s])

    expected = (_DENS*_UPAR*_TEMP)/(_DENS*_TEMP*np.sqrt(_VT_SQ))
    assert np.allclose(_cell_avg(qperp_norm), expected, rtol=1e-10)

  @_needs_dgops
  def test_qperp_norm_recovers_the_mach_number(self):
    """qperp/(n*T*c_s) = u/c_s for a Maxwellian, a known physical limit."""
    qperp = ff.fetch_qperp([_m3perp()])
    c_s = ff.fetch_c_s([_temp()], mass_i=_MASS)

    qperp_norm = ff.fetch_qperp_norm([qperp, _m0(), _temp(), c_s])

    assert np.allclose(_cell_avg(qperp_norm), _UPAR/np.sqrt(_VT_SQ), rtol=1e-10)


def _linear_gdata(coeff0: float, coeff1: float) -> GData:
  """A single-component p1 field with the given two modal coefficients."""
  values = np.zeros((_NUM_CELLS, _NUM_BASIS))
  values[:, 0] = coeff0
  values[:, 1] = coeff1
  gdata = GData(ctx={"poly_order": _POLY_ORDER, "basis_type": _BASIS_TYPE,
                     "mass": _MASS, "charge": 1.0})
  gdata.push([np.linspace(0.0, 1.0, _NUM_CELLS + 1)], values)
  return gdata


def _project_powsqrt_reference(coeff0: float, coeff1: float, exponent: float,
                               num_quad: int = _POLY_ORDER + 1) -> np.ndarray:
  """Independent numpy reference for pow(sqrt(f), exponent) projected on p1 1D.

  Reimplements the quadrature the gkeyll updater performs, from the definition
  rather than from its code: the 1D p1 modal basis orthonormal on [-1,1] is
  psi0 = 1/sqrt(2), psi1 = sqrt(3/2)*xi, and the projection of g onto it is
  coeff_k = integral of g*psi_k over [-1,1], evaluated by Gauss-Legendre.
  """
  xi, weights = np.polynomial.legendre.leggauss(num_quad)
  psi = np.array([np.full_like(xi, 1.0/np.sqrt(2.0)), np.sqrt(1.5)*xi])

  f_at_ords = coeff0*psi[0] + coeff1*psi[1]
  g_at_ords = np.power(np.sqrt(f_at_ords), exponent)

  return np.array([np.sum(weights*g_at_ords*psi[k]) for k in range(_NUM_BASIS)])


@_needs_dgops
class TestPowSqrt:
  """The gkyl_proj_powsqrt_on_basis binding backing c_s."""

  def test_sqrt_of_a_constant_field_is_exact(self):
    out = ff._sqrt_dg(_const_gdata(4.0))
    assert np.allclose(_cell_avg(out), 2.0, rtol=1e-12)

  def test_sqrt_keeps_the_higher_moments(self):
    """A varying field must produce a varying square root.

    This is the whole point of projecting onto the basis rather than taking
    the square root of the cell average: the slope must survive.
    """
    out = ff._sqrt_dg(_linear_gdata(4.0/_PSI0, 0.35))
    assert not np.allclose(out.get_values()[:, 1], 0.0), (
      "sqrt of a varying field must not be piecewise constant")

  def test_sqrt_matches_an_independent_quadrature(self):
    """Check the binding against a from-scratch numpy projection."""
    coeff0, coeff1 = 4.0/_PSI0, 0.35
    out = ff._sqrt_dg(_linear_gdata(coeff0, coeff1))

    expected = _project_powsqrt_reference(coeff0, coeff1, 1.0)
    assert np.allclose(out.get_values()[0, :], expected, rtol=1e-12)

  @pytest.mark.parametrize("exponent", [1.0, -1.0, 3.0])
  def test_exponents_match_an_independent_quadrature(self, exponent):
    """sqrt (1), reciprocal sqrt (-1) and the 3/2 power (3)."""
    coeff0, coeff1 = 4.0/_PSI0, 0.35
    out = ff._powsqrt_dg(_linear_gdata(coeff0, coeff1), exponent)

    expected = _project_powsqrt_reference(coeff0, coeff1, exponent)
    assert np.allclose(out.get_values()[0, :], expected, rtol=1e-12)

  def test_constant_field_exponents(self):
    """On a constant field the closed-form answers are exact."""
    field = _const_gdata(4.0)
    assert np.allclose(_cell_avg(ff._powsqrt_dg(field, 1.0)), 2.0, rtol=1e-12)
    assert np.allclose(_cell_avg(ff._powsqrt_dg(field, -1.0)), 0.5, rtol=1e-12)
    assert np.allclose(_cell_avg(ff._powsqrt_dg(field, 3.0)), 8.0, rtol=1e-12)

  def test_multi_component_input_is_rejected(self):
    """The kernel has no component index, so a vector field must not be taken."""
    from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops

    field = _const_gdata([1.0, 2.0, 3.0])  # Three physical components.
    with pytest.raises(ValueError, match="single-component"):
      GkeyllDGops().powsqrt(field, field, 1.0)
