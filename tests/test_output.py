"""Tests for output utilities."""

from __future__ import annotations

import importlib

import numpy as np
import pytest

import postgkyl as pg
from postgkyl.output.axis_and_grid_prep import (
    _default_axis_labels,
    _format_axis_label,
    _resolve_plot_labels,
    axis_and_grid_prep,
)
from postgkyl.output.downsample import downsample
from postgkyl.output.latex_conversion import latex_to_html, latex_to_unicode
from postgkyl.output.load_plot_data import load_plot_data
from postgkyl.output.nodal_to_cell_centered_grid import nodal_to_cell_centered_grid


load_plot_data_module = importlib.import_module("postgkyl.output.load_plot_data")


class _FakeGData:
    def __init__(self, num_dims: int, bounds: tuple[np.ndarray, np.ndarray], cells: np.ndarray):
        self._num_dims = num_dims
        self._bounds = bounds
        self._cells = cells

    def get_num_dims(self, squeeze: bool = False) -> int:
        assert squeeze is True
        return self._num_dims

    def get_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        return self._bounds

    def get_num_cells(self) -> np.ndarray:
        return self._cells


# ---------------------------------------------------------------------------
# nodal_to_cell_centered_grid
# ---------------------------------------------------------------------------

class TestNodalToCellCenteredGrid:
    def test_1d_nodal_grid(self):
        grid = [np.linspace(0.0, 1.0, 5)]
        cells = np.array([4])
        result = nodal_to_cell_centered_grid(grid, cells)
        assert len(result) == 1
        assert result[0].shape[0] == 4

    def test_1d_already_cell_centered(self):
        grid = [np.linspace(0.125, 0.875, 4)]
        cells = np.array([4])
        result = nodal_to_cell_centered_grid(grid, cells)
        assert len(result) == 1
        np.testing.assert_array_equal(result[0], grid[0])

    def test_1d_wrong_size_raises(self):
        grid = [np.linspace(0.0, 1.0, 7)]
        cells = np.array([4])
        with pytest.raises(ValueError):
            nodal_to_cell_centered_grid(grid, cells)

    def test_dimension_mismatch_raises(self):
        grid = [np.linspace(0.0, 1.0, 5)]
        cells = np.array([4, 3])
        with pytest.raises(ValueError):
            nodal_to_cell_centered_grid(grid, cells)

    def test_2d_nodal_grid(self):
        grid = [np.linspace(0.0, 1.0, 5), np.linspace(0.0, 2.0, 4)]
        cells = np.array([4, 3])
        result = nodal_to_cell_centered_grid(grid, cells)
        assert len(result) == 2
        assert result[0].shape[0] == 4
        assert result[1].shape[0] == 3

    def test_meshgrid_flag_1d(self):
        grid = [np.linspace(0.0, 1.0, 5)]
        cells = np.array([4])
        result = nodal_to_cell_centered_grid(grid, cells, meshgrid=True)
        assert len(result) == 1

    def test_meshgrid_flag_2d(self):
        grid = [np.linspace(0.0, 1.0, 5), np.linspace(0.0, 2.0, 4)]
        cells = np.array([4, 3])
        result = nodal_to_cell_centered_grid(grid, cells, meshgrid=True)
        assert len(result) == 2
        assert result[0].ndim == 2
        assert result[1].ndim == 2

    def test_2d_non1d_grid_nodal(self):
        g0 = np.linspace(0.0, 1.0, 5)
        g1 = np.linspace(0.0, 2.0, 4)
        g0_2d, g1_2d = np.meshgrid(g0, g1, indexing="ij")
        grid = [g0_2d, g1_2d]
        cells = np.array([4, 3])
        result = nodal_to_cell_centered_grid(grid, cells)
        assert len(result) == 2

    def test_1d_and_meshgrid_2d(self):
        x_nodal = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        centered = nodal_to_cell_centered_grid([x_nodal], np.array([4]))
        np.testing.assert_allclose(centered[0], np.array([0.5, 1.5, 2.5, 3.5]))

        x = np.array([0.0, 1.0, 2.0, 3.0])
        y = np.array([-1.0, 0.0, 1.0])
        mx, my = nodal_to_cell_centered_grid([x, y], np.array([3, 2]), meshgrid=True)
        assert mx.shape == (3, 2)
        assert my.shape == (3, 2)
        np.testing.assert_allclose(mx[:, 0], np.array([0.5, 1.5, 2.5]))
        np.testing.assert_allclose(my[0, :], np.array([-0.5, 0.5]))

    def test_raises_on_dim_mismatch(self):
        with np.testing.assert_raises(ValueError):
            nodal_to_cell_centered_grid([np.array([0.0, 1.0, 2.0])], np.array([2, 2]))


