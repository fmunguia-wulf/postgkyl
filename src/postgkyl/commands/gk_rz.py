import click
import numpy as np

from postgkyl.data import GData, GInterpModal
from postgkyl.utils import verb_print
import postgkyl.utils.gk_utils as gku


def _interp(gdat, comp=0):
  """Interpolate component 'comp' of the DG GData object 'gdat'.

  Returns the computational grid (list of 1D node arrays) and the
  interpolated values at fine cell centers.
  """
  poly_order = gdat.ctx["poly_order"]
  basis_type = gdat.ctx["basis_type"]
  if basis_type == "serendipity":
    basis_type = "ms"
  # end
  grid, vals = GInterpModal(gdat, poly_order, basis_type).interpolate(comp)
  return [np.squeeze(g) for g in grid], np.squeeze(vals)

@click.command()
@click.option("--mapc2p", "-n", required=True, type=click.STRING,
  help="Path to the mapc2p.gkyl file with computational to physical coordinate mapping.")
@click.option("--use", "-u", default=None,
  help="Specify tag of datasets to process from the stack.")
@click.option("--tag", "-t", default="rz", type=click.STRING,
  help="Tag for output datasets.")
@click.option("--label", "-l", default=None, type=click.STRING,
  help="Custom label for the result.")
@click.pass_context
def gk_rz(ctx, **kwargs):
  """
  \b
  Gyrokinetics: Interpolate DG dataset(s) and map them to the R-Z plane.
  Assumes DG data (not yet interpolated) has been loaded onto the stack by a
  preceding command. 

  """
  data = ctx.obj["data"]

  verb_print(ctx, "Mapping stack data to R-Z using " + kwargs["mapc2p"])

  # Load the mapc2p DG file and interpolate to get physical R, Z at fine cell centers.
  mapc2p_gdat = GData(kwargs["mapc2p"])
  is_mapc2p = gku.is_gdata_geo_mapc2p(mapc2p_gdat)

  if is_mapc2p:
    # Components are Cartesian X, Y, Z: compute R = sqrt(X^2 + Y^2).
    _, X = _interp(mapc2p_gdat, 0)
    _, Y = _interp(mapc2p_gdat, 1)
    _, vertZ = _interp(mapc2p_gdat, 2)
    majorR = np.sqrt(X**2 + Y**2)
  else:
    # Components are directly R, Z, phi.
    _, majorR = _interp(mapc2p_gdat, 0)
    _, vertZ = _interp(mapc2p_gdat, 1)
  # end

  # Interpolate each stack dataset and push it with the R-Z physical grid.
  loaded_count = 0
  for dat in data.iterator(kwargs["use"]):
    _, vals = _interp(dat)
    out = GData(tag=kwargs["tag"], label=kwargs["label"], ctx=dat.ctx)
    out.push([majorR, vertZ], vals[..., np.newaxis])
    data.add(out)
    dat.deactivate()
    loaded_count += 1
  # end

  if loaded_count > 1:
    data.set_unique_labels()
  # end

  verb_print(ctx, "Finishing R-Z mapping.")
