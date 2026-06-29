import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl.utils.gk_quantities.registry import gk_quant_registry
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
    from postgkyl.commands.gk_load_quantity import load_gk_quantity
    gdat = load_gk_quantity("n", "ion", "gk_sheath_2x2v_p1", frame=9)
  """
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}

  if kwargs['qlist']:
    # Print accepted quantities and exit.
    valid = gk_quant_registry.list()
    print(f"Available quantities: {', '.join(valid)}.")
    return

  data = ctx.obj["data"]
  verb_print(ctx, f"Loading quantity {kwargs['quantity']} for {kwargs['name']}")

  if not gk_quant_registry.has(kwargs['quantity']):
    valid = gk_quant_registry.list()
    raise ValueError(f"Unknown quantity '{kwargs['quantity']}'. "
                     f"Available quantities: {', '.join(valid)}.")

  gkquant = gk_quant_registry.get(kwargs['quantity'])

  # Parse --extra into a dict, auto-converting numeric values.
  user_extra = {}
  if kwargs.get('extra'):
    for pair in kwargs['extra'].split(","):
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
      user_extra[key] = val

  path = kwargs['path'].rstrip("/") + "/"

  # Create species list.
  species_inp = kwargs['species']
  species_list = [s.strip() for s in species_inp.split(",")] if species_inp else [None]

  verb_print(ctx, f"Species: {species_list}")

  for species in species_list:
    # Determine which source combination and frames to use for this species.
    src_combo_idx, frames = gkquant.get_avail_source(path, kwargs['name'], species, kwargs['frame'])

    verb_print(ctx, f"  {species}: will compute {gkquant.name} using source {src_combo_idx}, frames {frames}")

    for frame in frames:

      # Load required datasets (sources) and compute the quantity.
      out = gkquant.fetch(path, kwargs['name'], species, frame, src_combo_idx, **user_extra)

      # Set label.
      default_label = gkquant.get_label(species=species, direction=user_extra.get("dir", None))

      out_label = ''
      if kwargs['label'] is not None:
        out_label = kwargs['label']
        if len(species_list) > 1:
          out_label += f" {species}"
        # end
      else:
        out_label = default_label

      if len(frames) > 1:
        out_label += f" f{frame}"
      # end

      out.set_label(out_label)

      # Set tag.
      out_tag = kwargs['tag']
      if len(species_list) > 1:
        out_tag += f"_{species}"
      # end

      out.set_tag(out_tag)

      data.add(out) # Push data to stack.
    # end frame loop
  # end species loop

  verb_print(ctx, f"Finished loading '{gkquant.name}'")

