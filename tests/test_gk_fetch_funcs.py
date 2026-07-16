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
import postgkyl.utils.gkeyll_const as gkc
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


def _const_gdata(comp_avgs, mass: float = _MASS, charge: float = 1.0) -> GData:
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
                     "mass": mass, "charge": charge})
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


def _strip_ctx(gdata: GData, *keys) -> GData:
  """Drop attributes from a GData's context, as if the file did not carry them."""
  for key in keys:
    gdata.ctx.pop(key, None)
  return gdata


class TestGetCtxVal:
  """Resolution of species attributes: '--extra' first, then the file context."""

  def test_extra_overrides_the_context(self):
    """An explicit --extra must win over the attribute stored in the file."""
    gdata = _const_gdata(1.0, mass=_MASS)
    assert ff._get_ctx_val(gdata, "mass", mass=999.0) == 999.0

  def test_extra_array_overrides_the_context_per_species(self):
    """The override must hold for per-species arrays too, entry by entry."""
    gdata = _const_gdata(1.0, mass=_MASS)
    for species_idx, expected in enumerate([1.0, 2.0, 3.0]):
      got = ff._get_ctx_val(gdata, "mass", mass=[1.0, 2.0, 3.0], species_idx=species_idx)
      assert got == expected

  def test_context_is_used_when_extra_does_not_carry_the_key(self):
    """Without an --extra the file's own attribute is still what is used."""
    gdata = _const_gdata(1.0, mass=_MASS)
    assert ff._get_ctx_val(gdata, "mass") == _MASS
    assert ff._get_ctx_val(gdata, "mass", charge=999.0) == _MASS

  def test_scalar_extra_is_used_when_the_context_lacks_it(self):
    gdata = _strip_ctx(_const_gdata(1.0), "mass")
    assert ff._get_ctx_val(gdata, "mass", mass=7.0) == 7.0

  def test_none_in_context_falls_back_to_extra(self):
    gdata = _const_gdata(1.0)
    gdata.ctx["mass"] = None
    assert ff._get_ctx_val(gdata, "mass", mass=7.0) == 7.0

  def test_a_scalar_extra_applies_to_every_species(self):
    gdata = _strip_ctx(_const_gdata(1.0), "mass")
    for species_idx in range(3):
      assert ff._get_ctx_val(gdata, "mass", mass=7.0, species_idx=species_idx) == 7.0

  def test_per_species_array_is_picked_by_species_index(self):
    """'--extra mass=1,2,3' must give each species its own value."""
    gdata = _strip_ctx(_const_gdata(1.0), "mass")
    for species_idx, expected in enumerate([1.0, 2.0, 3.0]):
      got = ff._get_ctx_val(gdata, "mass", mass=[1.0, 2.0, 3.0], species_idx=species_idx)
      assert got == expected

  def test_array_without_a_species_index_is_an_error(self):
    """An array is meaningless where there is no species to index with."""
    gdata = _strip_ctx(_const_gdata(1.0), "mass")
    with pytest.raises(KeyError, match="not computed per species"):
      ff._get_ctx_val(gdata, "mass", mass=[1.0, 2.0])

  def test_too_short_an_array_is_an_error(self):
    """Fewer values than species must be reported, not silently wrap around."""
    gdata = _strip_ctx(_const_gdata(1.0), "mass")
    with pytest.raises(ValueError, match="only 2 values"):
      ff._get_ctx_val(gdata, "mass", mass=[1.0, 2.0], species_idx=2, species="ion2")

  def test_missing_everywhere_is_an_error(self):
    gdata = _strip_ctx(_const_gdata(1.0), "mass")
    with pytest.raises(KeyError, match="mass"):
      ff._get_ctx_val(gdata, "mass")


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


