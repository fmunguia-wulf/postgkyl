"""Postgkyl module for testing DG interpolation"""
import os
from pathlib import Path
import numpy as np

import postgkyl as pg

from conftest import GEN_DIR


class TestGkylInterpolate:
  """Test Postgkyl interpolate functions."""
  dir_path =  f"{os.path.dirname(__file__)}/test_data"

  def test_ser_p1(self):
    data = pg.GData(f"{self.dir_path:s}/shock-f-ser-p1.gkyl")
    dg = pg.GInterpModal(data, poly_order=1, basis_type="ms")
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 17)
    np.testing.assert_equal(len(grid[1]), 17)
    np.testing.assert_array_equal(values.shape, (16, 16, 1))
    np.testing.assert_approx_equal(values.mean(), 0.5)

  def test_ser_p2(self):
    data = pg.GData(f"{self.dir_path:s}/twostream-f-p2.gkyl")
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 193)
    np.testing.assert_equal(len(grid[1]), 97)
    np.testing.assert_array_equal(values.shape, (192, 96, 1))
    np.testing.assert_approx_equal(values.mean(), 0.08337313364405809)

  def test_ser_p1_i(self):
    data = pg.GData(f"{self.dir_path:s}/shock-f-ser-p1.gkyl")
    dg = pg.GInterpModal(data, poly_order=1, basis_type='ms', num_interp=3)
    _, values = dg.interpolate()
    np.testing.assert_array_equal(values.shape, (24, 24, 1))
  #end

  def test_ser_p2_i(self):
    data = pg.GData(f"{self.dir_path:s}/twostream-f-p2.gkyl")
    dg = pg.GInterpModal(data, num_interp=4)
    _, values = dg.interpolate()
    np.testing.assert_array_equal(values.shape, (256, 128, 1))
  #end

  def test_ten_p1(self):
    data = pg.GData(f"{self.dir_path:s}/shock-f-ten-p1.gkyl")
    dg = pg.GInterpModal(data, poly_order=1, basis_type="mt")
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 17)
    np.testing.assert_equal(len(grid[1]), 17)
    np.testing.assert_array_equal(values.shape, (16, 16, 1))
    np.testing.assert_approx_equal(values.mean(), 0.5)

  def test_ser_p1_c2p(self):
    data = pg.GData(f"{self.dir_path:s}/shock-f-ser-p1.gkyl",
        mapc2p_name=f"{self.dir_path:s}/shock-rtheta-ser.gkyl")
    dg = pg.GInterpModal(data, poly_order=1, basis_type="ms")
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 17)
    np.testing.assert_equal(len(grid[1]), 17)
    np.testing.assert_array_equal(values.shape, (16, 16, 1))
    np.testing.assert_approx_equal(values.mean(), 0.5)

  def test_ten_p1_c2p(self):
    data = pg.GData(f"{self.dir_path:s}/shock-f-ten-p1.gkyl",
        mapc2p_name=f"{self.dir_path:s}/shock-rtheta-ten.gkyl")
    dg = pg.GInterpModal(data, poly_order=1, basis_type="mt")
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 17)
    np.testing.assert_equal(len(grid[1]), 17)
    np.testing.assert_array_equal(values.shape, (16, 16, 1))
    np.testing.assert_approx_equal(values.mean(), 0.5)


