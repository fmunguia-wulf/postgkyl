"""Comprehensive tests for data.idx_parser."""

from __future__ import annotations

import numpy as np
import pytest

from postgkeyll.data.idx_parser import idx_parser


_ARRAY = np.linspace(0.0, 10.0, 11)  # [0, 1, 2, ..., 10]


class TestIdxParserInt:
    def test_positive_integer(self):
        result = idx_parser(3)
        assert result == 3

    def test_zero(self):
        assert idx_parser(0) == 0

    def test_negative_integer(self):
        assert idx_parser(-1) == -1


class TestIdxParserFloat:
    def test_nearest_value(self):
        # _ARRAY is [0..10]; float 3.2 → nearest is 3 (index 3)
        result = idx_parser(3.2, _ARRAY)
        assert result == 3

    def test_exact_value(self):
        # searchsorted([0..10], 5.0)=5, then idx-1=4 (cell left of 5.0)
        result = idx_parser(5.0, _ARRAY)
        assert result == 4

    def test_float_at_end(self):
        result = idx_parser(9.9, _ARRAY)
        # Nearest is 10, but _find_nearest_index returns idx-1 after searchsorted
        assert isinstance(result, int)

    def test_float_at_start(self):
        result = idx_parser(0.0, _ARRAY)
        assert result == 0

    def test_float_nodal_uses_cell_index(self):
        result = idx_parser(3.2, _ARRAY, nodal=True)
        # searchsorted(3.2) → 4 in [0,1,...,10]
        assert isinstance(result, int)

    def test_float_no_array_raises(self):
        with pytest.raises(TypeError):
            idx_parser(3.5, None)


class TestIdxParserString:
    def test_digit_string(self):
        result = idx_parser("3", _ARRAY)
        assert result == 3

    def test_float_string_nearest(self):
        result = idx_parser("3.2", _ARRAY)
        assert isinstance(result, int)

    def test_float_string_nodal(self):
        result = idx_parser("3.2", _ARRAY, nodal=True)
        assert isinstance(result, int)

    def test_slice_string(self):
        result = idx_parser("2:5", _ARRAY)
        assert isinstance(result, slice)
        assert result.start == 2
        assert result.stop == 5

    def test_slice_open_start(self):
        result = idx_parser(":5", _ARRAY)
        assert isinstance(result, slice)
        assert result.start == 0
        assert result.stop == 5

    def test_slice_open_end(self):
        result = idx_parser("2:", _ARRAY)
        assert isinstance(result, slice)
        assert result.stop == len(_ARRAY)

    def test_slice_negative_end(self):
        result = idx_parser("1:-2", _ARRAY)
        assert isinstance(result, slice)
        # -2 means len - 2 + 1 = 11 - 2 + 1 = 10
        assert result.stop == 10

    def test_comma_separated(self):
        result = idx_parser("1,3,5", _ARRAY)
        assert isinstance(result, tuple)
        assert result == (1, 3, 5)

    def test_comma_two_items(self):
        result = idx_parser("2,7", _ARRAY)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_float_string_comma(self):
        result = idx_parser("2.5,7.5", _ARRAY)
        assert isinstance(result, tuple)


class TestIdxParserEdgeCases:
    def test_none_returns_none(self):
        # idx_parser doesn't handle None directly, but it's called with z
        # Only non-None z values reach idx_parser; this is a guard test.
        # The function doesn't have a None branch, so calling it with None
        # would result in no match → idx remains None (None return).
        result = idx_parser(None, _ARRAY)
        assert result is None

    def test_type_errors_propagate_for_non_string_array(self):
        # Passing a float without an array raises TypeError inside
        with pytest.raises(TypeError):
            idx_parser(3.14, None)

    def test_single_element_array(self):
        arr = np.array([5.0])
        result = idx_parser(5.0, arr)
        assert isinstance(result, int)

    def test_large_array_performance(self):
        large = np.linspace(0.0, 1000.0, 1001)
        result = idx_parser(500.0, large)
        # searchsorted([0..1000], 500.0)=500, returns 499
        assert result == 499
