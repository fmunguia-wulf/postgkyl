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

import glob
import os
import re
import shlex
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

  This class is inherited by ``PgkylSession`` in ``postgkyl.api``. Since 
  ``PgkylSession`` is generated automatically, this class is a space where one 
  can add stable, hand-written features to the session API.
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
    self.cmd_stack = []

  def _run(self, command: click.Command, _files=None, **kwargs):
    """Dispatch a click command against this session's stack.

    ``ctx.invoke`` fills in defaults for any option that is not passed, so the
    generated methods only need to forward their (already defaulted) arguments.

    The equivalent CLI fragment is recorded on ``cmd_stack`` (see
    :meth:`print_cmd`). ``_files`` carries the positional file name(s) for the
    ``load`` command, which on the command line are named directly rather than
    via a ``load`` keyword.
    """
    self.cmd_stack.append(self._format_command(command, kwargs, files=_files))
    return self.ctx.invoke(command, **kwargs)

  @staticmethod
  def _long_opt(opts) -> str:
    """Pick the most readable CLI flag for a parameter (prefer the long form)."""
    long = [o for o in opts if o.startswith("--")]
    return max(long or opts, key=len)

  def _format_command(self, command: click.Command, kwargs: dict, files=None) -> str:
    """Render one command as the CLI fragment that reproduces it.

    Only options whose value differs from the command default are emitted, so
    the result matches what a user would actually type rather than spelling out
    every defaulted option the generated methods forward.
    """
    # ``load`` is triggered on the CLI by naming the file(s) directly; there is
    # no ``load`` token. Every other command is named explicitly.
    tokens = [shlex.quote(f) for f in files] if files is not None else [command.name]

    for param in command.params:
      if param.name == "help" or param.name not in kwargs:
        continue
      value = kwargs[param.name]
      default = param.default
      # click >=8.2 marks "no default given" with a Sentinel; treat as None.
      if repr(default).startswith("Sentinel"):
        default = None

      if getattr(param, "is_flag", False):
        secondary = getattr(param, "secondary_opts", [])
        if default is True and secondary:
          # Toggle flag that defaults on (e.g. --show/--no-show); only the
          # off-switch is worth printing.
          if value is False:
            tokens.append(self._long_opt(secondary))
        elif value:
          tokens.append(self._long_opt(param.opts))
        continue

      if value is None or value == default:
        continue

      opt = self._long_opt(param.opts)
      if getattr(param, "multiple", False) or getattr(param, "nargs", 1) == -1:
        for item in value:
          tokens.append(f"{opt} {shlex.quote(str(item))}")
      else:
        tokens.append(f"{opt} {shlex.quote(str(value))}")

    return " ".join(tokens)

  def get_cmd(self) -> str:
    """Return the pgkyl CLI command equivalent to this session so far."""
    parts = ["pgkyl"]
    if self.ctx.obj.get("verbose"):
      parts.append("--verbose")
    if self.ctx.obj.get("batch_mode"):
      parts.append("--batch-mode")
    parts.extend(self.cmd_stack)
    return " ".join(parts)

  def print_cmd(self) -> str:
    """Print the pgkyl CLI command equivalent to this session.

    Reconstructs the chained command line that would reproduce every command run
    on this session so far, e.g. after::

        pg.load("file.gkyl")
        pg.gk_rz(phi_tor=0.0)
        pg.plot(fixaspect=True)

    ``pg.print_cmd()`` prints ``pgkyl file.gkyl gk-rz --fix-aspect``.
    """
    print(self.get_cmd())

  def load(self, *files: str, **kwargs):
    """Load one or more Gkeyll files onto the stack.

    This is the Python counterpart of naming files on the pgkyl command line.
    Any additional keyword arguments are forwarded to the ``load`` command
    (e.g. ``tag``, ``label``, ``mapc2p_name``).

    Args:
      files: One or more paths to Gkeyll output files. e.g.
          ``pg.load("file1.gkyl", "file2.gkyl")``
    """
    self.ctx.obj["in_data_strings"].extend(files)
    # The ``load`` command loads a single file per invocation (it consumes one
    # entry of ``in_data_strings`` and advances the counter), mirroring how each
    # file on the CLI triggers its own ``load`` call. Invoke it once per file.
    result = None
    for f in files:
      result = self._run(cmd.load, _files=(f,), **kwargs)
    return result
  
  def get_framelist(self, name: str, simprefix: str, path: str = ".") -> list[int]:
    """List the available frame numbers for a given output in a directory.

    Scans ``path`` for files named ``{simprefix}-{name}_{frame}.gkyl`` and
    returns the sorted frame numbers. For example, files
    ``rt_gk_alfven_1x2v-apar_0.gkyl``, ``..._1.gkyl``, ``..._2.gkyl`` yield
    ``[0, 1, 2]``.

    Args:
      name: The output name (e.g. ``"apar"``).
      simprefix: The simulation prefix (e.g. ``"rt_gk_alfven_1x2v"``).
      path: The directory to search (default is the current directory).

    Returns:
      The sorted list of frame numbers found for the specified output.
    """
    pattern = os.path.join(path, f"{simprefix}-{name}_*.gkyl")
    regex = re.compile(rf"{re.escape(simprefix)}-{re.escape(name)}_(\d+)\.gkyl$")
    frames = []
    for fn in glob.glob(pattern):
      match = regex.search(os.path.basename(fn))
      if match:
        frames.append(int(match.group(1)))
    return sorted(frames)



  @property
  def data(self) -> DataSpace:
    """The ``DataSpace`` stack holding all loaded/processed datasets."""
    return self.ctx.obj["data"]
