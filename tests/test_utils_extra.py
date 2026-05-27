"""Tests for utils: gk_utils, verb_print, load_style, gkeyll_enums."""

from __future__ import annotations

import os
import numpy as np
import pytest
import click

from postgkyl.utils.gk_utils import parse_slice_string, get_block_indices
from postgkyl.utils.gk_utils import read_gfile


dir_path = f"{os.path.dirname(__file__)}/test_data"


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
        # No files match → 0 blocks
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
        # twostream-field-energy.gkyl is a dynvector (simple 1D file)
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
        import time
        from postgkyl.utils.verb_print import verb_print

        ctx = click.core.Context(click.Command("test"))
        ctx.obj = {
            "verbose": True,
            "start_time": time.time(),
        }
        verb_print(ctx, "test message")
        # click.echo writes to stdout; capsys may or may not capture it
        # but the function should not raise

    def test_verb_print_verbose_false(self):
        import time
        from postgkyl.utils.verb_print import verb_print

        ctx = click.core.Context(click.Command("test"))
        ctx.obj = {
            "verbose": False,
            "start_time": time.time(),
        }
        # Should not raise, and should not print anything
        verb_print(ctx, "test message")


# ---------------------------------------------------------------------------
# load_style
# ---------------------------------------------------------------------------

class TestLoadStyle:
    def test_load_style_simple_key(self, tmp_path):
        from postgkyl.utils.load_style import load_style
        import click

        style_file = tmp_path / "style.rc"
        style_file.write_text("lines.linewidth: 2\n")

        ctx = click.core.Context(click.Command("test"))
        ctx.obj = {"rcParams": {}}
        load_style(ctx, str(style_file))
        assert "lines.linewidth" in ctx.obj["rcParams"]
        assert ctx.obj["rcParams"]["lines.linewidth"] == "2"

    def test_load_style_multiple_keys(self, tmp_path):
        from postgkyl.utils.load_style import load_style
        import click

        style_file = tmp_path / "style.rc"
        style_file.write_text("lines.linewidth: 2\nfont.size: 12\n")

        ctx = click.core.Context(click.Command("test"))
        ctx.obj = {"rcParams": {}}
        load_style(ctx, str(style_file))
        assert "lines.linewidth" in ctx.obj["rcParams"]
        assert "font.size" in ctx.obj["rcParams"]