@_needs_dgops
class TestThermalSpeed:
  """vth = sqrt(T/m), m being the requested species' own mass."""

  def test_vth(self):
    vth = ff.fetch_vth([_temp()])
    assert np.allclose(_cell_avg(vth), np.sqrt(_VT_SQ), rtol=1e-12)

  def test_vth_uses_the_species_mass_from_ctx(self):
    """A different species mass must give a different thermal speed."""
    mass = 100.0*_MASS
    vth = ff.fetch_vth([_const_gdata(_TEMP, mass=mass)])
    assert np.allclose(_cell_avg(vth), np.sqrt(_TEMP/mass), rtol=1e-12)


# --- Sound speed: a two-ion-species plasma -----------------------------------
#
# A deuterium species (Z=1) and a doubly-charged impurity (Z=2), with the
# electron density set by quasineutrality. Every value is distinct so that a
# formula which mixes up a species, a charge state or a mass cannot accidentally
# agree.
_E_CHARGE = gkc.GKYL_ELEMENTARY_CHARGE

_N_I1, _T_I1, _M_I1, _Z_I1 = 2.7e19, 6.1e-18, 3.343e-27, 1.0
_N_I2, _T_I2, _M_I2, _Z_I2 = 4.0e18, 4.3e-18, 2.007e-26, 2.0
_N_E = _N_I1*_Z_I1 + _N_I2*_Z_I2  # Quasineutrality.
_T_E = 9.5e-18
_M_E = gkc.GKYL_ELECTRON_MASS


def _species_srcs(dens: float, temp: float, mass: float, charge: float) -> list:
  """The [M0, temp] source pair for one species, as fetch_c_s receives it."""
  return [_const_gdata(dens, mass=mass, charge=charge),
          _const_gdata(temp, mass=mass, charge=charge)]


def _elc_srcs():
  return _species_srcs(_N_E, _T_E, _M_E, -_E_CHARGE)

def _ion1_srcs():
  return _species_srcs(_N_I1, _T_I1, _M_I1, _Z_I1*_E_CHARGE)

def _ion2_srcs():
  return _species_srcs(_N_I2, _T_I2, _M_I2, _Z_I2*_E_CHARGE)


