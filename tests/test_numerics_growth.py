"""Tests for postgkyl.numerics.growth — exp2 and fit_growth."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.numerics.growth import exp2, fit_growth


class TestExp2:
  def test_at_zero(self):
    np.testing.assert_allclose(exp2(0.0, a=2.0, b=1.0), 2.0)

  def test_positive_growth(self):
    x, a, b = 1.0, 3.0, 0.5
    np.testing.assert_allclose(exp2(x, a=a, b=b), a * np.exp(2 * b * x))

  def test_array_input(self):
    x = np.array([0.0, 1.0, 2.0])
    result = exp2(x, a=1.0, b=1.0)
    np.testing.assert_allclose(result, np.exp(2 * x))

  def test_negative_growth_rate(self):
    x = np.linspace(0, 3, 10)
    result = exp2(x, a=2.0, b=-0.5)
    np.testing.assert_allclose(result, 2.0 * np.exp(-1.0 * x))


class TestFitGrowth:
  def test_recovers_known_growth_rate(self):
    x = np.linspace(0, 5, 60)
    true_a, true_b = 1.0, 0.8
    y = exp2(x, true_a, true_b)
    params, R2, N = fit_growth(x, y)
    assert R2 > 0.99
    np.testing.assert_allclose(params[1], true_b, rtol=0.05)

  def test_returns_three_elements(self):
    x = np.linspace(0, 3, 30)
    y = exp2(x, 1.0, 0.5)
    result = fit_growth(x, y)
    assert len(result) == 3

  def test_best_N_is_within_bounds(self):
    x = np.linspace(0, 4, 40)
    y = exp2(x, 1.0, 0.5)
    params, R2, N = fit_growth(x, y, min_N=5)
    assert 5 <= N <= len(x)

  def test_custom_min_N(self):
    x = np.linspace(0, 3, 30)
    y = exp2(x, 1.0, 0.5)
    params, R2, N = fit_growth(x, y, min_N=10)
    assert N >= 10

  def test_curve_fit_failure_for_some_windows_is_skipped(self, monkeypatch):
    """A RuntimeError from curve_fit (non-convergence) for one fitting
    window is caught, not fatal -- the scan continues and still returns
    the best window that did converge."""
    import postgkyl.numerics.growth as growth_mod

    x = np.linspace(0, 5, 30)
    y = exp2(x, 1.0, 0.8)
    real_curve_fit = growth_mod.opt.curve_fit
    calls = {"n": 0}

    def flaky_curve_fit(*args, **kwargs):
      calls["n"] += 1
      if calls["n"] == 1:
        raise RuntimeError("simulated non-convergence")
      return real_curve_fit(*args, **kwargs)

    monkeypatch.setattr(growth_mod.opt, "curve_fit", flaky_curve_fit)
    params, R2, N = fit_growth(x, y, min_N=5)
    assert R2 > 0.9

  def test_all_windows_failing_to_converge_raises(self, monkeypatch):
    """If curve_fit never converges for any window in the scan range,
    fit_growth must raise a clear domain error rather than crash trying to
    rescale a still-tuple ``best_params`` (the inherited src_bak bug this
    guards against)."""
    import postgkyl.numerics.growth as growth_mod

    x = np.linspace(0, 5, 30)
    y = exp2(x, 1.0, 0.8)

    def always_fails(*args, **kwargs):
      raise RuntimeError("simulated non-convergence")

    monkeypatch.setattr(growth_mod.opt, "curve_fit", always_fails)
    with pytest.raises(RuntimeError, match="no fitting window converged|failed to converge"):
      fit_growth(x, y, min_N=5)

  def test_custom_function_is_used(self):
    """fit_growth is generic over `function`, not hard-wired to exp2."""
    def linear(x, a, b):
      return a * x + b

    x = np.linspace(0.1, 5, 40)
    y = 2.0 * x + 1.0
    params, R2, N = fit_growth(x, y, function=linear, p0=(1.0, 1.0))
    assert R2 > 0.99
