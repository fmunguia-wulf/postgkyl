"""Tests for tools.growth — exp2 function and fit_growth."""

from __future__ import annotations

import numpy as np
import pytest

import postgkeyll.tools as tools


class TestExp2:
    def test_at_zero(self):
        result = tools.exp2(0.0, a=2.0, b=1.0)
        np.testing.assert_allclose(result, 2.0)

    def test_positive_growth(self):
        # a*exp(2*b*x)
        x = 1.0
        a, b = 3.0, 0.5
        result = tools.exp2(x, a=a, b=b)
        np.testing.assert_allclose(result, a * np.exp(2 * b * x))

    def test_array_input(self):
        x = np.array([0.0, 1.0, 2.0])
        a, b = 1.0, 1.0
        result = tools.exp2(x, a=a, b=b)
        expected = np.exp(2 * x)
        np.testing.assert_allclose(result, expected)

    def test_negative_growth_rate(self):
        x = np.linspace(0, 3, 10)
        a, b = 2.0, -0.5
        result = tools.exp2(x, a=a, b=b)
        expected = 2.0 * np.exp(-1.0 * x)
        np.testing.assert_allclose(result, expected)


class TestFitGrowth:
    def test_recovers_known_growth_rate(self, capsys):
        # Generate exact exponential growth data
        x = np.linspace(0, 5, 60)
        true_a, true_b = 1.0, 0.8
        y = tools.exp2(x, true_a, true_b)

        params, R2, N = tools.fit_growth(x, y)
        # R2 should be very high for exact data
        assert R2 > 0.99
        # Fitted growth rate (returned as params[1]) should be close to true_b
        np.testing.assert_allclose(params[1], true_b, rtol=0.05)

    def test_returns_three_elements(self, capsys):
        x = np.linspace(0, 3, 30)
        y = tools.exp2(x, 1.0, 0.5)
        result = tools.fit_growth(x, y)
        assert len(result) == 3

    def test_best_N_is_within_bounds(self, capsys):
        x = np.linspace(0, 4, 40)
        y = tools.exp2(x, 1.0, 0.5)
        params, R2, N = tools.fit_growth(x, y, min_N=5)
        assert 5 <= N <= len(x)

    def test_custom_min_N(self, capsys):
        x = np.linspace(0, 3, 30)
        y = tools.exp2(x, 1.0, 0.5)
        params, R2, N = tools.fit_growth(x, y, min_N=10)
        assert N >= 10
