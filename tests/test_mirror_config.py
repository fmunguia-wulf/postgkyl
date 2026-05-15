"""Tests for LorentzianMirrorConfig."""
import numpy as np
import pytest

import postgkyl as pg
from postgkyl.configs import LorentzianMirrorConfig


# Reference parameters from the C input file
_REF = dict(
    Te0_eV=940.0,
    n0=3e19,
    B_p=0.53,
    beta=0.4,
    mi_amu=2.014,      # deuterium
    Z_min=-2.5, Z_max=2.5,
    Z_m=0.98,
    mcB=3.691260,
    gamma=0.226381,
    RatZeq0=0.10,
)


class TestLorentzianMirrorConfigInit:
    """Test that parameters are stored and derived quantities are correct."""

    def setup_method(self):
        self.cfg = LorentzianMirrorConfig(**_REF)

    def test_primary_params_stored(self):
        cfg = self.cfg
        assert cfg.Te0 == pytest.approx(940.0 * cfg.eV)
        assert cfg.n0  == pytest.approx(3e19)
        assert cfg.B_p == pytest.approx(0.53)
        assert cfg.beta == pytest.approx(0.4)
        assert cfg.Z_min == pytest.approx(-2.5)
        assert cfg.Z_max == pytest.approx(2.5)
        assert cfg.Z_m   == pytest.approx(0.98)

    def test_ion_mass(self):
        cfg = self.cfg
        assert cfg.mi == pytest.approx(2.014 * cfg.mp, rel=1e-6)

    def test_charges(self):
        cfg = self.cfg
        assert cfg.qi == pytest.approx(cfg.eV)
        assert cfg.qe == pytest.approx(-cfg.eV)

    def test_Ti0_from_pressure_balance(self):
        """Ti0 derived from beta pressure balance must match the C formula."""
        cfg = self.cfg
        # tau = B_p^2 * beta / (2*mu0*n0*Te0) - 1
        expected_tau = (cfg.B_p**2 * cfg.beta) / (2.0 * cfg.mu0 * cfg.n0 * cfg.Te0) - 1.0
        assert cfg.tau == pytest.approx(expected_tau, rel=1e-6)
        assert cfg.Ti0 == pytest.approx(expected_tau * cfg.Te0, rel=1e-6)

    def test_Ti0_positive(self):
        assert self.cfg.Ti0 > 0

    def test_thermal_speeds(self):
        cfg = self.cfg
        assert cfg.vti == pytest.approx(np.sqrt(cfg.Ti0 / cfg.mi), rel=1e-9)
        assert cfg.vte == pytest.approx(np.sqrt(cfg.Te0 / cfg.me), rel=1e-9)
        assert cfg.vte > cfg.vti   # electrons always faster than ions

    def test_velocity_grid_bounds(self):
        cfg = self.cfg
        assert cfg.vpar_max_ion == pytest.approx(16.0 * cfg.vti, rel=1e-9)
        assert cfg.mu_max_ion   == pytest.approx(cfg.mi * (3.0*cfg.vti)**2 / (2.0*cfg.B_p), rel=1e-9)
        assert cfg.vpar_max_elc == pytest.approx(4.0  * cfg.vte, rel=1e-9)
        assert cfg.mu_max_elc   == pytest.approx(cfg.me * (4.0*cfg.vte)**2 / (2.0*cfg.B_p), rel=1e-9)

    def test_nuIon_positive(self):
        assert self.cfg.nuIon > 0

    def test_nuIon_scales_with_nuFrac(self):
        cfg1 = LorentzianMirrorConfig(**_REF, nuFrac=1.0)
        cfg2 = LorentzianMirrorConfig(**_REF, nuFrac=2.0)
        assert cfg2.nuIon == pytest.approx(2.0 * cfg1.nuIon, rel=1e-9)

    def test_grid_sizes_stored(self):
        cfg = self.cfg
        assert cfg.Nz        == 400
        assert cfg.Nvpar     == 64
        assert cfg.Nmu       == 32
        assert cfg.Nvpar_elc == 8
        assert cfg.Nmu_elc   == 8


