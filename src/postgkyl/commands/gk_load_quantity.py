import click

from postgkyl.utils.gk_quantities.registry import gk_quant_registry
from postgkyl.utils import verb_print

def _convert_extra_val(val: str):
  """Convert an --extra value to an int or a float when it looks like one."""
  try:
    return int(val)
  except ValueError:
    try:
      return float(val)
    except ValueError:
      return val

def parse_extra(extra_inp: str | None) -> dict:
  """
  Parse the --extra string into a dict of key/value pairs.

  Values are auto-converted to int/float when possible. A comma-separated value
  that carries no '=' extends the previous key into a list, which is how a
  per-species array is given:

    'dir=1,mass=0.1'        -> {'dir': 1, 'mass': 0.1}
    'mass=1,2,3'            -> {'mass': [1, 2, 3]}
    'mass=1,2,charge=-1,1'  -> {'mass': [1, 2], 'charge': [-1, 1]}

  A key given a single value stays a scalar and applies to every species.
  """
  extra : dict = {}
  if not extra_inp:
    return extra
  # end

  last_key = None
  for token in extra_inp.split(","):
    token = token.strip()
    if not token:
      continue
    # end

    if "=" in token:
      key, _, val = token.partition("=")
      key = key.strip()
      extra[key] = _convert_extra_val(val.strip())
      last_key = key
    elif last_key is None:
      raise ValueError(f"--extra: '{token}' is not a key=value pair and does not follow one. "
                       f"Use e.g. 'mass=1,2,3' to give one value per species.")
    else:
      # A bare value continues the previous key's per-species list.
      if not isinstance(extra[last_key], list):
        extra[last_key] = [extra[last_key]]
      # end
      extra[last_key].append(_convert_extra_val(token))
    # end
  # end

  return extra

@click.command(name="gk-load-quantity")
@click.option("--quantity", "-q", required=False, type=click.STRING,
  help="Quantity to plot.")
@click.option("--qlist", is_flag=True, default=False,
  help="List accepted quantities.")
@click.option("--name", "-n", required=False, type=click.STRING,
  help="Simulation name prefix (e.g. gk_sheath_2x2v_p1).")
@click.option("--species", "-s", required=False, type=click.STRING,
  help="Species name (e.g. ion or elc).")
@click.option("--frame", "-f", required=False, type=click.STRING,
  help="Frame number, comma-separated list, or range 'start:stop[:step]'. "
       "Use ':' for all available frames.")
@click.option("--path", "-p", default="./", type=click.STRING,
  help="Directory containing the simulation files.")
@click.option("--tag", "-t", default="default", type=click.STRING,
  help="Tag for the output dataset.")
@click.option("--label", "-l", default=None, type=click.STRING,
  help="Label override for the output dataset.")
@click.option("--extra", "-e", default=None, type=click.STRING,
  help="Extra comma-separated key=value pairs of extra commands, e.g. dir=1,mass=0.1. "
       "A key may be given one value per species as a comma-separated array, e.g. "
       "mass=me,mi1,mi2 alongside --species elc,ion1,ion2. Purpose depends on -q.")
@click.pass_context
def gk_load_quantity(ctx, **kwargs):
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
  user_extra = parse_extra(kwargs.get('extra'))

  path = kwargs['path'].rstrip("/") + "/"

  # Create species list.
  species_inp = kwargs['species']
  species_list = [s.strip() for s in species_inp.split(",")] if species_inp else [None]

  verb_print(ctx, f"Species: {species_list}")

  if gkquant.is_multi_species:
    # Combine every species into a single dataset (e.g. the sound speed), so it is fetched 
    # once for the whole species list instead of once per species.
    if species_list == [None]:
      raise ValueError(f"Quantity '{gkquant.name}' combines several species, so it needs "
                       f"a species list, e.g. --species elc,ion.")

    src_combo_idx, frames = gkquant.get_avail_source_multi(path, kwargs['name'], species_list, kwargs['frame'])

    verb_print(ctx, f"  {species_list}: will compute {gkquant.name} using source {src_combo_idx}, frames {frames}")

    for frame in frames:
      # Load required datasets (sources) for every species and compute the quantity.
      out = gkquant.fetch_multi(path, kwargs['name'], species_list, frame, src_combo_idx, **user_extra)

      out_label = kwargs['label'] if kwargs['label'] is not None else gkquant.get_label()
      if len(frames) > 1:
        out_label += f" f{frame}"

      out.set_label(out_label)
      out.set_tag(kwargs['tag'])

      data.add(out) # Push data to stack.

    verb_print(ctx, f"Finished loading '{gkquant.name}'")
    return
  
  for species_idx, species in enumerate(species_list):
    # Determine which source combination and frames to use for this species.
    src_combo_idx, frames = gkquant.get_avail_source(path, kwargs['name'], species, kwargs['frame'])

    verb_print(ctx, f"  {species}: will compute {gkquant.name} using source {src_combo_idx}, frames {frames}")

    # Tells the fetch functions which entry of a per-species '--extra' array
    # (e.g. 'mass=1,2,3') applies to the species being computed.
    species_extra = dict(user_extra, species_idx=species_idx)

    for frame in frames:

      # Load required datasets (sources) and compute the quantity.
      out = gkquant.fetch(path, kwargs['name'], species, frame, src_combo_idx, **species_extra)

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

