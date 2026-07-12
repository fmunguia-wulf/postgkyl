"""Tests for the ``fit`` verb — model fitting on a dataset's grid."""

from __future__ import annotations

import os

import numpy as np
import pytest

import postgkyl as pg
from postgkyl import gpython, ops
from postgkyl.core.state import GDataState

needs_gkeyll = pytest.mark.skipif(not gpython.available(),
    reason="no compiled Gkeyll (libg0core.so) found")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tests", "test_data")
F1 = os.path.join(DATA, "rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl")


def _make(grid, values, **ctx):
  d = GDataState(ctx=ctx or None)
  d.push(list(grid), values)
  return d


def _linear_dataset(a=2.0, b=1.0, n=20):
  edges = np.linspace(0.0, 1.0, n + 1)
  centers = 0.5 * (edges[:-1] + edges[1:])
  y = a * centers + b
  return _make([edges], y[:, np.newaxis]), centers


def test_linear_fit_recovers_parameters():
  d, _ = _linear_dataset(a=2.0, b=1.0)
  out = ops.fit(d, "linear")
  params = out.ctx["fit_params"][0]
  np.testing.assert_allclose(params, [2.0, 1.0], atol=1e-8)
  assert out.ctx["fit_R2"][0] > 0.999


def test_fitted_curve_matches_evaluated_model():
  d, centers = _linear_dataset(a=3.0, b=-2.0)
  out = ops.fit(d, "linear")
  expected = 3.0 * centers - 2.0
  np.testing.assert_allclose(out.get_values().flatten(), expected, atol=1e-8)


def test_explicit_guess_is_used():
  d, _ = _linear_dataset(a=2.0, b=1.0)
  out = ops.fit(d, "linear", guess="1.5,0.5")
  np.testing.assert_allclose(out.ctx["fit_params"][0], [2.0, 1.0], atol=1e-6)


def test_explicit_guess_as_string_matches_sequence():
  d, _ = _linear_dataset(a=2.0, b=1.0)
  out_str = ops.fit(d, "linear", guess="1.0,0.0")
  out_seq = ops.fit(d, "linear", guess=[1.0, 0.0])
  np.testing.assert_allclose(out_str.ctx["fit_params"][0], out_seq.ctx["fit_params"][0])


def test_gaussian_fit_rpn_and_multi_component():
  edges = np.linspace(-5.0, 5.0, 51)
  centers = 0.5 * (edges[:-1] + edges[1:])
  y0 = 3.0 * np.exp(-0.5 * (centers / 1.0) ** 2)
  y1 = 5.0 * np.exp(-0.5 * ((centers - 1.0) / 2.0) ** 2)
  d = _make([edges], np.stack([y0, y1], axis=-1))
  out = ops.fit(d, "gaussian")
  assert len(out.ctx["fit_params"]) == 2
  np.testing.assert_allclose(out.ctx["fit_params"][0][:2], [3.0, 0.0], atol=1e-3)


def test_wrong_dimensionality_raises():
  d, _ = _linear_dataset()
  with pytest.raises(ValueError, match="requires"):
    ops.fit(d, "plane")  # plane needs 2 spatial dims, data has 1


def test_unknown_fit_type_raises():
  d, _ = _linear_dataset()
  with pytest.raises(ValueError):
    ops.fit(d, "not_a_real_model_@@")


def test_drops_collapsed_axes():
  # A 2nd axis collapsed to a single cell (e.g. after select/integrate).
  edges0 = np.linspace(0.0, 1.0, 6)
  edges1 = np.linspace(0.0, 1.0, 2)  # single cell
  centers0 = 0.5 * (edges0[:-1] + edges0[1:])
  y = (2.0 * centers0 + 1.0)[:, np.newaxis, np.newaxis]
  d = _make([edges0, edges1], y)
  out = ops.fit(d, "linear")
  np.testing.assert_allclose(out.ctx["fit_params"][0], [2.0, 1.0], atol=1e-8)
  assert out.get_values().ndim == 2  # the collapsed axis was dropped


def test_grid_already_cell_centered_needs_no_conversion():
  centers = np.linspace(0.0, 1.0, 20)  # matches value count -- not +1
  y = 2.0 * centers + 1.0
  d = _make([centers], y[:, np.newaxis])
  out = ops.fit(d, "linear")
  np.testing.assert_allclose(out.ctx["fit_params"][0], [2.0, 1.0], atol=1e-8)


def test_plane_fit_2d():
  e0, e1 = np.linspace(0.0, 1.0, 6), np.linspace(0.0, 1.0, 5)
  c0, c1 = 0.5 * (e0[:-1] + e0[1:]), 0.5 * (e1[:-1] + e1[1:])
  X, Y = np.meshgrid(c0, c1, indexing="ij")
  z = 2.0 * X + 3.0 * Y + 1.0
  d = _make([e0, e1], z[..., np.newaxis])
  out = ops.fit(d, "plane")
  np.testing.assert_allclose(out.ctx["fit_params"][0], [2.0, 3.0, 1.0], atol=1e-6)


def test_inplace_and_tag_label():
  d, _ = _linear_dataset()
  out = ops.fit(d, "linear", tag="t", label="l", inplace=True)
  assert out is d
  assert d.get_tag() == "t"
  assert d.get_label() == "l"


@needs_gkeyll
def test_rejects_modal_data():
  d = pg.load(F1)
  with pytest.raises(ValueError, match=r"\.interp\(\)"):
    ops.fit(d, "linear")
