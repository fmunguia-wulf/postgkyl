"""``style`` — probe and control the Matplotlib plotting style."""

from __future__ import annotations

import click


@click.command("style")
@click.option("--file", "-f", default=None,
    help="Matplotlib style name (e.g. 'postgkyl', 'dark_background') or .mplstyle file path.")
@click.option("--set", "-s", "set_params", multiple=True,
    help="Set an individual rcParam as 'key:value' (repeatable).")
@click.option("--print", "-p", "print_flag", is_flag=True, default=False,
    help="Print the current rcParams.")
@click.pass_context
def command(ctx, file, set_params, print_flag) -> None:
  """Apply a Matplotlib style and/or set/print individual rcParams."""
  import matplotlib as mpl

  import postgkyl as pg

  if file:
    pg.render.style.apply_style(file)
  # end
  for param in set_params:
    key, _, value = param.partition(":")
    mpl.rcParams[key.strip()] = value.strip()
  # end
  if print_flag:
    for key, value in mpl.rcParams.items():
      click.echo(f"{key} : {value}")
    # end
  # end
