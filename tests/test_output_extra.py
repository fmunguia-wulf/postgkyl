"""Tests for output utilities: nodal_to_cell_centered_grid, axis_and_grid_prep."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.output.nodal_to_cell_centered_grid import nodal_to_cell_centered_grid
from postgkyl.output.axis_and_grid_prep import (
    _default_axis_labels,
    _format_axis_label,
    _resolve_plot_labels,
    axis_and_grid_prep,
)
from postgkyl.output.latex_conversion import latex_to_unicode, latex_to_html
from postgkyl.output.downsample import downsample


# ---------------------------------------------------------------------------
# nodal_to_cell_centered_grid
# ---------------------------------------------------------------------------

class TestNodalToCellCenteredGrid:
    def test_1d_nodal_grid(self):
        # Nodal grid: N+1 points for N cells
        grid = [np.linspace(0.0, 1.0, 5)]  # 4 cells
        cells = np.array([4])
        result = nodal_to_cell_centered_grid(grid, cells)
        assert len(result) == 1
        assert result[0].shape[0] == 4  # cell-centered

    def test_1d_already_cell_centered(self):
        # Grid already has N points (not N+1)
        grid = [np.linspace(0.125, 0.875, 4)]
        cells = np.array([4])
        result = nodal_to_cell_centered_grid(grid, cells)
        assert len(result) == 1
        np.testing.assert_array_equal(result[0], grid[0])

    def test_1d_wrong_size_raises(self):
        grid = [np.linspace(0.0, 1.0, 7)]  # neither N nor N+1 for cells=4
        cells = np.array([4])
        with pytest.raises(ValueError):
            nodal_to_cell_centered_grid(grid, cells)

    def test_dimension_mismatch_raises(self):
        grid = [np.linspace(0.0, 1.0, 5)]
        cells = np.array([4, 3])  # wrong number of dims
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
        # meshgrid=True with 1D doesn't apply (needs num_dims > 1)
        grid = [np.linspace(0.0, 1.0, 5)]
        cells = np.array([4])
        result = nodal_to_cell_centered_grid(grid, cells, meshgrid=True)
        assert len(result) == 1

    def test_meshgrid_flag_2d(self):
        grid = [np.linspace(0.0, 1.0, 5), np.linspace(0.0, 2.0, 4)]
        cells = np.array([4, 3])
        result = nodal_to_cell_centered_grid(grid, cells, meshgrid=True)
        assert len(result) == 2
        # meshgrid result should be 2D arrays
        assert result[0].ndim == 2
        assert result[1].ndim == 2

    def test_2d_non1d_grid_nodal(self):
        # Multi-dim grid arrays (e.g., from c2p mapping) of shape N+1
        g0 = np.linspace(0.0, 1.0, 5)
        g1 = np.linspace(0.0, 2.0, 4)
        # Create 2D meshgrid arrays simulating c2p
        g0_2d, g1_2d = np.meshgrid(g0, g1, indexing="ij")
        grid = [g0_2d, g1_2d]
        cells = np.array([4, 3])
        result = nodal_to_cell_centered_grid(grid, cells)
        assert len(result) == 2


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
        assert "2.00" in cl  # scale applied to clabel


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
        assert result[0].shape[0] <= 10 + 1  # includes endpoint

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
        # Mismatched shapes → return originals
        assert result[0] is a
