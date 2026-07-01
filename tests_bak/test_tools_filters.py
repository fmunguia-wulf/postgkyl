"""Comprehensive tests for tools.filters."""

from __future__ import annotations

import numpy as np
import pytest

import postgkeyll.tools as tools


class TestFftFiltering:
    def test_removes_high_frequency_component(self):
        N = 256
        dt = 1.0 / N
        t = np.linspace(0.0, 1.0 - dt, N)
        # Low frequency (f=2) + high frequency (f=50)
        signal = np.sin(2 * 2 * np.pi * t) + 0.5 * np.sin(50 * 2 * np.pi * t)
        filtered = tools.fft_filtering(signal, dt=dt, cutoff=10.0)
        # After filtering, high-frequency power should be much smaller
        high_freq_power_before = 0.5  # amplitude of high-freq component
        high_freq_power_after = np.std(np.real(filtered) - np.sin(2 * 2 * np.pi * t))
        assert high_freq_power_after < 0.1 * high_freq_power_before

    def test_preserves_dc_component(self):
        N = 128
        dt = 1.0 / N
        signal = np.ones(N) * 3.0
        filtered = tools.fft_filtering(signal, dt=dt, cutoff=1.0)
        np.testing.assert_allclose(np.real(filtered), 3.0, atol=1e-10)

    def test_output_same_length(self):
        N = 64
        signal = np.random.randn(N)
        filtered = tools.fft_filtering(signal, dt=0.01, cutoff=10.0)
        assert len(filtered) == N

    def test_cutoff_zero_removes_all(self):
        N = 64
        signal = np.sin(2 * np.pi * np.linspace(0, 1, N))
        filtered = tools.fft_filtering(signal, dt=1.0 / N, cutoff=0.0)
        # With cutoff=0, no frequency passes (nothing is ≤0 strictly)
        # Result should be nearly zero
        np.testing.assert_allclose(np.abs(filtered).max(), 0.0, atol=1e-10)


class TestButterFiltering:
    def test_removes_high_frequency(self):
        N = 512
        dt = 1.0 / N
        t = np.linspace(0.0, 1.0, N)
        low = np.sin(2 * 2 * np.pi * t)
        high = 0.5 * np.sin(100 * 2 * np.pi * t)
        filtered = tools.butter_filtering(low + high, dt=dt, cutoff=10.0)
        # High-frequency component should be attenuated: filtered variance < original variance
        skip = N // 5
        std_filtered = np.std(filtered[skip:])
        std_original = np.std((low + high)[skip:])
        # Filtered should have less variance (high freq removed)
        assert std_filtered < std_original

    def test_output_same_length(self):
        N = 64
        signal = np.random.randn(N)
        filtered = tools.butter_filtering(signal, dt=0.01, cutoff=5.0)
        assert len(filtered) == N

    def test_preserves_low_frequency(self):
        N = 512
        dt = 1.0 / N
        t = np.linspace(0.0, 1.0, N)
        freq = 1.0
        signal = np.sin(2 * np.pi * freq * t)
        filtered = tools.butter_filtering(signal, dt=dt, cutoff=100.0)
        # Low-pass with very high cutoff → signal amplitude mostly preserved
        skip = N // 5
        np.testing.assert_allclose(np.max(np.abs(filtered[skip:])), 1.0, atol=0.05)