@_needs_dgops
class TestSoundSpeed:
  """The multi-species sound speeds, dispatched by '--extra kind='."""

  def test_ion_acoustic_single_ion_species(self):
    """With one Z=1 ion species the formula collapses to sqrt(Te/mi)."""
    c_s = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()],
                       species=["elc", "ion1"], kind="ion_acoustic")
    assert np.allclose(_cell_avg(c_s), np.sqrt(_T_E/_M_I1), rtol=1e-10)

  def test_ion_acoustic_two_ion_species(self):
    """c_s = sqrt(Te*sum(n_j*Z_j^2/m_j)/sum(n_j*Z_j))."""
    c_s = ff.fetch_c_s([_elc_srcs(), _ion1_srcs(), _ion2_srcs()],
                       species=["elc", "ion1", "ion2"], kind="ion_acoustic")

    numer = _N_I1*_Z_I1**2/_M_I1 + _N_I2*_Z_I2**2/_M_I2
    denom = _N_I1*_Z_I1 + _N_I2*_Z_I2
    assert np.allclose(_cell_avg(c_s), np.sqrt(_T_E*numer/denom), rtol=1e-10)

  def test_thermo_single_ion_species(self):
    """With one Z=1 ion species: sqrt((gamma_e*Te + gamma_i*Ti)/mi)."""
    c_s = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()],
                       species=["elc", "ion1"], kind="thermo")

    # n_e = n_i1 here only if quasineutrality holds for a single species, so
    # use the general formula rather than the reduced one.
    numer = 1.0*_N_E*_T_E + 3.0*_N_I1*_T_I1
    denom = _N_I1*_M_I1
    assert np.allclose(_cell_avg(c_s), np.sqrt(numer/denom), rtol=1e-10)

  def test_thermo_two_ion_species(self):
    """c_s = sqrt((gamma_e*n_e*Te + sum(gamma_j*n_j*Tj))/sum(n_j*m_j))."""
    c_s = ff.fetch_c_s([_elc_srcs(), _ion1_srcs(), _ion2_srcs()],
                       species=["elc", "ion1", "ion2"], kind="thermo")

    numer = 1.0*_N_E*_T_E + 3.0*(_N_I1*_T_I1 + _N_I2*_T_I2)
    denom = _N_I1*_M_I1 + _N_I2*_M_I2
    assert np.allclose(_cell_avg(c_s), np.sqrt(numer/denom), rtol=1e-10)

  def test_thermo_defaults_are_gamma_e_1_gamma_i_3(self):
    """The documented defaults must be what an un-flagged call actually uses."""
    default = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()],
                           species=["elc", "ion1"], kind="thermo")
    explicit = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()],
                            species=["elc", "ion1"], kind="thermo",
                            gamma_e=1.0, gamma_i=3.0)
    assert np.allclose(_cell_avg(default), _cell_avg(explicit), rtol=1e-12)

  def test_thermo_honours_the_gamma_overrides(self):
    c_s = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()],
                       species=["elc", "ion1"], kind="thermo",
                       gamma_e=5.0/3.0, gamma_i=5.0/3.0)

    numer = (5.0/3.0)*(_N_E*_T_E + _N_I1*_T_I1)
    assert np.allclose(_cell_avg(c_s), np.sqrt(numer/(_N_I1*_M_I1)), rtol=1e-10)

  def test_default_kind_is_ion_acoustic(self):
    default = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()], species=["elc", "ion1"])
    explicit = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()],
                            species=["elc", "ion1"], kind="ion_acoustic")
    assert np.allclose(_cell_avg(default), _cell_avg(explicit), rtol=1e-12)

  def test_species_order_does_not_matter(self):
    """Species are identified by charge sign, so the order is irrelevant."""
    forward = ff.fetch_c_s([_elc_srcs(), _ion1_srcs(), _ion2_srcs()],
                           species=["elc", "ion1", "ion2"], kind="ion_acoustic")
    shuffled = ff.fetch_c_s([_ion2_srcs(), _elc_srcs(), _ion1_srcs()],
                            species=["ion2", "elc", "ion1"], kind="ion_acoustic")
    assert np.allclose(_cell_avg(forward), _cell_avg(shuffled), rtol=1e-12)

  def test_electrons_are_found_by_charge_not_by_name(self):
    """A species called anything must still be treated as the electrons."""
    named = ff.fetch_c_s([_elc_srcs(), _ion1_srcs()],
                         species=["elc", "ion1"], kind="ion_acoustic")
    odd = ff.fetch_c_s([_species_srcs(_N_E, _T_E, _M_E, -_E_CHARGE), _ion1_srcs()],
                       species=["negatron", "deuterium"], kind="ion_acoustic")
    assert np.allclose(_cell_avg(named), _cell_avg(odd), rtol=1e-12)

  def test_no_electron_species_is_an_error(self):
    with pytest.raises(ValueError, match="exactly one negatively charged"):
      ff.fetch_c_s([_ion1_srcs(), _ion2_srcs()], species=["ion1", "ion2"])

  def test_two_electron_species_is_an_error(self):
    with pytest.raises(ValueError, match="exactly one negatively charged"):
      ff.fetch_c_s([_elc_srcs(), _elc_srcs(), _ion1_srcs()],
                   species=["elc1", "elc2", "ion1"])

  def test_no_ion_species_is_an_error(self):
    with pytest.raises(ValueError, match="no positively charged"):
      ff.fetch_c_s([_elc_srcs()], species=["elc"])

  def test_unknown_kind_is_an_error(self):
    with pytest.raises(ValueError, match="unknown kind"):
      ff.fetch_c_s([_elc_srcs(), _ion1_srcs()], species=["elc", "ion1"], kind="bogus")

  def test_missing_charge_attribute_is_an_error(self):
    """Charge missing from both the file and --extra must be reported."""
    srcs = _strip_ctx(_ion1_srcs()[0], "charge"), _ion1_srcs()[1]
    with pytest.raises(KeyError, match="charge"):
      ff.fetch_c_s([_elc_srcs(), list(srcs)], species=["elc", "ion1"])

  def test_attributes_can_come_from_per_species_extra_arrays(self):
    """Species attributes absent from the files can be given per species.

    This is the '--extra mass=..,..,charge=..,..' path: each species must pick
    its own entry, in the order of '--species'.
    """
    def bare(dens, temp):
      return [_strip_ctx(_const_gdata(dens), "mass", "charge"),
              _strip_ctx(_const_gdata(temp), "mass", "charge")]

    c_s = ff.fetch_c_s([bare(_N_E, _T_E), bare(_N_I1, _T_I1), bare(_N_I2, _T_I2)],
                       species=["elc", "ion1", "ion2"], kind="ion_acoustic",
                       mass=[_M_E, _M_I1, _M_I2],
                       charge=[-_E_CHARGE, _Z_I1*_E_CHARGE, _Z_I2*_E_CHARGE])

    numer = _N_I1*_Z_I1**2/_M_I1 + _N_I2*_Z_I2**2/_M_I2
    denom = _N_I1*_Z_I1 + _N_I2*_Z_I2
    assert np.allclose(_cell_avg(c_s), np.sqrt(_T_E*numer/denom), rtol=1e-10)

  def test_extra_arrays_must_cover_every_species(self):
    """Too few values must be reported rather than silently mis-assigned."""
    def bare(dens, temp):
      return [_strip_ctx(_const_gdata(dens), "mass", "charge"),
              _strip_ctx(_const_gdata(temp), "mass", "charge")]

    with pytest.raises(ValueError, match="only 2 values"):
      ff.fetch_c_s([bare(_N_E, _T_E), bare(_N_I1, _T_I1), bare(_N_I2, _T_I2)],
                   species=["elc", "ion1", "ion2"],
                   mass=[_M_E, _M_I1, _M_I2],
                   charge=[-_E_CHARGE, _Z_I1*_E_CHARGE])


