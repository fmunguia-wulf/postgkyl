"""Tests for fft isotropic and additional paths."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.data.gdata import GData
from postgkyl.tools.fft import fft


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make(grid, values):
    d = GData()
    d.push(grid, values)
    return d


# ---------------------------------------------------------------------------
# Isotropic FFT (3D)
# ---------------------------------------------------------------------------

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
        # Should return 1D isotropic spectrum
        assert isinstance(freq, list)
        assert len(freq) == 1
        assert ft.ndim == 2  # (nkpolar, num_comps)

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
        # PSD should be non-negative for non-NaN entries
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
        # Even with overwrite=True, iso path returns the result
        assert ft is not None

    def test_fft_3d_psd_no_iso(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.random.rand(Nx, Ny, Nz, 1)
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True, iso=False)
        # 3D PSD output
        assert ft.shape == (Nx // 2, Ny // 2, Nz // 2, 1)

    def test_fft_3d_overwrite_no_iso(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.ones((Nx, Ny, Nz, 1))
        dat = _make(grid, values)
        fft(dat, overwrite=True)
        # Data should be updated in place
        assert dat.get_values() is not None

    def test_fft_2d_psd(self):
        Nx, Ny = 8, 8
        grid = [np.linspace(0.0, 1.0, Nx + 1), np.linspace(0.0, 1.0, Ny + 1)]
        values = np.ones((Nx, Ny, 1))
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True)
        assert ft.shape == (Nx // 2, Ny // 2, 1)

    def test_fft_multi_comp_3d(self):
        Nx, Ny, Nz = 4, 4, 4
        grid = [
            np.linspace(0.0, 1.0, Nx + 1),
            np.linspace(0.0, 1.0, Ny + 1),
            np.linspace(0.0, 1.0, Nz + 1),
        ]
        values = np.random.rand(Nx, Ny, Nz, 3)
        dat = _make(grid, values)
        freq, ft = fft(dat, psd=True, iso=True)
        # Should handle 3 components
        assert ft.shape[-1] == 3
