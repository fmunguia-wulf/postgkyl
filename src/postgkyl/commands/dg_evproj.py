import click

from postgkyl.data import select as pgkyl_select
from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops
from postgkyl.utils import verb_print

@click.command(name="dg-evproj")
@click.option("--z0", default=None, type=float,
    help="Physical coord to evaluate in direction 0.")
@click.option("--z1", default=None, type=float,
    help="Physical coord to evaluate in direction 1.")
@click.option("--z2", default=None, type=float,
    help="Physical coord to evaluate in direction 2.")
@click.option("--z3", default=None, type=float,
    help="Physical coord to evaluate in direction 3.")
@click.option("--z4", default=None, type=float,
    help="Physical coord to evaluate in direction 4.")
@click.option("--z5", default=None, type=float,
    help="Physical coord to evaluate in direction 5.")
@click.option("--comp", "-c", default=None,
    help="Component index to select from the result (int or slice).")
@click.option("--use", "-u", help="Tag to apply to. [default: all active]")
@click.option("--tag", "-t", help="Tag for the output dataset.")
@click.option("--label", "-l", help="Label for the output dataset.")
@click.pass_context
def dg_evproj(ctx, **kwargs):
  """
  Evaluate a DG field at specified coordinates and project onto a lower-dimensional basis.

  Coordinates specified with --z0, --z1, ... --z5.
  """
  verb_print(ctx, "Starting dg-evproj")
  data = ctx.obj["data"]

  z_opts      = [kwargs["z0"], kwargs["z1"], kwargs["z2"],
                 kwargs["z3"], kwargs["z4"], kwargs["z5"]]
  eval_dirs   = [i for i, z in enumerate(z_opts) if z is not None]
  eval_coords = [z_opts[i] for i in eval_dirs]

  if not eval_dirs:
    ctx.fail("dg-evproj requires at least one --z0 ... --z5 coordinate.")

  ops = GkeyllDGops()

  for dat in data.iterator(kwargs["use"]):
    out = ops.eval_at_coord_proj(eval_dirs, eval_coords, dat,
                                 comp_grid=ctx.obj["compgrid"])
    if kwargs["tag"]:
      out.set_tag(kwargs["tag"])
    if kwargs["label"]:
      out.set_label(kwargs["label"])

    if kwargs["comp"] is not None:
      pgkyl_select(out, overwrite=True, comp=kwargs["comp"])

    dat.deactivate()

    data.add(out)
  verb_print(ctx, "Finishing dg-evproj")
