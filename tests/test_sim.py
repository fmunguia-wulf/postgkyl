"""Tests for the high-level simulation API merged from pygkyl."""
import numpy as np
import pytest

import postgkyl as pg
from postgkyl.sim import Species, NumParam, PhysParam, Normalization
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
        T, m, q, B = 100 * eV, 9.109e-31, 1.602e-19, 1.0
        rL = phys_tools.larmor_radius(T, m, q, B)
        assert rL > 0


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
