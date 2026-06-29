from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.data import GData, GInterpModal
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
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting Gkyl PKPM")
  data = ctx.obj["data"]

  gf = GData(f"{kwargs['name']:s}-{kwargs['species']:s}_{kwargs['idx']:s}.gkyl")
  gvars = GData(f"{kwargs['name']:s}-{kwargs['species']:s}_pkpm_vars_{kwargs['idx']:s}.gkyl")

  c_dim = gf.get_num_dims() - 1

  GInterpModal(gf, kwargs["poly_order"], "pkpmhyb").interpolate((0, 1), overwrite=True)

  dg_vars = GInterpModal(gvars, kwargs["poly_order"], "ms")
  grid_and_T_m = dg_vars.interpolate(3)
  grid_and_us = dg_vars.interpolate((0, 1, 2))

  ops.laguerre_compose(gf, grid_and_T_m, inplace=True)
  ops.transform_frame(gf, grid_and_us, cdim=c_dim, inplace=True)

  gf.set_tag(kwargs["tag"])
  gf.set_label(kwargs["label"])
  data.add(gf)

  verb_print(ctx, "Finishing Gkyl PKPM")
