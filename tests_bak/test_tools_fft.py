"""Tests for tools.fft."""

from __future__ import annotations

import numpy as np
import pytest

import postgkeyll.tools as tools
from postgkeyll.data.gdata import GData
from postgkeyll.tools.fft import fft


def _make(grid, values):
    d = GData()
    d.push(grid, values)
    return d


class TestFft1D:
    def test_returns_freq_and_ft_values(self):
        N = 32
        grid = [np.linspace(0.0, 1.0, N + 1)]
        x_cc = 0.5 * (grid[0][:-1] + grid[0][1:])
        values = np.sin(2 * np.pi * x_cc)[:, np.newaxis]
        d = _make(grid, values)
        freq, ft = tools.fft(d)
        assert len(freq) == 1
        assert ft.shape[0] == N

    def test_dc_component_for_constant(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        d = _make(grid, values)
        freq, ft = tools.fft(d)
        np.testing.assert_allclose(np.abs(ft[0, 0]), float(N))

    def test_psd_halves_spectrum(self):
        N = 32
        grid = [np.linspace(0.0, 1.0, N + 1)]
        x_cc = 0.5 * (grid[0][:-1] + grid[0][1:])
        values = np.sin(2 * np.pi * x_cc)[:, np.newaxis]
        d = _make(grid, values)
        freq, ft = tools.fft(d, psd=True)
        assert ft.shape[0] == N // 2
        assert ft.shape[0] == len(freq[0])

    def test_overwrite_stores_result_in_data(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        d = _make(grid, values)
        tools.fft(d, overwrite=True)
        assert d.get_grid() is not None
        assert d.get_values().shape[0] == N

    def test_multiple_components(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.column_stack([np.ones(N), np.zeros(N)])
        d = _make(grid, values)
        freq, ft = tools.fft(d)
        assert ft.shape[-1] == 2

    def test_dummy_dimension_squeezed(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1), np.array([0.0, 1.0])]
        values = np.ones((N, 1, 1))
        d = _make(grid, values)
        freq, ft = tools.fft(d)
        assert len(freq) == 1

    def test_stack_parameter_alias(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        d = _make(grid, values)
        tools.fft(d, stack=True)
        assert d.get_values() is not None


class TestFft2D:
    def test_2d_fft_returns_correct_shape(self):
        Nx, Ny = 16, 8
        grid = [np.linspace(0.0, 1.0, Nx + 1), np.linspace(0.0, 1.0, Ny + 1)]
        values = np.ones((Nx, Ny, 1))
        d = _make(grid, values)
        freq, ft = tools.fft(d)
        assert ft.shape == (Nx, Ny, 1)
        assert len(freq) == 2

    def test_2d_psd(self):
        Nx, Ny = 16, 8
        grid = [np.linspace(0.0, 1.0, Nx + 1), np.linspace(0.0, 1.0, Ny + 1)]
        values = np.ones((Nx, Ny, 1))
        d = _make(grid, values)
        freq, ft = tools.fft(d, psd=True)
        assert ft.shape[0] == Nx // 2
        assert ft.shape[1] == Ny // 2

    def test_2d_overwrite(self):
        Nx, Ny = 8, 8
        grid = [np.linspace(0.0, 1.0, Nx + 1), np.linspace(0.0, 1.0, Ny + 1)]
        values = np.ones((Nx, Ny, 1))
        d = _make(grid, values)
        freq, ft = tools.fft(d, overwrite=False)
        assert freq is not None

    def test_2d_psd_shape(self):
        Nx, Ny = 8, 8
        grid = [np.linspace(0.0, 1.0, Nx + 1), np.linspace(0.0, 1.0, Ny + 1)]
        values = np.ones((Nx, Ny, 1))
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True)
        assert ft.shape == (Nx // 2, Ny // 2, 1)


class TestFft3D:
    def test_3d_fft_runs(self):
        Nx, Ny, Nz = 8, 8, 8
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.ones((Nx, Ny, Nz, 1))
        d = _make(grid, values)
        freq, ft = tools.fft(d)
        assert ft.shape == (Nx, Ny, Nz, 1)

    def test_3d_psd_halves_dims(self):
        Nx, Ny, Nz = 8, 8, 8
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.ones((Nx, Ny, Nz, 1))
        d = _make(grid, values)
        freq, ft = tools.fft(d, psd=True)
        assert ft.shape == (Nx // 2, Ny // 2, Nz // 2, 1)

    def test_3d_psd_no_iso(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.random.rand(Nx, Ny, Nz, 1)
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True, iso=False)
        assert ft.shape == (Nx // 2, Ny // 2, Nz // 2, 1)

    def test_3d_overwrite(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.ones((Nx, Ny, Nz, 1))
        dat = _make(grid, values)
        fft(dat, overwrite=True)
        assert dat.get_values() is not None

    @pytest.mark.filterwarnings("ignore:invalid value encountered in divide:RuntimeWarning")
    def test_3d_multi_comp(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.random.rand(Nx, Ny, Nz, 3)
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True, iso=True)
        assert ft.shape[-1] == 3


@pytest.mark.filterwarnings("ignore:invalid value encountered in divide:RuntimeWarning")
class TestFftIsotropic:
    def test_fft_3d_psd_iso(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.random.rand(Nx, Ny, Nz, 1)
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True, iso=True)
        assert isinstance(freq, list)
        assert len(freq) == 1
        assert ft.ndim == 2

    def test_fft_3d_psd_iso_positive(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        np.random.seed(42)
        values = np.ones((Nx, Ny, Nz, 1))
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True, iso=True)
        finite_vals = ft[np.isfinite(ft)]
        assert np.all(finite_vals >= 0)

    def test_fft_3d_psd_iso_overwrite(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.random.rand(Nx, Ny, Nz, 1)
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True, iso=True, overwrite=True)
        assert ft is not None