# ---------------------------------------------------------------------------
# axis_and_grid_prep helpers
# ---------------------------------------------------------------------------

class TestAxisAndGridPrepHelpers:
    def test_default_axis_labels(self):
        labels = _default_axis_labels(3)
        assert len(labels) == 3
        assert "$z_0$" in labels[0]

    def test_format_axis_label_no_shift_no_scale(self):
        result = _format_axis_label("x", 0.0, 1.0)
        assert result == "x"

    def test_format_axis_label_with_shift(self):
        result = _format_axis_label("x", 1.0, 1.0)
        assert "x" in result
        assert "1.00e+00" in result

    def test_format_axis_label_with_scale(self):
        result = _format_axis_label("x", 0.0, 2.0)
        assert "x" in result
        assert "2.00e+00" in result

    def test_format_axis_label_both(self):
        result = _format_axis_label("x", 1.0, 2.0)
        assert "x" in result

    def test_resolve_plot_labels_defaults(self):
        xl, yl, zl, cl = _resolve_plot_labels(
            None, None, None, "",
            0.0, 0.0, 0.0,
            1.0, 1.0, 1.0,
            num_dims=2,
        )
        assert xl is not None
        assert yl is not None

    def test_resolve_plot_labels_custom(self):
        xl, yl, zl, cl = _resolve_plot_labels(
            "myX", "myY", "myZ", "myC",
            0.0, 0.0, 0.0,
            1.0, 1.0, 2.0,
            num_dims=2,
        )
        assert xl == "myX"
        assert yl == "myY"
        assert "2.00" in cl


# ---------------------------------------------------------------------------
# axis_and_grid_prep (full function)
# ---------------------------------------------------------------------------

