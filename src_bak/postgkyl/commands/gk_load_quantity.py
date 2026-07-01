import typer
from typing import Annotated, Optional

from postgkyl.loaders.gk_quantity import load_gk_quantity, available_quantities
from postgkyl.utils import verb_print

def gk_load_quantity(
    ctx: typer.Context,
    quantity: Annotated[Optional[str], typer.Option("--quantity", "-q", help="Quantity to plot.")] = None,
    qlist: Annotated[bool, typer.Option("--qlist", help="List accepted quantities.")] = False,
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Simulation name prefix (e.g. gk_sheath_2x2v_p1).")] = None,
    species: Annotated[Optional[str], typer.Option("--species", "-s", help="Species name (e.g. ion or elc).")] = None,
    frame: Annotated[Optional[str], typer.Option("--frame", "-f", help="Frame number, comma-separated list, or range 'start:stop[:step]'. Use ':' for all available frames.")] = None,
    path: Annotated[Optional[str], typer.Option("--path", "-p", help="Directory containing the simulation files.")] = "./",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the output dataset.")] = "default",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Label override for the output dataset.")] = None,
    extra: Annotated[Optional[str], typer.Option("--extra", "-e", help="Extra comma-separated key=value pairs of extra commands, e.g. dir=1,mass=0.1. Purpose depends on -q.")] = None,
):
  """
  Gyrokinetics: load a pre-named quantity from simulation output files.

  \b
  For a list of accepted quantities use:
    pgkyl gk-load-quantity --qlist

  \b
  Command line example:
    pgkyl gk-load-quantity den -s ion -n gk_sheath_2x2v_p1 -f 9 interp plot

  \b
  Script example:
    import postgkyl as pg
    gdat = pg.load.gk_quantity("n", "ion", "gk_sheath_2x2v_p1", frame=9)
  """
  if qlist:
    # Print accepted quantities and exit.
    print(f"Available quantities: {', '.join(available_quantities())}.")
    return
  # end

  data = ctx.obj.data
  verb_print(ctx, f"Loading quantity {quantity} for {name}")

  # Parse --extra into a dict, auto-converting numeric values.
  user_extra = {}
  if extra:
    for pair in extra.split(","):
      key, _, val = pair.partition("=")
      key = key.strip()
      val = val.strip()
      try:
        val = int(val)
      except ValueError:
        try:
          val = float(val)
        except ValueError:
          pass
        # end
      # end
      user_extra[key] = val
    # end
  # end

  datasets = load_gk_quantity(quantity, species, name, frame, path=path,
      tag=tag, label=label, log=lambda m: verb_print(ctx, m), **user_extra)
  for out in datasets:
    data.add(out)
  # end

