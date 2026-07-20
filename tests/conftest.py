"""Shared pytest configuration for the postgkyl test suite.

No-GUI guarantee
-----------------
This test session must never put a window or a browser tab on the desktop --
doing so can crash/hang the sandboxed environment this suite runs in. Two
independent guards enforce that, both applied before any test module (or its
imports) can run:

- ``matplotlib.use("Agg")`` is forced at import time, below, before anything
  else gets a chance to trigger Matplotlib's own backend auto-detection
  (which, given a display, could pick an interactive GUI backend). Agg is a
  pure-raster, no-window backend, so ``plt.show()`` is always a no-op under it.
- ``_block_gui_popups`` (autouse, session-scoped) monkeypatches
  ``webbrowser.open`` -- the mechanism ``render.plotly``'s ``open_preview``
  (default-off; see its docstring) uses to show a Plotly figure -- and, if
  PyVista is installed, ``pyvista.Plotter.show`` -- the analogous mechanism
  for a PyVista render window (default-off there too; see
  ``render.pyvista.pyvista``'s ``show`` parameter). Both render functions
  already default their own ``show`` to ``False`` for exactly this reason;
  this fixture is the backstop for any call (present or future) that forgets
  to pass ``show=False`` explicitly.

Session fixture
---------------
``generated_test_data`` runs once per pytest session and writes synthetic
.gkyl files to ``tests/test_data/generated/`` (gitignored — every test that
reads from that directory depends on this fixture via autouse). Without it,
a clean checkout (e.g. CI) has no fixtures to read; only a machine where
someone has run ``python tests/generate_test_data.py`` (or a prior pytest
session) before would happen to have them already on disk.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pytest

from generate_test_data import generate_all

GEN_DIR = Path(__file__).parent / "test_data" / "generated"


@pytest.fixture(scope="session", autouse=True)
def _block_gui_popups():
  """Backstop: no test may open a browser tab or a native render window."""
  import webbrowser

  def _no_browser(*_args, **_kwargs):
    raise AssertionError(
        "webbrowser.open() was called during tests -- a figure/preview would "
        "have popped up on the desktop. Pass show=False (render.plotly's/"
        "render.pyvista's default) or mock the call being tested.")
  # end

  webbrowser.open = _no_browser
  webbrowser.open_new = _no_browser
  webbrowser.open_new_tab = _no_browser

  try:
    import pyvista

    def _no_plotter_show(*_args, **_kwargs):
      raise AssertionError(
          "pyvista.Plotter.show() was called during tests -- a render window "
          "would have popped up on the desktop. Pass show=False (the default) "
          "or mock the call being tested.")
    # end
    pyvista.Plotter.show = _no_plotter_show
  # end
  except ImportError:
    pass
  # end
# end


@pytest.fixture(scope="session", autouse=True)
def generated_test_data():
  """Write synthetic .gkyl test files before any test runs."""
  generate_all(GEN_DIR)
  return GEN_DIR
# end