class TestAxisAndGridPrep:
    def _make_1d_inputs(self, N=10):
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        lower = np.array([0.0])
        upper = np.array([1.0])
        cells = np.array([N])
        return grid, values, lower, upper, cells

    def test_1d_basic(self):
        grid, values, lower, upper, cells = self._make_1d_inputs()
        result = axis_and_grid_prep(
            grid=grid, values=values,
            lower=lower, upper=upper, cells=cells,
            num_dims=1, streamline=False, quiver=False,
            num_axes=None, lineouts=None,
            xlabel=None, ylabel=None, zlabel=None, clabel="",
            xshift=0.0, yshift=0.0, zshift=0.0,
            xscale=1.0, yscale=1.0, zscale=1.0,
        )
        assert result is not None
        assert len(result) == 12

    def test_2d_basic(self):
        Nx, Ny = 4, 5
        grid = [np.linspace(0.0, 1.0, Nx + 1), np.linspace(0.0, 2.0, Ny + 1)]
        values = np.ones((Nx, Ny, 2))
        lower = np.array([0.0, 0.0])
        upper = np.array([1.0, 2.0])
        cells = np.array([Nx, Ny])
        result = axis_and_grid_prep(
            grid=grid, values=values,
            lower=lower, upper=upper, cells=cells,
            num_dims=2, streamline=False, quiver=False,
            num_axes=None, lineouts=None,
            xlabel=None, ylabel=None, zlabel=None, clabel="",
            xshift=0.0, yshift=0.0, zshift=0.0,
            xscale=1.0, yscale=1.0, zscale=1.0,
        )
        assert result is not None

    def test_with_streamline(self):
        Nx, Ny = 4, 5
        grid = [np.linspace(0.0, 1.0, Nx + 1), np.linspace(0.0, 2.0, Ny + 1)]
        values = np.ones((Nx, Ny, 2))
        lower = np.array([0.0, 0.0])
        upper = np.array([1.0, 2.0])
        cells = np.array([Nx, Ny])
        result = axis_and_grid_prep(
            grid=grid, values=values,
            lower=lower, upper=upper, cells=cells,
            num_dims=2, streamline=True, quiver=False,
            num_axes=None, lineouts=None,
            xlabel="X", ylabel="Y", zlabel=None, clabel="",
            xshift=0.0, yshift=0.0, zshift=0.0,
            xscale=1.0, yscale=1.0, zscale=1.0,
        )
        assert result is not None

    def test_with_lineouts_1(self):
        grid, values, lower, upper, cells = self._make_1d_inputs()
        result = axis_and_grid_prep(
            grid=grid, values=values,
            lower=lower, upper=upper, cells=cells,
            num_dims=1, streamline=False, quiver=False,
            num_axes=None, lineouts=1,
            xlabel=None, ylabel=None, zlabel=None, clabel="",
            xshift=0.0, yshift=0.0, zshift=0.0,
            xscale=1.0, yscale=1.0, zscale=1.0,
        )
        assert result is not None

    def test_with_num_axes(self):
        grid, values, lower, upper, cells = self._make_1d_inputs()
        values = np.ones((10, 3))
        result = axis_and_grid_prep(
            grid=grid, values=values,
            lower=lower, upper=upper, cells=cells,
            num_dims=1, streamline=False, quiver=False,
            num_axes=2, lineouts=None,
            xlabel="X", ylabel=None, zlabel=None, clabel="f",
            xshift=0.0, yshift=0.0, zshift=0.0,
            xscale=1.0, yscale=1.0, zscale=2.0,
        )
        g, v, lo, up, c, al, nc, ic, xl, yl, zl, cl = result
        assert nc == 2

    def test_prunes_collapsed_dims_and_formats_labels(self):
        x = np.linspace(0.0, 1.0, 4)
        y = np.array([0.0])
        z = np.linspace(-1.0, 1.0, 5)
        values = np.zeros((4, 1, 5, 3))
        out = axis_and_grid_prep(
            grid=[x, y, z],
            values=values,
            lower=np.array([0.0, 0.0, -1.0]),
            upper=np.array([1.0, 0.0, 1.0]),
            cells=np.array([4, 1, 5]),
            num_dims=2, streamline=False, quiver=False,
            num_axes=None, lineouts=None,
            xlabel=None, ylabel=None, zlabel=None, clabel="density",
            xshift=1.0, yshift=0.0, zshift=0.0,
            xscale=2.0, yscale=1.0, zscale=3.0,
        )
        grid, out_values, lower, upper, cells, _, num_comps, idx_comps, xlabel, ylabel, zlabel, clabel = out
        assert len(grid) == 2
        assert out_values.shape == (4, 5, 3)
        np.testing.assert_array_equal(lower, np.array([0.0, -1.0]))
        np.testing.assert_array_equal(upper, np.array([1.0, 1.0]))
        np.testing.assert_array_equal(cells, np.array([4, 5]))
        assert num_comps == 3
        assert list(idx_comps) == [0, 1, 2]
        assert xlabel == r"($z_0$ + 1.00e+00) $\times$ 2.00e+00"
        assert ylabel == r"$z_2$"
        assert zlabel == r"$z_1$ $\times$ 3.00e+00"
        assert clabel == r"density $\times$ 3.000e+00"

    def test_quiver_component_stride_and_lineout_xlabel(self):
        x = np.linspace(0.0, 1.0, 4)
        y = np.linspace(0.0, 1.0, 3)
        values = np.zeros((4, 3, 6))
        out = axis_and_grid_prep(
            grid=[x, y],
            values=values,
            lower=np.array([0.0, 0.0]),
            upper=np.array([1.0, 1.0]),
            cells=np.array([4, 3]),
            num_dims=2, streamline=False, quiver=True,
            num_axes=None, lineouts=1,
            xlabel=None, ylabel=None, zlabel=None, clabel="",
            xshift=0.0, yshift=0.0, zshift=0.0,
            xscale=1.0, yscale=1.0, zscale=1.0,
        )
        _, _, _, _, _, _, num_comps, idx_comps, xlabel, _, _, _ = out
        assert num_comps == 3
        assert list(idx_comps) == [0, 1, 2]
        assert xlabel == r"$z_1$"


# ---------------------------------------------------------------------------
# load_plot_data
# ---------------------------------------------------------------------------

def test_load_plot_data_tuple_mode_detects_dims_and_bounds():
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([-2.0, 0.0, 2.0])
    values = np.zeros((4, 3, 2))
    grid, out_values, num_dims, lower, upper, cells = load_plot_data(([x, y], values))
    assert num_dims == 2
    assert grid is not ([x, y])
    assert out_values is values
    np.testing.assert_allclose(lower, np.array([0.0, -2.0]))
    np.testing.assert_allclose(upper, np.array([3.0, 2.0]))
    np.testing.assert_allclose(cells, np.array([4.0, 3.0]))


def test_load_plot_data_gdata_mode_uses_gdata_metadata(monkeypatch):
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([-2.0, 0.0, 2.0])
    values = np.zeros((4, 3, 1))

    def _fake_input_parser(_):
        return [x, y], values

    monkeypatch.setattr(load_plot_data_module, "input_parser", _fake_input_parser)
    fake = _FakeGData(
        num_dims=2,
        bounds=(np.array([-1.0, -2.0]), np.array([1.0, 2.0])),
        cells=np.array([8, 9]),
    )
    _, out_values, num_dims, lower, upper, cells = load_plot_data(fake)
    assert out_values is values
    assert num_dims == 2
    np.testing.assert_array_equal(lower, np.array([-1.0, -2.0]))
    np.testing.assert_array_equal(upper, np.array([1.0, 2.0]))
    np.testing.assert_array_equal(cells, np.array([8, 9]))


