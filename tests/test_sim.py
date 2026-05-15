"""Tests for the high-level simulation API merged from pygkyl."""
import numpy as np
import pytest

import postgkyl as pg
from postgkyl.sim import Species, NumParam, PhysParam, Normalization, Source, GBsource
from postgkyl.tools import phys_tools


class TestSpecies:
    def test_basic_attributes(self):
        s = Species('elc', m=9.109e-31, q=-1.602e-19, T0=100*1.602e-19, n0=1e19)
        assert s.name == 'elc'
        assert s.m == pytest.approx(9.109e-31)
        assert s.q == pytest.approx(-1.602e-19)
        assert s.T0 == pytest.approx(100 * 1.602e-19)
        assert s.n0 == pytest.approx(1e19)

    def test_gyromotion_computed_when_Bref_set(self):
        s = Species('ion', m=1.673e-27, q=1.602e-19, T0=1e3*1.602e-19, n0=1e19, Bref=1.0)
        assert s.omega_c is not None
        assert s.omega_c > 0

    def test_fluid_flag(self):
        s = Species('fluid', m=1.0, q=1.0, T0=1.0, n0=1.0, is_fluid=True)
        assert s.is_fluid is True


class TestNumParam:
    def test_grid_sizes_stored(self):
        n = NumParam(Nx=32, Ny=64, Nz=16, Nvp=8, Nmu=4)
        assert n.Nx == 32
        assert n.Ny == 64
        assert n.Nz == 16
        assert n.Nvp == 8
        assert n.Nmu == 4

    def test_domain_limits_default_none(self):
        n = NumParam()
        assert n.Lx is None
        assert n.x_min is None


class TestPhysParam:
    def test_default_constants(self):
        p = PhysParam()
        assert p.eV == pytest.approx(1.602e-19, rel=1e-3)
        assert p.mp == pytest.approx(1.673e-27, rel=1e-3)
        assert p.me == pytest.approx(9.109e-31, rel=1e-3)

    def test_custom_values(self):
        p = PhysParam(eV=1.0, mp=2.0, me=3.0)
        assert p.eV == 1.0
        assert p.mp == 2.0
        assert p.me == 3.0


class TestPhysTools:
    def test_thermal_velocity(self):
        eV = 1.602e-19
        me = 9.109e-31
        T = 100 * eV
        vth = phys_tools.thermal_vel(T, me)
        expected = np.sqrt(T / me)
        assert vth == pytest.approx(expected, rel=1e-6)

    def test_gyrofrequency(self):
        q, m, B = 1.602e-19, 9.109e-31, 1.0
        wc = phys_tools.gyrofrequency(q, m, B)
        expected = q * B / m
        assert wc == pytest.approx(expected, rel=1e-6)

    def test_larmor_radius(self):
        eV = 1.602e-19
        q, m, T, B = 1.602e-19, 9.109e-31, 100 * eV, 1.0
        rL = phys_tools.larmor_radius(q, m, T, B)
        assert rL > 0


class TestSource:
    """Tests for the Source plasma source profile class."""

    def _make_source(self, profile='gaussian'):
        eV = 1.602e-19
        return Source(
            n_src=1e19, x_src=0.05, Te_src=100*eV, Ti_src=200*eV,
            sigma_src=0.01, floor_src=0.01,
            density_src_profile=profile,
        )

    def test_attributes_stored(self):
        s = self._make_source()
        assert s.n_src == pytest.approx(1e19)
        assert s.x_src == pytest.approx(0.05)
        assert s.sigma_src == pytest.approx(0.01)
        assert s.floor_src == pytest.approx(0.01)

    def test_gaussian_density_peak_at_center(self):
        s = self._make_source('gaussian')
        x = np.linspace(0, 0.1, 200)
        n = s.density_profile(x)
        assert n.argmax() == np.abs(x - s.x_src).argmin()

    def test_gaussian_density_floor(self):
        s = self._make_source('gaussian')
        x = np.array([1e6])  # far from center
        n = s.density_profile(x)
        assert n == pytest.approx(s.n_src * s.floor_src, rel=1e-3)

    def test_exponential_density_peak_at_center(self):
        s = self._make_source('exponential')
        x = np.linspace(0, 0.1, 200)
        n = s.density_profile(x)
        assert n.argmax() == np.abs(x - s.x_src).argmin()

    def test_exponential_density_floor(self):
        s = self._make_source('exponential')
        x = np.array([1e6])
        n = s.density_profile(x)
        assert n == pytest.approx(s.n_src * s.floor_src, rel=1e-3)

    def test_default_temp_elc_flat_inside_source(self):
        eV = 1.602e-19
        s = self._make_source()
        x_in = np.array([s.x_src - 0.001])  # just inside the source
        T = s.temp_profile_elc(x_in)
        assert T[0] == pytest.approx(s.Te_src)

    def test_default_temp_ion_drops_outside_source(self):
        eV = 1.602e-19
        s = self._make_source()
        x_out = np.array([s.x_src + 4 * s.sigma_src])  # well outside
        T = s.temp_profile_ion(x_out)
        assert T[0] == pytest.approx(s.Ti_src * 3.0 / 8.0)

    def test_custom_density_callable(self):
        eV = 1.602e-19
        custom = lambda x, y=None, z=None: np.ones_like(x) * 5e18
        s = Source(n_src=0, x_src=0, Te_src=eV, Ti_src=eV,
                   sigma_src=1, floor_src=0, density_src_profile=custom)
        x = np.linspace(0, 1, 10)
        assert np.allclose(s.density_profile(x), 5e18)

    def test_invalid_profile_raises(self):
        eV = 1.602e-19
        with pytest.raises(ValueError):
            Source(n_src=1, x_src=0, Te_src=eV, Ti_src=eV,
                   sigma_src=1, floor_src=0, density_src_profile='bad_name')

    def test_info_runs_without_error(self, capsys):
        s = self._make_source()
        s.info()
        out = capsys.readouterr().out
        assert 'n_src' in out


