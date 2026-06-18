"""Tests for the high-level scriptable pgkyl API (``postgkyl.api``)."""
import os

import postgkyl as pg
from postgkyl.api import _api_gen


class TestApiGeneration:
  """The generated ``api.py`` must stay in sync with the click commands."""

  def test_api_in_sync(self):
    path = _api_gen._target_path()
    with open(path, "r") as fh:
      current = fh.read()
    assert current == _api_gen.render(), (
        "postgkyl/api/api.py is stale; run 'python -m postgkyl.api._api_gen'.")


class TestApiSession:
  """The session methods mirror the command chain on a shared stack."""
  dir_path = f"{os.path.dirname(__file__)}/test_data"

  def test_load_interp_chain(self):
    session = pg.PgkylSession(batch_mode=True)
    session.load(f"{self.dir_path:s}/shock-f-ser-p1.gkyl")
    session.interpolate(basis_type="ms", poly_order=1)
    assert session.data.get_num_datasets() == 1