# ---------------------------------------------------------------------------
# downsample
# ---------------------------------------------------------------------------

class TestDownsample:
    def test_no_downsample_zero(self):
        arr = np.ones((10,))
        result = downsample(arr, maximum_points_per_axis=0)
        assert result[0] is arr

    def test_1d_downsample(self):
        arr = np.ones((100,))
        result = downsample(arr, maximum_points_per_axis=10)
        assert result[0].shape[0] <= 10 + 1

    def test_2d_downsample(self):
        arr = np.ones((50, 50))
        result = downsample(arr, maximum_points_per_axis=10)
        assert result[0].shape[0] <= 11
        assert result[0].shape[1] <= 11

    def test_multiple_arrays(self):
        a = np.ones((50,))
        b = np.ones((50,))
        result = downsample(a, b, maximum_points_per_axis=10)
        assert len(result) == 2
        assert result[0].shape == result[1].shape

    def test_no_arrays(self):
        result = downsample()
        assert result == ()

    def test_shape_mismatch_returns_original(self):
        a = np.ones((50,))
        b = np.ones((30,))
        result = downsample(a, b, maximum_points_per_axis=10)
        assert result[0] is a

    def test_any_dimension_appends_last_index(self):
        shape = (5, 6, 7, 8)
        a = np.arange(np.prod(shape)).reshape(shape)
        b = -a
        out_a, out_b = downsample(a, b, maximum_points_per_axis=2)
        assert out_a.shape == (3, 3, 3, 3)
        assert out_b.shape == (3, 3, 3, 3)
        np.testing.assert_array_equal(out_b, -out_a)
        expected = a[np.ix_([0, 3, 4], [0, 3, 5], [0, 4, 6], [0, 4, 7])]
        np.testing.assert_array_equal(out_a, expected)

    def test_returns_input_for_bad_limits_and_shape_mismatch(self):
        a = np.arange(12).reshape(3, 4)
        b = np.arange(10).reshape(2, 5)
        out = downsample(a, maximum_points_per_axis=0)
        assert out[0] is a
        out = downsample(a, maximum_points_per_axis=-3)
        assert out[0] is a
        out = downsample(a, b, maximum_points_per_axis=2)
        assert out[0] is a
        assert out[1] is b

    def test_scalar_is_unchanged(self):
        scalar = np.array(42.0)
        out = downsample(scalar, maximum_points_per_axis=2)
        assert out[0] is scalar


# ---------------------------------------------------------------------------
# latex_conversion
# ---------------------------------------------------------------------------

class TestLatexConversion:
    def test_latex_to_unicode_simple(self):
        result = latex_to_unicode("hello")
        assert isinstance(result, str)
        assert result == "hello"

    def test_latex_to_unicode_empty(self):
        result = latex_to_unicode("")
        assert result == ""

    def test_latex_to_unicode_greek(self):
        result = latex_to_unicode(r"$\mu$")
        assert "μ" in result

    def test_latex_to_unicode_rho(self):
        result = latex_to_unicode(r"\rho")
        assert "ρ" in result

    def test_latex_to_html_subscript(self):
        result = latex_to_html(r"$B_{x}$")
        assert "<sub>" in result

    def test_latex_to_html_simple(self):
        result = latex_to_html("field")
        assert isinstance(result, str)

    def test_latex_to_html_empty(self):
        result = latex_to_html("")
        assert result == ""

    def test_latex_to_html_greek(self):
        result = latex_to_html(r"$\omega$")
        assert "ω" in result

    def test_latex_to_unicode_parallel(self):
        assert latex_to_unicode(r"$\mu_{\parallel}$") == "μ_{∥}"
        assert latex_to_unicode(r"E_{\perp}") == "E_{⊥}"

    def test_latex_to_html_subscripts_and_unicode(self):
        assert latex_to_html(r"$\mu_{\parallel}$") == "μ<sub>∥</sub>"
        assert latex_to_html(r"E_{\perp}") == "E<sub>⊥</sub>"


# ---------------------------------------------------------------------------
# module exports
# ---------------------------------------------------------------------------

def test_output_module_exports_helpers():
    assert pg.output.downsample is downsample
    assert pg.output.nodal_to_cell_centered_grid is nodal_to_cell_centered_grid
