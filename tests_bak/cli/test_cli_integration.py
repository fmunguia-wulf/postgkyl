"""End-to-end tests for the Typer-based ``pgkyl`` command line.

These drive the *full* CLI through :data:`postgkyl.pgkyl.cli` (the Click command
produced from the Typer app), exercising the chained-command dispatch,
command-name abbreviation, explicit aliases, bare-filename-as-load and the
global option callback implemented by ``PgkylGroup`` in ``pgkyl.py``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import typer

from postgkeyll.pgkyl import cli


DATA = Path(__file__).resolve().parent.parent / "test_data" / "twostream-f-p2.gkyl"
DATA_STR = str(DATA)


def run(args: list[str]):
  """Invoke the CLI like a real shell call, returning the command result.

  ``standalone_mode=False`` makes Click/Typer propagate ``UsageError`` and
  ``Exit`` instead of writing to stderr and calling ``sys.exit``.
  """
  try:
    return cli.main(args=args, prog_name="pgkyl", standalone_mode=False)
  except (SystemExit, typer.Exit):
    return None
  # end


# ---------------------------------------------------------------------------
# Global options / callback
# ---------------------------------------------------------------------------

def test_version(capsys):
  run(["--version"])
  out = capsys.readouterr().out
  assert "Postgkyl" in out
  assert "Spam, egg, sausage, and spam." in out


def test_help(capsys):
  run(["--help"])
  out = capsys.readouterr().out
  assert "Postprocessing" in out


def test_no_args_shows_help(capsys):
  # no_args_is_help → invoking with no command prints help and exits.
  try:
    cli.main(args=[], prog_name="pgkyl", standalone_mode=False)
  except Exception:
    pass
  # end
  out = capsys.readouterr().out
  assert "Usage" in out or "Commands" in out


def test_verbose_flag(capsys):
  run(["-v", "--batch-mode", DATA_STR, "interpolate", "info", "-c"])
  out = capsys.readouterr().out
  # verbose mode emits timestamped progress lines
  assert "Postgkyl running in verbose mode" in out


# ---------------------------------------------------------------------------
# Chained dispatch
# ---------------------------------------------------------------------------

def test_chained_load_interp_info(capsys):
  run(["--batch-mode", DATA_STR, "interpolate", "info", "-c"])
  out = capsys.readouterr().out
  assert "default#0" in out


def test_chained_ev_rpn():
  # file → interp → ev 'f f +' → no exception means the chained stack worked
  run(["--batch-mode", DATA_STR, "interpolate", "ev", "f f +"])


# ---------------------------------------------------------------------------
# Custom get_command: abbreviation, alias, bare filename, errors
# ---------------------------------------------------------------------------

def test_abbreviation_unique(capsys):
  # 'int' is unique enough? No — 'int' matches integrate+interpolate. Use 'interp'.
  run(["--batch-mode", DATA_STR, "interp", "info", "-c"])
  out = capsys.readouterr().out
  assert "default#0" in out


def test_abbreviation_ambiguous_fails():
  with pytest.raises(Exception) as exc:
    cli.main(args=[DATA_STR, "inte"], prog_name="pgkyl", standalone_mode=False)
  # end
  assert "Too many matches" in str(exc.value)


def test_alias_pl(capsys):
  # 'pl' is an explicit alias for 'plot'
  run(["--batch-mode", DATA_STR, "interpolate", "pl", "--no-show"])


def test_bare_filename_is_load(capsys):
  # A bare file name should be treated as an implicit 'load'.
  run(["--batch-mode", DATA_STR, "info", "-c"])
  out = capsys.readouterr().out
  assert "default#0" in out


def test_unknown_command_fails():
  with pytest.raises(Exception) as exc:
    cli.main(args=[DATA_STR, "definitely_not_a_command"], prog_name="pgkyl",
        standalone_mode=False)
  # end
  assert "does not match" in str(exc.value)
