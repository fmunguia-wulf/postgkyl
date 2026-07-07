import os

import click

from postgkyl.data import GData
from postgkyl.data import select as pgkyl_select
from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops
from postgkyl.utils import verb_print


def _jacobgeo_path(file_name):
  """Return the <prefix>-geo_int_jacobgeo.gkyl path next to file_name, or None."""
  if not file_name:
    return None
  dirname  = os.path.dirname(file_name)
  basename = os.path.basename(file_name)
  prefix   = basename.split("-")[0]
  return os.path.join(dirname, f"{prefix}-geo_int_jacobgeo.gkyl")


@click.command(name="dg-evproj")
@click.option("--z0", default=None, type=str,
    help="Physical coord to evaluate in direction 0, or 'avg' to average over it.")
@click.option("--z1", default=None, type=str,
    help="Physical coord to evaluate in direction 1, or 'avg' to average over it.")
@click.option("--z2", default=None, type=str,
    help="Physical coord to evaluate in direction 2, or 'avg' to average over it.")
@click.option("--z3", default=None, type=str,
    help="Physical coord to evaluate in direction 3, or 'avg' to average over it.")
@click.option("--z4", default=None, type=str,
    help="Physical coord to evaluate in direction 4, or 'avg' to average over it.")
@click.option("--z5", default=None, type=str,
    help="Physical coord to evaluate in direction 5, or 'avg' to average over it.")
@click.option("--comp", "-c", default=None,
    help="Component index to select from the result (int or slice).")
@click.option("--weight", "-w", default=None,
    help="Weight file for the average. Defaults to <prefix>-geo_int_jacobgeo.gkyl "
         "found next to the dataset; pass a path to override, or 'none' to disable.")
@click.option("--use", "-u", help="Tag to apply to. [default: all active]")
@click.option("--tag", "-t", help="Tag for the output dataset.")
@click.option("--label", "-l", help="Label for the output dataset.")
@click.pass_context
def dg_evproj(ctx, **kwargs):
  """
  Evaluate a DG field at specified coordinates and project onto a lower-dimensional basis.

  Coordinates specified with --z0, --z1, ... --z5. Each direction can instead be
  given as 'avg' to average the field over that direction (integral over the
  direction divided by its length). Evaluation and averaging can be combined,
  e.g. --z0 avg --z1 0.5. The output has the same reduced dimensionality whether
  a direction is evaluated at a coordinate or averaged.

  When averaging, the geometric Jacobian <prefix>-geo_int_jacobgeo.gkyl (found
  next to the dataset) is used as the weight if present, giving the weighted
  average int(f J dx) / int(J dx). Override the weight file with --weight, or
  disable weighting with '--weight none'.
  """
  verb_print(ctx, "Starting dg-evproj")
  data = ctx.obj["data"]

  z_opts      = [kwargs["z0"], kwargs["z1"], kwargs["z2"],
                 kwargs["z3"], kwargs["z4"], kwargs["z5"]]
  eval_dirs   = []
  eval_coords = []
  avg_dirs    = []
  for i, z in enumerate(z_opts):
    if z is None:
      continue
    if str(z).strip().lower() in ("avg", "average"):
      avg_dirs.append(i)
    else:
      try:
        eval_coords.append(float(z))
      except ValueError:
        ctx.fail(f"--z{i} must be a number or 'avg', got '{z}'.")
      eval_dirs.append(i)

  if not eval_dirs and not avg_dirs:
    ctx.fail("dg-evproj requires at least one --z0 ... --z5 coordinate or 'avg'.")

  ops = GkeyllDGops()

  weight_opt   = kwargs["weight"]
  weight_off   = weight_opt is not None and str(weight_opt).strip().lower() == "none"
  weight_cache = {}  # file path -> loaded GData (avoid re-reading per dataset)

  def _load_weight(dat):
    """Resolve and load the weight GData for a dataset, or None."""
    if not avg_dirs or weight_off:
      return None
    if weight_opt:  # explicit override: must exist
      path = weight_opt
      if not os.path.isfile(path):
        ctx.fail(f"weight file '{path}' not found.")
    else:  # auto-detect the geometric Jacobian
      path = _jacobgeo_path(dat.get_file_name())
      if path is None or not os.path.isfile(path):
        verb_print(ctx, f"No jacobgeo weight found ({path}); using unweighted average.")
        return None
    if path not in weight_cache:
      verb_print(ctx, f"Loading average weight from {path}")
      weight_cache[path] = GData(file_name=path, comp_grid=ctx.obj["compgrid"])
    return weight_cache[path]

  for dat in data.iterator(kwargs["use"]):
    out = dat
    weight = _load_weight(dat)
    if eval_dirs:
      out = ops.eval_at_coord_proj(eval_dirs, eval_coords, out,
                                   comp_grid=ctx.obj["compgrid"])
      if weight is not None:
        # Reduce the weight the same way so it matches the evaluated field.
        weight = ops.eval_at_coord_proj(eval_dirs, eval_coords, weight,
                                        comp_grid=ctx.obj["compgrid"])
    if avg_dirs:
      # eval_at_coord_proj removed eval_dirs, so shift avg indices into the
      # surviving (reduced) dimension space.
      avg_dirs_red = [d - sum(1 for e in eval_dirs if e < d) for d in avg_dirs]
      out = ops.average(avg_dirs_red, out, weight=weight,
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
