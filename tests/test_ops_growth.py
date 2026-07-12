"""Tests for the ``growth`` verb — exponential growth-rate fitting."""

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


def _series(a=1.0, b=0.5, n=60):
  edges = np.linspace(0.0, 1.0, n + 1)
  centers = 0.5 * (edges[:-1] + edges[1:])
  y = a * np.exp(2.0 * b * centers)
  return _make([edges], y[:, np.newaxis]), centers


def test_recovers_growth_rate():
  d, _ = _series(a=1.0, b=1.5)
  out = ops.growth(d)
  assert out.ctx["growth_rate"] == pytest.approx(1.5, abs=1e-3)


def test_output_shape_is_one_shorter_than_edges():
  d, centers = _series()
  out = ops.growth(d)
  assert out.get_values().shape[0] == len(centers)


def test_explicit_guess_string_and_sequence_agree():
  d, _ = _series(a=1.0, b=0.8)
  out_str = ops.growth(d, guess="1,1")
  out_seq = ops.growth(d, guess=(1.0, 1.0))
  assert out_str.ctx["growth_rate"] == pytest.approx(out_seq.ctx["growth_rate"])


def test_minn_controls_minimum_window():
  d, _ = _series(a=1.0, b=1.0, n=100)
  out = ops.growth(d, minn=5)
  assert out.ctx["growth_rate"] == pytest.approx(1.0, abs=1e-2)


def test_inplace_and_tag_label():
  d, _ = _series()
  out = ops.growth(d, tag="g", label="growth-fit", inplace=True)
  assert out is d
  assert d.get_tag() == "g"
  assert d.get_label() == "growth-fit"


@needs_gkeyll
def test_rejects_modal_data():
  d = pg.load(F1)
  with pytest.raises(ValueError, match=r"\.interp\(\)"):
    ops.growth(d)
