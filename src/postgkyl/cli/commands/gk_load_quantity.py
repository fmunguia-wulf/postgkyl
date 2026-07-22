"""``gk_load_quantity`` -- load a pre-named gyrokinetic quantity by name."""

from __future__ import annotations

import click

import postgkyl as pg

from .._options import label_option, tag_option


@click.command("gk_load_quantity")
@click.option("--quantity", "-q", default=None, help="Registered quantity name.")
@click.option("--qlist", is_flag=True, default=False,
    help="List the available quantities and exit.")
@click.option("--name", "-n", default=None, help="Simulation name prefix.")
@click.option("--species", "-s", default=None,
    help="Species name, or a comma-separated list (species-independent quantities: omit).")
@click.option("--frame", "-f", default=None,
    help="Frame number, comma-separated list, or 'start:stop[:step]' range; default: all.")
@click.option("--path", "-p", default="./", help="Directory containing the simulation files.")
@click.option("--extra", "-e", default=None,
    help="Extra comma-separated key=value pairs of extra commands, e.g. dir=1,mass=0.1. "
         "Purpose depends on -q.")
@tag_option(default="default")
@label_option()
@click.pass_context
def command(ctx, quantity, qlist, name, species, frame, path, extra, tag, label) -> None:
  """Gyrokinetics: load and compute a pre-named quantity by name.

  Use --qlist to print the registered quantity names.
  """
  if qlist:
    click.echo(f"Available quantities: {', '.join(pg.available_gk_quantities())}.")
    return
  # end
  if not quantity or not name:
    raise click.UsageError("gk_load_quantity: --quantity and --name are required (unless --qlist)")
  # end
  datasets = pg.load_gk_quantity(quantity, species, name, frame, path=path,
      tag=tag, label=label, **_parse_extra(extra))
  ctx.obj.datasets.extend(datasets)
# end


def _parse_extra(extra: str | None) -> dict:
  """Parse ``--extra``'s ``key=value,...`` syntax, coercing numeric values."""
  parsed = {}
  for pair in (extra.split(",") if extra else []):
    key, _, val = pair.partition("=")
    key, val = key.strip(), val.strip()
    try:
      val = int(val)
    except ValueError:
      try:
        val = float(val)
      except ValueError:
        pass
      # end
    # end
    parsed[key] = val
  # end
  return parsed
# end
