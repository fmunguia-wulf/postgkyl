import importlib.util
import os
import subprocess
import sys

import click

from postgkyl.utils import verb_print

# src/postgkyl directory (this file lives in src/postgkyl/commands).
_PKG_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Path to the marimo notebook shipped with postgkyl (src/postgkyl/gui/gui.mo.py).
_GUI_NOTEBOOK = os.path.join(_PKG_DIR, "gui", "gui.mo.py")

# Default data directory: the repo's tests/test_data (src/postgkyl -> repo root).
_DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(_PKG_DIR)), "tests", "test_data")


@click.command(help="Launch the postgkyl marimo GUI on a data directory.")
@click.option("--path", "-p", default=_DEFAULT_DATA_DIR, type=click.STRING,
    help="Path to the Gkeyll data directory to open in the GUI "
         "(default: the bundled tests/test_data).")
@click.pass_context
def gui(ctx, **kwargs):
  """Launch the marimo notebook GUI pointed at the given data directory.

  \b
  Example:
    pgkyl gui --path /path/to/my/data
    pgkyl gui -p /path/to/my/data
  """
  if importlib.util.find_spec("marimo") is None:
    click.echo("Marimo not detected in the current environment. "
               "Please install using pip install marimo.")
    ctx.exit(1)

  data_path = os.path.expanduser(kwargs["path"].strip())

  verb_print(ctx, f"Launching marimo GUI ({_GUI_NOTEBOOK}) on '{data_path}'")

  # 'marimo run <notebook> -- <app args>': everything after '--' is forwarded
  # to the notebook and read there via mo.cli_args().
  subprocess.run([sys.executable, "-m", "marimo", "run", _GUI_NOTEBOOK,
                  "--", "--path", data_path])