@_needs_dgops
class TestNormalizedHeatFluxes:
  """q_norm = q/(n*T*vth)."""

  def test_qpar_norm(self):
    qpar = ff.fetch_qpar([_m3par()])
    vth = ff.fetch_vth([_temp()])

    qpar_norm = ff.fetch_qpar_norm([qpar, _m0(), _temp(), vth])

    qpar_exact = 0.5*_MASS*_DENS*(_UPAR**3 + 3.0*_UPAR*_VT_SQ)
    expected = qpar_exact/(_DENS*_TEMP*np.sqrt(_VT_SQ))
    assert np.allclose(_cell_avg(qpar_norm), expected, rtol=1e-10)

  def test_qperp_norm(self):
    qperp = ff.fetch_qperp([_m3perp()])
    vth = ff.fetch_vth([_temp()])

    qperp_norm = ff.fetch_qperp_norm([qperp, _m0(), _temp(), vth])

    expected = (_DENS*_UPAR*_TEMP)/(_DENS*_TEMP*np.sqrt(_VT_SQ))
    assert np.allclose(_cell_avg(qperp_norm), expected, rtol=1e-10)

  def test_qperp_norm_recovers_the_mach_number(self):
    """qperp/(n*T*vth) = u/vth for a Maxwellian, a known physical limit."""
    qperp = ff.fetch_qperp([_m3perp()])
    vth = ff.fetch_vth([_temp()])

    qperp_norm = ff.fetch_qperp_norm([qperp, _m0(), _temp(), vth])

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
  """The gkyl_proj_powsqrt_on_basis binding backing vth."""

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
