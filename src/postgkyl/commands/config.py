import os
import pathlib

import click

from postgkyl._gkylsoft_path import default_config_path

@click.command(name="config")
@click.option("--gkylsoft", "-g", default=None, type=click.Path(),
  help="Path to the gkylsoft directory. Uses GKYLSOFT_DIR env variable if not provided.")
@click.option("--config-file", "-c", default=None, type=click.Path(),
  help="Config file to write. Default: ~/.postgkyl/gkylsoft_path, "
       "or the POSTGKYL_CONFIG env variable if set.")
def config(gkylsoft, config_file):
  """Write postgkyl configuration (gkylsoft path) to the config file."""

  if gkylsoft is None:
    gkylsoft = os.environ.get("GKYLSOFT_DIR")

  if gkylsoft is None:
    raise click.UsageError("No gkylsoft path provided. Pass --gkylsoft /path/to/gkylsoft "
                           "or set the GKYLSOFT_DIR env variable.")

  out = pathlib.Path(config_file if config_file is not None else default_config_path())
  out.parent.mkdir(parents=True, exist_ok=True)
  out.write_text(f"GKYLSOFT_DIR={gkylsoft}\n")
  click.echo(f"Wrote gkylsoft path to {out}")