class TestGeneratedInterpolate:
  """Interpolation tests on synthetic data covering all basis/dimension combos.

  Each test uses GData auto-detection of poly_order and basis_type from the
  file metadata, so no explicit arguments are passed to GInterpModal.
  Assertions check output shapes; value correctness for serendipity and tensor
  is verified separately in TestGkylInterpolate.
  """

  def test_1d_ser_p1(self):
    data = pg.GData(GEN_DIR / "1d_ms_p1.gkyl")
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 17)       # 8*(1+1)+1
    np.testing.assert_array_equal(values.shape, (16, 1))
    assert np.all(np.isfinite(values))

  def test_1d_ser_p2(self):
    data = pg.GData(GEN_DIR / "1d_ms_p2.gkyl")
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 25)       # 8*(2+1)+1
    np.testing.assert_array_equal(values.shape, (24, 1))
    assert np.all(np.isfinite(values))

  def test_2d_ser_p1_metadata(self):
    """Auto-detected poly_order/basis_type from file metadata."""
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl")
    assert data.ctx["poly_order"] == 1
    assert data.ctx["basis_type"] == "serendipity"
    dg = pg.GInterpModal(data)
    _, values = dg.interpolate()
    np.testing.assert_array_equal(values.shape, (16, 16, 1))

  def test_2d_ser_p2(self):
    data = pg.GData(GEN_DIR / "2d_ms_p2.gkyl")
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 25)
    np.testing.assert_array_equal(values.shape, (24, 24, 1))
    assert np.all(np.isfinite(values))

  def test_2d_ten_p1(self):
    data = pg.GData(GEN_DIR / "2d_mt_p1.gkyl")
    dg = pg.GInterpModal(data)
    _, values = dg.interpolate()
    np.testing.assert_array_equal(values.shape, (16, 16, 1))
    assert np.all(np.isfinite(values))

  def test_2d_ten_p2(self):
    data = pg.GData(GEN_DIR / "2d_mt_p2.gkyl")
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 25)
    np.testing.assert_array_equal(values.shape, (24, 24, 1))
    assert np.all(np.isfinite(values))

  def test_2d_mo_p1(self):
    data = pg.GData(GEN_DIR / "2d_mo_p1.gkyl")
    dg = pg.GInterpModal(data)
    _, values = dg.interpolate()
    np.testing.assert_array_equal(values.shape, (16, 16, 1))
    assert np.all(np.isfinite(values))

  def test_2d_mo_p2(self):
    data = pg.GData(GEN_DIR / "2d_mo_p2.gkyl")
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 25)
    np.testing.assert_array_equal(values.shape, (24, 24, 1))
    assert np.all(np.isfinite(values))

  def test_3d_ser_p1(self):
    data = pg.GData(GEN_DIR / "3d_ms_p1.gkyl")
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_equal(len(grid[0]), 9)        # 4*(1+1)+1
    np.testing.assert_array_equal(values.shape, (8, 8, 8, 1))
    assert np.all(np.isfinite(values))

  def test_num_interp_override(self):
    """Custom num_interp should scale output nodes independently of poly_order."""
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl")
    dg = pg.GInterpModal(data, num_interp=4)
    _, values = dg.interpolate()
    np.testing.assert_array_equal(values.shape, (32, 32, 1))  # 8*4


