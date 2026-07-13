"""Tests for postgkyl.core.group.DatasetGroup — the verb-less container.

Ported from tests_bak/test_group.py: only the state-concerned tests survive
(construction, flattening, indexing, iteration, combining, repr). Tests that
exercised broadcasting (``__getattr__`` dispatch to member verbs) or terminal
verbs (``plot``/``info``/``animate``/``plotly_animate``/``collect``/``evaluate``) are
dropped here — those methods are deferred to the layer-10 fluent group; see
that layer's worklist.
"""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.core.group import DatasetGroup
from postgkyl.core.state import GDataState


def _line(tag: str = "default", offset: float = 0.0) -> GDataState:
  d = GDataState(tag=tag)
  d.push([np.linspace(0.0, 1.0, 9)], (np.arange(8.0) + offset)[:, None])
  return d
# end


class _SubGData(GDataState):
  """Stand-in for the fluent ``GData`` subclass (layer 10 adds the real one)."""
# end


class TestConstruction:
  def test_from_list(self):
    g = DatasetGroup([_line("a"), _line("b")])
    assert len(g) == 2
  # end

  def test_flattens_nested(self):
    g = DatasetGroup([_line("a"), [_line("b"), _line("c")]])
    assert len(g) == 3
  # end

  def test_flattens_nested_group(self):
    inner = DatasetGroup([_line("b"), _line("c")])
    g = DatasetGroup([_line("a"), inner])
    assert len(g) == 3
    assert all(isinstance(d, GDataState) for d in g)
  # end

  def test_iter_and_index(self):
    a, b = _line("a"), _line("b")
    g = DatasetGroup([a, b])
    assert list(g) == [a, b]
    assert g[0] is a
  # end

  def test_slice_returns_group(self):
    g = DatasetGroup([_line("a"), _line("b"), _line("c")])
    assert isinstance(g[:2], DatasetGroup)
    assert len(g[:2]) == 2
  # end

  def test_rejects_non_gdata(self):
    with pytest.raises(TypeError):
      DatasetGroup([1, 2, 3])
    # end
  # end

  def test_empty_group_default(self):
    g = DatasetGroup()
    assert len(g) == 0
    assert list(g) == []
  # end

  def test_empty_group_from_empty_list(self):
    g = DatasetGroup([])
    assert len(g) == 0
  # end

  def test_group_of_one(self):
    a = _line("a")
    g = DatasetGroup([a])
    assert len(g) == 1
    assert g[0] is a
  # end

  def test_heterogeneous_member_types(self):
    a = _line("a")
    b = _SubGData(tag="b")
    b.push([np.linspace(0.0, 1.0, 5)], np.arange(4.0)[:, None])
    g = DatasetGroup([a, b])
    assert len(g) == 2
    assert type(g[0]) is GDataState
    assert isinstance(g[1], _SubGData)
  # end
# end


class TestCombining:
  def test_with_appends(self):
    g = DatasetGroup([_line("a")]).with_(_line("b"), _line("c"))
    assert len(g) == 3
  # end

  def test_with_accepts_group(self):
    g = DatasetGroup([_line("a")]).with_(DatasetGroup([_line("b")]))
    assert len(g) == 2
  # end

  def test_and_operator(self):
    g = DatasetGroup([_line("a")]) & DatasetGroup([_line("b")])
    assert len(g) == 2
  # end

  def test_with_does_not_mutate(self):
    g = DatasetGroup([_line("a")])
    g.with_(_line("b"))
    assert len(g) == 1
  # end
# end


class TestSequenceAndRepr:
  def test_datasets_is_defensive_copy(self):
    a, b = _line("a"), _line("b")
    g = DatasetGroup([a, b])
    members = g.datasets
    members.append(_line("c"))
    assert len(g) == 2
  # end

  def test_repr_shows_count(self):
    g = DatasetGroup([_line("a"), _line("b")])
    assert repr(g) == "<DatasetGroup [2 datasets]>"
  # end

  def test_repr_empty(self):
    assert repr(DatasetGroup()) == "<DatasetGroup [0 datasets]>"
  # end
# end