class TestGBsource:
    """Tests for the GBsource grad-B source profile class."""

    def _make_species(self):
        eV = 1.602e-19
        return Species('ion', m=1.673e-27, q=1.602e-19,
                       T0=500*eV, n0=1e19, Bref=1.0)

    def _make_gbsource(self, model='singaus'):
        spec = self._make_species()
        return GBsource(
            n_srcGB=1e20, T_srcGB=500*1.602e-19,
            x_srcGB=0.0, sigma_srcGB=0.02, bfac_srcGB=1.0,
            species=spec, dens_model=model,
        )

    def test_attributes_stored(self):
        gb = self._make_gbsource()
        assert gb.nrate == pytest.approx(1e20)
        assert gb.sigma == pytest.approx(0.02)
        assert gb.bfac == pytest.approx(1.0)

    def test_dens_source_shape(self):
        gb = self._make_gbsource()
        x = np.linspace(-0.1, 0.1, 20)
        y = np.zeros_like(x)
        z = np.linspace(-np.pi, np.pi, 20)
        n = gb.dens_source(x, y, z)
        assert n.shape == x.shape

    def test_dens_source_nonnegative(self):
        gb = self._make_gbsource()
        x = np.linspace(-0.1, 0.1, 30)
        y = np.zeros_like(x)
        z = np.linspace(-np.pi, np.pi, 30)
        n = gb.dens_source(x, y, z)
        assert np.all(n >= 0)

    def test_temp_source_constant(self):
        gb = self._make_gbsource()
        x = np.linspace(-0.05, 0.05, 10)
        y = np.zeros_like(x)
        z = np.zeros_like(x)
        T = gb.temp_source(x, y, z)
        assert np.allclose(T, gb.T)

    def test_flux_model_nonnegative(self):
        gb = self._make_gbsource()
        x = np.linspace(-0.1, 0.1, 20)
        y = np.zeros_like(x)
        z = np.linspace(-np.pi, np.pi, 20)
        flux = gb.flux_model(x, y, z)
        assert np.all(flux >= 0)

    def test_invalid_dens_model_raises(self):
        with pytest.raises(ValueError):
            gb = self._make_gbsource()
            x = y = z = np.array([0.0])
            gb.dens_model = 'bad'
            gb.dens_source(x, y, z)

    def test_info_runs_without_error(self, capsys):
        gb = self._make_gbsource()
        gb.info()
        out = capsys.readouterr().out
        assert 'GBsource' in out


class TestPhysToolsExtended:
    """Extended tests for phys_tools covering edge cases."""

    def test_larmor_radius_scales_with_temperature(self):
        eV = 1.602e-19
        m, q, B = 9.109e-31, 1.602e-19, 1.0
        rL_low  = phys_tools.larmor_radius(q, m, 100*eV, B)
        rL_high = phys_tools.larmor_radius(q, m, 400*eV, B)
        assert rL_high > rL_low

    def test_gyrofrequency_scales_inversely_with_mass(self):
        q, B = 1.602e-19, 1.0
        wc_e = phys_tools.gyrofrequency(q, 9.109e-31, B)
        wc_i = phys_tools.gyrofrequency(q, 1.673e-27, B)
        assert wc_e > wc_i

    def test_thermal_velocity_scales_with_temperature(self):
        m = 9.109e-31
        eV = 1.602e-19
        vth_low  = phys_tools.thermal_vel(100*eV, m)
        vth_high = phys_tools.thermal_vel(400*eV, m)
        assert vth_high == pytest.approx(2 * vth_low, rel=1e-6)

    def test_larmor_radius_uncharged_returns_inf(self):
        # charge=0 → gyrofrequency=0 → infinite Larmor radius
        rL = phys_tools.larmor_radius(0.0, 1.0, 1.0, 1.0)
        assert np.isinf(rL)


class TestTopLevelImports:
    """Verify that all sim classes are accessible from the top-level postgkyl namespace."""
    def test_simulation_class_accessible(self):
        assert hasattr(pg, 'Simulation')

    def test_frame_class_accessible(self):
        assert hasattr(pg, 'Frame')

    def test_species_class_accessible(self):
        assert hasattr(pg, 'Species')

    def test_timeserie_class_accessible(self):
        assert hasattr(pg, 'TimeSerie')

    def test_geomparam_class_accessible(self):
        assert hasattr(pg, 'GeomParam')

    def test_normalization_class_accessible(self):
        assert hasattr(pg, 'Normalization')

    def test_existing_gdata_still_accessible(self):
        assert pg.GData is not None

    def test_existing_ginterpmodal_still_accessible(self):
        assert pg.GInterpModal is not None
