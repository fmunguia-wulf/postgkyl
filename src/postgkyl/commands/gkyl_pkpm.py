from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl.gk.pkpm import load_pkpm
from postgkyl.utils import verb_print


def pkpm(
    ctx: typer.Context,
    name: Annotated[Optional[str], typer.Option("--name", "-n", prompt=True, help="Set the root name for files.")] = None,
    species: Annotated[Optional[str], typer.Option("--species", "-s", prompt=True, help="Set species name.")] = None,
    idx: Annotated[Optional[str], typer.Option("--idx", "-i", prompt=True, help="Set the file number.")] = None,
    poly_order: Annotated[Optional[int], typer.Option("--poly_order", "-p", prompt=True, help="Set the polynomial order.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
):
  """Shortcut to load Gkeyll PKPM data, interpolate, and transform."""
  verb_print(ctx, "Starting Gkyl PKPM")
  gf = load_pkpm(name, species, idx, poly_order, tag=tag, label=label)
  ctx.obj["data"].add(gf)
  verb_print(ctx, "Finishing Gkyl PKPM")
