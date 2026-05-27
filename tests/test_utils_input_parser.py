"""Tests for utils.input_parser."""

from __future__ import annotations

import numpy as np
import pytest

import postgkyl as pg
from postgkyl.data.gdata import GData
from postgkyl.utils.input_parser import input_parser


class TestInputParser:
    def test_gdata_returns_grid_and_values(self):
        d = GData()
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 1))
        d.push(grid, values)
        g, v = input_parser(d)
        assert g is d.get_grid()
        assert v is d.get_values()

    def test_numpy_array_returns_empty_grid(self):
        arr = np.array([1.0, 2.0, 3.0])
        g, v = input_parser(arr)
        assert g == ()
        assert v is arr

    def test_tuple_of_grid_and_values(self):
        grid = [np.array([0.0, 1.0])]
        values = np.array([[1.0]])
        g, v = input_parser((grid, values))
        assert g is grid
        assert v is values

    def test_list_of_grid_and_values(self):
        grid = [np.array([0.0, 1.0])]
        values = np.array([[1.0]])
        g, v = input_parser([grid, values])
        assert g is grid
        assert v is values

    def test_tuple_grid_must_be_list_raises(self):
        with pytest.raises(TypeError, match="grid"):
            input_parser((np.array([0.0, 1.0]), np.array([[1.0]])))

    def test_tuple_values_must_be_ndarray_raises(self):
        grid = [np.array([0.0, 1.0])]
        with pytest.raises(TypeError, match="values"):
            input_parser((grid, [[1.0]]))

    def test_tuple_wrong_length_raises(self):
        with pytest.raises(TypeError):
            input_parser(([np.array([0.0])], np.array([[1.0]]), "extra"))

    def test_wrong_type_raises(self):
        with pytest.raises(TypeError):
            input_parser("a_string")

    def test_integer_raises(self):
        with pytest.raises(TypeError):
            input_parser(42)

    def test_2d_grid_values_tuple(self):
        grid = [np.linspace(0.0, 1.0, 4), np.linspace(0.0, 1.0, 3)]
        values = np.ones((3, 2, 1))
        g, v = input_parser((grid, values))
        assert len(g) == 2
        assert v.shape == (3, 2, 1)

    def test_dim_mismatch_raises(self):
        # 3D grid but 2D values (including component axis): len(grid)=3, len(shape)=2
        grid = [np.linspace(0.0, 1.0, 4),
                np.linspace(0.0, 1.0, 3),
                np.linspace(0.0, 1.0, 3)]
        values = np.ones((5, 1))  # shape len=2, but grid has 3 dims
        with pytest.raises(ValueError):
            input_parser((grid, values))
