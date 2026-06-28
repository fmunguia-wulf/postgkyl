import click

from postgkyl import ops
from postgkyl.data import GData, GInterpModal
from postgkyl.utils import verb_print


@click.command()
@click.option("--name", "-n", type=click.STRING, prompt=True, help="Set the root name for files.")
@click.option("--species", "-s", type=click.STRING, prompt=True, help="Set species name.")
@click.option("--idx", "-i", type=click.STRING, prompt=True, help="Set the file number.")
@click.option("--poly_order", "-p", type=click.INT, prompt=True, help="Set the polynomial order.")
@click.option("--tag", "-t", help="Optional tag for the resulting array.")
@click.option("--label", "-l", help="Custom label for the result.")
@click.pass_context
def pkpm(ctx, **kwargs):
  """Shortcut to load Gkeyll PKPM data, interpolate, and transform."""
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
