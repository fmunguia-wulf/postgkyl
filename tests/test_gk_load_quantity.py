"""Postgkyl module for testing the gk-load-quantity command.

This exercises ``gk_load_quantity`` against *every* quantity registered in
``gk_quant_registry``. Because the on-disk .gkyl writer does not persist the DG
metadata (poly_order, basis_type, mass) needed by the fetch functions, the test
does not rely on real simulation output. Instead it

  1. creates empty marker files with the exact names each quantity's sources are
     discovered by (so ``choose_source`` finds a valid source combination), and
  2. monkeypatches the ``GData`` constructor used inside ``gkquantity`` so that
     loading a source returns a small, self-consistent synthetic DG dataset.

The fetch functions (and their gkylsoft-backed DG operators) then run for real.
Quantities whose computation requires the compiled gkylsoft library are skipped
when that library is unavailable.
"""
import os

import click
import numpy as np
import pytest

import postgkyl.commands as cmd
import postgkyl.utils.gk_quantities.gkquantity as gkquantity
from postgkyl.data import GData
from postgkyl.pgkyl import cli
from postgkyl.utils.gk_quantities.registry import gk_quant_registry

# Synthetic DG dataset parameters: 1D, p1 serendipity (num_basis = 2), four
# physical components so that fetch functions selecting up to component 3 work.
_POLY_ORDER = 1
_BASIS_TYPE = "serendipity"
_NUM_BASIS = 2
_NUM_PHYS_COMPS = 4
_NUM_CELLS = 4

# Probe whether the gkylsoft DG-operator library is available. Quantities whose
# fetch functions use it (e.g. press, beta, ExB_vel) are skipped if it is not.
try:
  from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops
  GkeyllDGops()
  _DGOPS_AVAILABLE = True
except Exception:  # noqa: BLE001 - any failure means the lib is unusable here
  _DGOPS_AVAILABLE = False

# Extra command options required by specific quantities (beyond the per-component
# selection that every vector quantity needs, which is added automatically below).
# The ion mass is not a species' own file attribute, so c_s (and everything
# normalized by it) must be given one explicitly.
_EXTRA_OPTS = {
  "c_s": "mass_i=1.0",
  "qpar_norm": "mass_i=1.0",
  "qperp_norm": "mass_i=1.0",
  "qpar_fluid_norm": "mass_i=1.0",
  "qperp_fluid_norm": "mass_i=1.0",
}

# Define the data used to test the handling of GK distribution functions.
_TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
_DISTF_REAL = {
  "name": "rt_gk_tcv_iwl_1x2v_p1",
  "species": "elc",
  "frame": 250,
}


def _extra_opts_for(quant) -> str | None:
  """Build the '--extra' string a quantity needs to be fetched in the test."""
  opts = []
  if quant.is_vector:
    opts.append("dir=0")  # Vector quantities need a component selection.
  if quant.name in _EXTRA_OPTS:
    opts.append(_EXTRA_OPTS[quant.name])
  return ",".join(opts) if opts else None


def _make_synthetic_gdata(*args, **kwargs) -> GData:
  """Return a small, self-consistent constant-valued DG dataset.

  Each physical component is a positive constant (only the cell-average modal
  coefficient is nonzero), which keeps the DG multiply/invert operations
  well-defined. The filename argument is ignored on purpose - every source is
  served the same synthetic data, which is enough to drive the fetch functions.
  """
  values = np.zeros((_NUM_CELLS, _NUM_BASIS * _NUM_PHYS_COMPS))
  for comp in range(_NUM_PHYS_COMPS):
    # Distinct positive cell-average per component (1/sqrt(2) is the value of
    # the 0th modal serendipity basis function).
    values[:, comp * _NUM_BASIS] = (comp + 2) * np.sqrt(2.0)

  grid = [np.linspace(0.0, 1.0, _NUM_CELLS + 1)]
  gdata = GData(ctx={"poly_order": _POLY_ORDER, "basis_type": _BASIS_TYPE,
                     "mass": 1.0, "charge": 1.0})
  gdata.push(grid, values)
  return gdata


def _collect_source_files(quant, path: str, name: str, species: str, frame: int) -> set[str]:
  """Recursively collect the file names every source combination would look for."""
  files: set[str] = set()
  for combo in quant.source:
    for src in combo:
      if isinstance(src, str):
        files.add(quant._src_file_name(path, name, species, src, frame))
      else:
        files |= _collect_source_files(src, path, name, species, frame)
  return files


class TestGkLoadQuantity:
  """Test that gk-load-quantity can load every registered quantity."""

  name = "gktest"
  species = "ion"
  frame = 0

  def _make_ctx(self):
    ctx = click.core.Context(cli)
    ctx.obj = {"data": cmd.DataSpace(), "verbose": False}
    return ctx

  @pytest.mark.parametrize("quantity", gk_quant_registry.list())
  def test_load_quantity(self, quantity, tmp_path, monkeypatch):
    if quantity == "distf":
      self._check_distf_real()
      return

    quant = gk_quant_registry.get(quantity)
    path = str(tmp_path)

    # Create empty marker files for every source so source discovery succeeds.
    for file_name in _collect_source_files(quant, path, self.name, self.species, self.frame):
      open(file_name, "w").close()

    # Serve synthetic DG data whenever a source file is "loaded".
    monkeypatch.setattr(gkquantity, "GData", _make_synthetic_gdata)

    ctx = self._make_ctx()
    try:
      ctx.invoke(
        cmd.gk_load_quantity,
        quantity=quantity,
        name=self.name,
        species=self.species,
        frame=str(self.frame),
        path=path,
        extra=_extra_opts_for(quant),
      )
    except (RuntimeError, FileNotFoundError, OSError) as err:
      if not _DGOPS_AVAILABLE:
        pytest.skip(f"'{quantity}' requires the gkylsoft DG library: {err}")
      raise

    assert ctx.obj["data"].get_num_datasets() >= 1, (
      f"gk-load-quantity produced no dataset for quantity '{quantity}'")

  def _check_distf_real(self):
    """
    Test the distf function with real data present in the test_data directory.
    """
    ctx = self._make_ctx()
    try:
      ctx.invoke(
        cmd.gk_load_quantity,
        quantity="distf",
        name=_DISTF_REAL["name"],
        species=_DISTF_REAL["species"],
        frame=str(_DISTF_REAL["frame"]),
        path=_TEST_DATA_DIR,
      )
    except (RuntimeError, FileNotFoundError, OSError) as err:
      if not _DGOPS_AVAILABLE:
        pytest.skip(f"'distf' requires the gkylsoft DG library: {err}")
      raise

    assert ctx.obj["data"].get_num_datasets() >= 1, (
      "gk-load-quantity produced no dataset for quantity 'distf'")
