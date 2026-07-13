"""Tests for the ``collect`` verb — stacking many datasets onto a time axis."""

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


def _frame(time, value, grid=None):
  grid = grid if grid is not None else [np.linspace(0.0, 1.0, 5)]
  d = GDataState(ctx={"time": time})
  d.push(list(grid), np.full((4, 1), value))
  return d
# end


def test_stacks_frames_sorted_by_time():
  a = _frame(1.0, 2.0)
  b = _frame(0.0, 1.0)
  out = ops.collect(a, b)
  np.testing.assert_allclose(out.get_grid()[0], [0.0, 1.0])
  np.testing.assert_allclose(out.get_values()[0].flatten(), 1.0)
  np.testing.assert_allclose(out.get_values()[1].flatten(), 2.0)
# end


def test_accepts_a_list_argument():
  frames = [_frame(0.0, 1.0), _frame(1.0, 2.0)]
  out = ops.collect(frames)
  assert out.get_values().shape[0] == 2
# end


def test_sumdata_reduces_spatial_axes():
  a = _frame(0.0, 3.0)
  b = _frame(1.0, 5.0)
  out = ops.collect(a, b, sumdata=True)
  np.testing.assert_allclose(out.get_values().flatten(), [3.0 * 4, 5.0 * 4])
  assert out.get_grid()[0].shape == (2,)
# end


def test_frame_stamp_falls_back_to_position_when_no_time_or_frame():
  a = GDataState()
  a.push([np.linspace(0.0, 1.0, 5)], np.full((4, 1), 10.0))
  b = GDataState()
  b.push([np.linspace(0.0, 1.0, 5)], np.full((4, 1), 20.0))
  out = ops.collect(a, b)
  np.testing.assert_allclose(out.get_grid()[0], [0, 1])
# end


def test_period_folds_time_axis():
  a = _frame(0.0, 1.0)
  b = _frame(3.0, 2.0)  # 3.0 % 2.0 == 1.0
  out = ops.collect(a, b, period=2.0)
  np.testing.assert_allclose(sorted(out.get_grid()[0]), [0.0, 1.0])
# end


def test_tag_and_label_defaults():
  a, b = _frame(0.0, 1.0), _frame(1.0, 2.0)
  out = ops.collect(a, b)
  assert out.get_tag() == "default"
  assert out.get_label() == "collect"
# end


def test_tag_and_label_explicit():
  a, b = _frame(0.0, 1.0), _frame(1.0, 2.0)
  out = ops.collect(a, b, tag="series", label="my series")
  assert out.get_tag() == "series"
  assert out.get_label() == "my series"
# end


def test_empty_raises():
  with pytest.raises(ValueError):
    ops.collect()
  # end
# end


@needs_gkeyll
def test_rejects_modal_data():
  modal = pg.load(F1)
  numpy_side = _frame(0.0, 1.0)
  with pytest.raises(ValueError, match=r"\.interpolate\(\)"):
    ops.collect(modal, numpy_side)
  # end
# end