class TestGeneratedC2PInterpolate:
  """Tests for c2p (computational-to-physical coordinate) mapped interpolation.

  Each test pairs a generated field file with a generated c2p mapping file.
  C2P mapping files store modal DG coefficients for analytical coordinate
  transformations; the basis is inferred from num_comps/ndim by GData.

  Two mapping types are covered:
    stretch   - linear scaling of each dimension independently
    rotation  - 2D rotation by 45 degrees (verifiable corner values)
  """

  # ------------------------------------------------------------------ stretch

  def test_stretch_p1_grid_type(self):
    """Loading a c2p file sets ctx['grid_type'] = 'c2p'."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl",
    )
    assert data.ctx["grid_type"] == "c2p"
    # Grid before interpolation holds DG coefficients, shape (N_x, N_y, nc)
    np.testing.assert_array_equal(data.get_grid()[0].shape, (8, 8, 4))
    np.testing.assert_array_equal(data.get_grid()[1].shape, (8, 8, 4))

  def test_stretch_p1_output_shape(self):
    """After interpolation the physical grid has shape (N*num_interp+1, ..., 1)."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    # p=1 → num_interp=2; 8 cells × 2 + 1 = 17 nodes per dim
    np.testing.assert_array_equal(grid[0].shape, (17, 17))
    np.testing.assert_array_equal(grid[1].shape, (17, 17))
    np.testing.assert_array_equal(values.shape, (16, 16, 1))

  def test_stretch_p1_physical_bounds(self):
    """Physical grid must span exactly the mapped domain [0,2] × [0,3]."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, _ = dg.interpolate()
    assert abs(grid[0].min()) < 1e-10
    np.testing.assert_approx_equal(grid[0].max(), 2.0)
    assert abs(grid[1].min()) < 1e-10
    np.testing.assert_approx_equal(grid[1].max(), 3.0)

  def test_stretch_p1_grid_is_separable(self):
    """For a stretch-only mapping x depends only on i and y only on j."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, _ = dg.interpolate()
    # x = f(xi) only: all values in a row must be equal (zero variation along eta)
    np.testing.assert_allclose(np.std(grid[0], axis=1), 0.0, atol=1e-12)
    # y = f(eta) only: all values in a column must be equal (zero variation along xi)
    np.testing.assert_allclose(np.std(grid[1], axis=0), 0.0, atol=1e-12)

  def test_stretch_p2_physical_bounds(self):
    """p=2 linear c2p mapping: physical bounds remain [0,2] × [0,3]."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p2.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_stretch_ms_p2.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    assert abs(grid[0].min()) < 1e-10
    np.testing.assert_approx_equal(grid[0].max(), 2.0)
    assert abs(grid[1].min()) < 1e-10
    np.testing.assert_approx_equal(grid[1].max(), 3.0)
    assert np.all(np.isfinite(values))

  def test_stretch_p2_output_shape(self):
    """p=2 → num_interp=3; 8 cells × 3 + 1 = 25 nodes per dim."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p2.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_stretch_ms_p2.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, values = dg.interpolate()
    np.testing.assert_array_equal(grid[0].shape, (25, 25))
    np.testing.assert_array_equal(values.shape, (24, 24, 1))

  # ------------------------------------------------------------------ rotation

  def test_rotation_grid_type_and_shape(self):
    """Rotation c2p: grid_type='c2p', grid has DG-coeff shape before interpolation."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_rot45_ms_p1.gkyl",
    )
    assert data.ctx["grid_type"] == "c2p"
    np.testing.assert_array_equal(data.get_grid()[0].shape, (8, 8, 4))

  def test_rotation_corner_origin(self):
    """The (0,0) corner of the computational domain maps to the physical origin."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_rot45_ms_p1.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, _ = dg.interpolate()
    assert abs(grid[0][0, 0]) < 1e-10
    assert abs(grid[1][0, 0]) < 1e-10

  def test_rotation_corners_45deg(self):
    """Corners of the unit comp square rotate exactly to known physical positions.

    With 45° rotation:
      (xi=1, eta=0) → (1/√2,  1/√2)
      (xi=0, eta=1) → (-1/√2, 1/√2)
      (xi=1, eta=1) → (0,     √2)
    """
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_rot45_ms_p1.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, _ = dg.interpolate()
    inv2 = 1.0 / np.sqrt(2)
    np.testing.assert_approx_equal(grid[0][-1,  0], inv2,  significant=10)
    np.testing.assert_approx_equal(grid[1][-1,  0], inv2,  significant=10)
    np.testing.assert_approx_equal(grid[0][ 0, -1], -inv2, significant=10)
    np.testing.assert_approx_equal(grid[1][ 0, -1], inv2,  significant=10)
    assert abs(grid[0][-1, -1]) < 1e-10
    np.testing.assert_approx_equal(grid[1][-1, -1], np.sqrt(2), significant=10)

  def test_rotation_preserves_distances(self):
    """Rotation is an isometry: distance between opposite corners = √2."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_rot45_ms_p1.gkyl",
    )
    dg = pg.GInterpModal(data)
    grid, _ = dg.interpolate()
    dx = grid[0][-1, -1] - grid[0][0, 0]
    dy = grid[1][-1, -1] - grid[1][0, 0]
    dist = np.sqrt(dx**2 + dy**2)
    np.testing.assert_approx_equal(dist, np.sqrt(2), significant=10)

  def test_rotation_values_finite(self):
    """Interpolated field values are finite when using a rotation c2p mapping."""
    data = pg.GData(
        GEN_DIR / "2d_ms_p1.gkyl",
        mapc2p_name=GEN_DIR / "2d_c2p_rot45_ms_p1.gkyl",
    )
    dg = pg.GInterpModal(data)
    _, values = dg.interpolate()
    assert np.all(np.isfinite(values))
    np.testing.assert_array_equal(values.shape, (16, 16, 1))
