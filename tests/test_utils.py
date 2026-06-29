"""Tests for postgkyl utilities."""

from __future__ import annotations

import os
import time

import click
import numpy as np
import pytest

import postgkyl as pg
from postgkyl.commands.state import AppState
from postgkyl.data.gdata import GData
from postgkyl.gk.gk_utils import get_block_indices, parse_slice_string, read_gfile
from postgkyl.utils.input_parser import input_parser


dir_path = f"{os.path.dirname(__file__)}/test_data"


# ---------------------------------------------------------------------------
# input_parser
# ---------------------------------------------------------------------------

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
        grid = [np.linspace(0.0, 1.0, 4),
                np.linspace(0.0, 1.0, 3),
                np.linspace(0.0, 1.0, 3)]
        values = np.ones((5, 1))
        with pytest.raises(ValueError):
            input_parser((grid, values))


# ---------------------------------------------------------------------------
# parse_slice_string
# ---------------------------------------------------------------------------

class TestParseSliceString:
    def test_start_stop(self):
        s = parse_slice_string("2:5")
        assert s == slice(2, 5)

    def test_start_stop_step(self):
        s = parse_slice_string("1:10:2")
        assert s == slice(1, 10, 2)

    def test_no_start(self):
        s = parse_slice_string(":5")
        assert s.start is None
        assert s.stop == 5

    def test_no_stop(self):
        s = parse_slice_string("3:")
        assert s.start == 3
        assert s.stop is None

    def test_empty_string_both(self):
        s = parse_slice_string(":")
        assert s.start is None
        assert s.stop is None

    def test_invalid_part_raises(self):
        with pytest.raises(ValueError, match="Invalid slice part"):
            parse_slice_string("a:5")


# ---------------------------------------------------------------------------
# get_block_indices
# ---------------------------------------------------------------------------

class TestGetBlockIndices:
    def test_single_block(self):
        blocks = get_block_indices("-10", "*")
        assert blocks == [0]

    def test_all_blocks_no_files(self, tmp_path):
        pattern = str(tmp_path / "*.gkyl")
        blocks = get_block_indices("-1", pattern)
        assert blocks == []

    def test_comma_separated(self):
        blocks = get_block_indices("1,3,5", "*")
        assert blocks == [1, 3, 5]

    def test_slice_string(self):
        blocks = get_block_indices("0:3", "*")
        assert blocks == [0, 1, 2]

    def test_single_integer_string(self):
        blocks = get_block_indices("2", "*")
        assert blocks == [2]

    def test_invalid_string_raises(self):
        with pytest.raises(NameError):
            get_block_indices("invalid", "*")


# ---------------------------------------------------------------------------
# read_gfile
# ---------------------------------------------------------------------------

class TestReadGfile:
    def test_read_gfile_dynvector(self):
        fn = f"{dir_path}/twostream-field-energy.gkyl"
        if not os.path.exists(fn):
            pytest.skip("test data not available")
        grid, vals, pgdat = read_gfile(fn)
        assert vals is not None

    def test_read_gfile_returns_tuple(self):
        fn = f"{dir_path}/twostream-field-energy.gkyl"
        if not os.path.exists(fn):
            pytest.skip("test data not available")
        result = read_gfile(fn)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# verb_print
# ---------------------------------------------------------------------------

class TestVerbPrint:
    def test_verb_print_verbose_true(self, capsys):
        from postgkyl.utils.verb_print import verb_print

        ctx = click.core.Context(click.Command("test"))
        ctx.obj = AppState(verbose=True, start_time=time.time())
        verb_print(ctx, "test message")

    def test_verb_print_verbose_false(self):
        from postgkyl.utils.verb_print import verb_print

        ctx = click.core.Context(click.Command("test"))
        ctx.obj = AppState(verbose=False, start_time=time.time())
        verb_print(ctx, "test message")


# ---------------------------------------------------------------------------
# load_style
# ---------------------------------------------------------------------------

class TestLoadStyle:
    def test_load_style_simple_key(self, tmp_path):
        from postgkyl.utils.load_style import load_style

        style_file = tmp_path / "style.rc"
        style_file.write_text("lines.linewidth: 2\n")
        ctx = click.core.Context(click.Command("test"))
        ctx.obj = AppState()
        load_style(ctx, str(style_file))
        assert "lines.linewidth" in ctx.obj.rcParams
        assert ctx.obj.rcParams["lines.linewidth"] == "2"

    def test_load_style_multiple_keys(self, tmp_path):
        from postgkyl.utils.load_style import load_style

        style_file = tmp_path / "style.rc"
        style_file.write_text("lines.linewidth: 2\nfont.size: 12\n")
        ctx = click.core.Context(click.Command("test"))
        ctx.obj = AppState()
        load_style(ctx, str(style_file))
        assert "lines.linewidth" in ctx.obj.rcParams
        assert "font.size" in ctx.obj.rcParams
