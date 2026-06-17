"""High-level, scriptable interface to the pgkyl command chain.

The pgkyl command line (e.g. ``pgkyl file.gkyl gk-rz pl``) is a chain of click
commands operating on a shared dataset stack. This module exposes that same
chain to Python/Jupyter as a stateful session object so each command can be
called as a typed method:

    from postgkyl.api import PgkylSession
    pg = PgkylSession()
    pg.load("file.gkyl")
    pg.gk_rz(phi_tor=0.0)
    pg.plot(fixaspect=True)

The typed methods themselves live in the generated ``postgkyl.api`` module; this
file holds the stable runtime core they build on. See ``postgkyl._api_gen`` for
the generator that keeps ``api.py`` in sync with the click commands.
"""

import os
import time

import click

import postgkyl.commands as cmd
import postgkyl.output
from postgkyl.commands import DataSpace
from postgkyl.pgkyl import cli
from postgkyl.utils import load_style


class _Session:
  """Stateful pgkyl stack; the Python equivalent of one CLI invocation.

  Datasets loaded and processed by the command methods accumulate on an internal
  stack (a ``DataSpace``), exactly as they would when chaining commands on the
  command line. Drop to ``session.data`` to reach the underlying ``GData``
  objects and their raw NumPy arrays.
  """

  def __init__(self, verbose: bool = False, batch_mode: bool = False,
      style: str | None = None):
    """Initialize an empty session.

    Args:
      verbose: Turn on pgkyl verbose output.
      batch_mode: Run in batch mode (no plots are shown).
      style: Path to a Matplotlib style file (defaults to the pgkyl style).
    """
    self.ctx = click.Context(cli)
    self.ctx.obj = {
        "start_time": time.time(),
        "verbose": verbose,
        "batch_mode": batch_mode,
        "saveframes_prefix": os.path.expanduser("~") + "/pg",
        "in_data_strings": [],
        "in_data_strings_loaded": 0,
        "data": DataSpace(),
        "fig": "",
        "ax": "",
        "compgrid": False,
        "global_var_names": (),
        "global_cuts": (None,) * 7,
        "global_c2p": None,
        "global_c2p_vel": None,
        "rcParams": {},
    }
    style_file = style or os.path.join(
        os.path.dirname(postgkyl.output.__file__), "postgkyl.mplstyle")
    load_style(self.ctx, style_file)

  def _run(self, command: click.Command, **kwargs):
    """Dispatch a click command against this session's stack.

    ``ctx.invoke`` fills in defaults for any option that is not passed, so the
    generated methods only need to forward their (already defaulted) arguments.
    """
    return self.ctx.invoke(command, **kwargs)

  def load(self, *files: str, **kwargs):
    """Load one or more Gkeyll files onto the stack.

    This is the Python counterpart of naming files on the pgkyl command line.
    Any additional keyword arguments are forwarded to the ``load`` command
    (e.g. ``tag``, ``label``, ``mapc2p_name``).

    Args:
      files: One or more paths to Gkeyll output files.
    """
    self.ctx.obj["in_data_strings"].extend(files)
    return self._run(cmd.load, **kwargs)

  @property
  def data(self) -> DataSpace:
    """The ``DataSpace`` stack holding all loaded/processed datasets."""
    return self.ctx.obj["data"]
