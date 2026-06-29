import os
import pathlib

import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl._gkylsoft_path import default_config_path


def config(
    gkylsoft: Annotated[Optional[str], typer.Option("--gkylsoft", "-g",
        help="Path to the gkylsoft directory. Uses GKYLSOFT_DIR env variable if not provided.")] = None,
    config_file: Annotated[Optional[str], typer.Option("--config-file", "-c",
        help="Config file to write. Default: ~/.postgkyl/gkylsoft_path, "
             "or the POSTGKYL_CONFIG env variable if set.")] = None,
):
  """Write postgkyl configuration (gkylsoft path) to the config file."""

  if gkylsoft is None:
    gkylsoft = os.environ.get("GKYLSOFT_DIR")

  if gkylsoft is None:
    raise typer.BadParameter("No gkylsoft path provided. Pass --gkylsoft /path/to/gkylsoft "
                           "or set the GKYLSOFT_DIR env variable.")

  out = pathlib.Path(config_file if config_file is not None else default_config_path())
  out.parent.mkdir(parents=True, exist_ok=True)
  out.write_text(f"GKYLSOFT_DIR={gkylsoft}\n")
  typer.echo(f"Wrote gkylsoft path to {out}")