class TestLorentzianMirrorConfigDimensionality:
    def test_default_is_1x2v(self):
        cfg = LorentzianMirrorConfig()
        assert cfg.dimensionality == '1x2v'

    def test_2x2v_accepted(self):
        cfg = LorentzianMirrorConfig(dimensionality='2x2v', Npsi=4)
        assert cfg.dimensionality == '2x2v'
        assert cfg.Npsi == 4

    def test_invalid_dimensionality_raises(self):
        with pytest.raises(ValueError, match="dimensionality"):
            LorentzianMirrorConfig(dimensionality='3x2v')

    def test_3x2v_raises(self):
        with pytest.raises(ValueError):
            LorentzianMirrorConfig(dimensionality='3x2v')


class TestLorentzianMirrorConfigGeometry:
    def setup_method(self):
        self.cfg = LorentzianMirrorConfig(**_REF)

    def test_mirror_ratio_above_one(self):
        assert self.cfg.mirror_ratio > 1.0

    def test_loss_cone_angle_in_valid_range(self):
        theta = self.cfg.loss_cone_angle
        assert 0.0 < theta < np.pi / 2

    def test_higher_beta_reduces_Ti0(self):
        """Lower beta → lower Ti0 (beta sets pressure balance)."""
        cfg_high = LorentzianMirrorConfig(**{**_REF, 'beta': 0.4})
        cfg_low  = LorentzianMirrorConfig(**{**_REF, 'beta': 0.2})
        assert cfg_high.Ti0 > cfg_low.Ti0


class TestLorentzianMirrorConfigSpecies:
    def setup_method(self):
        self.cfg = LorentzianMirrorConfig(**_REF)

    def test_make_species_returns_two(self):
        ion, elc = self.cfg.make_species()
        assert ion.name == 'ion'
        assert elc.name == 'elc'

    def test_ion_mass_correct(self):
        ion, _ = self.cfg.make_species()
        assert ion.m == pytest.approx(self.cfg.mi, rel=1e-9)

    def test_elc_mass_correct(self):
        _, elc = self.cfg.make_species()
        assert elc.m == pytest.approx(self.cfg.me, rel=1e-9)

    def test_ion_temperature_matches_Ti0(self):
        ion, _ = self.cfg.make_species()
        assert ion.T0 == pytest.approx(self.cfg.Ti0, rel=1e-9)

    def test_elc_temperature_matches_Te0(self):
        _, elc = self.cfg.make_species()
        assert elc.T0 == pytest.approx(self.cfg.Te0, rel=1e-9)

    def test_gyromotion_computed_at_Bp(self):
        ion, elc = self.cfg.make_species()
        assert ion.omega_c is not None
        assert elc.omega_c is not None
        assert abs(ion.omega_c) > 0
        assert abs(elc.omega_c) > 0

    def test_electron_gyrofreq_much_higher_than_ion(self):
        # |omega_c| = |q|*B/m; electrons are lighter so |omega_ce| >> |omega_ci|
        ion, elc = self.cfg.make_species()
        assert abs(elc.omega_c) > abs(ion.omega_c)


class TestLorentzianMirrorConfigSimulation:
    def setup_method(self):
        self.cfg = LorentzianMirrorConfig(**_REF)

    def test_make_simulation_returns_simulation(self):
        sim = self.cfg.make_simulation()
        assert isinstance(sim, pg.Simulation)

    def test_simulation_has_both_species(self):
        sim = self.cfg.make_simulation()
        assert 'ion' in sim.species
        assert 'elc' in sim.species

    def test_simulation_dimensionality(self):
        sim = self.cfg.make_simulation()
        assert sim.dimensionality == '1x2v'

    def test_2x2v_simulation(self):
        cfg = LorentzianMirrorConfig(dimensionality='2x2v')
        sim = cfg.make_simulation()
        assert sim.dimensionality == '2x2v'

    def test_simulation_poly_order(self):
        cfg = LorentzianMirrorConfig(poly_order=2)
        sim = cfg.make_simulation()
        assert sim.polyOrder == 2

    def test_simulation_accessible_from_top_level(self):
        assert hasattr(pg, 'LorentzianMirrorConfig')


class TestLorentzianMirrorConfigInfo:
    def test_info_runs_without_error(self, capsys):
        cfg = LorentzianMirrorConfig(**_REF)
        cfg.info()
        out = capsys.readouterr().out
        assert 'LorentzianMirrorConfig' in out
        assert '1x2v' in out

    def test_info_2x2v(self, capsys):
        cfg = LorentzianMirrorConfig(dimensionality='2x2v')
        cfg.info()
        out = capsys.readouterr().out
        assert '2x2v' in out
        assert 'Npsi' in out
