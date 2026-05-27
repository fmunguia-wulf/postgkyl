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
