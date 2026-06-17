"""Command and Python API for loading pre-named gyrokinetic quantities.

"""

import glob
import os

import click

from postgkyl.data import GData
from postgkyl.utils.gk_quantities.registry import gk_quant_registry
from postgkyl.utils import verb_print

def choose_file_set(frame_inp: str, name: str, species: str, path: str, quantity: str,) -> list[int]:
  # Identify the set of quantities/files and frames to process in order to get
  # the quantity requested.
  # Returns the a list of quantities and a list of frames to use.

  frame_inp = frame_inp.strip()
  if "," in frame_inp:
    return [int(f.strip()) for f in frame_inp.split(",")]
  # end
  if ":" not in frame_inp:
    return [int(frame_inp)]
  # end

  def append_frame(path, name, species, qname):
    # Create a set of available frames for <path><name>-<species>_<qname>_#.gkyl.
    stem = f"{path}{name}-{species}_{qname}_"
    frames_avail: set[int] = set()
    for f in glob.glob(f"{glob.escape(stem)}*.gkyl"):
      suffix = f.removeprefix(stem)[:-5]
      if suffix.isdigit():
        frames_avail.add(int(suffix))
      # end
    # end
    return frames_avail

  # Range: discover available frames from any of the possible file types
  quant_attr = gk_quant_registry[quantity]
  path = path.rstrip("/") + "/"
  qcombo = list()
  frames_avail: set[int] = set()
  for src in quant_attr["source"]:
    # Check each combination of files.
    for qname in src:
      # Check each file for this quantity.
      frames_avail_q = append_frame(path, name, species, qname)

      if frames_avail_q:
        if qname == src[0]:
          frames_avail = frames_avail_q.copy()
        else:
          # Check this has the same frames as previously checked files in this combo.
          # if it doesn't, go to the next combo.
          if not (frames_avail_q == frames_avail):
            break

        qcombo = src
      else:
        break

  frames_avail_sorted = sorted(frames_avail)
  if not frames_avail_sorted:
    raise FileNotFoundError(f"No frames found for quantity '{quantity}' "
                            f"(name='{name}', species='{species}', path='{path}').")

  parts = frame_inp.split(":")
  lower = int(parts[0]) if parts[0] else frames_avail_sorted[0]
  upper = int(parts[1]) if parts[1] else frames_avail_sorted[-1] + 1
  step  = int(parts[2]) if len(parts) == 3 and parts[2] else 1
  frame_list = [f for f in frames_avail_sorted if lower <= f < upper and (f - lower) % step == 0]
  return frame_list

def load_gk_quantity(quantity: str, species: str, name: str, frame: int, path: str = "./",
  tag: str = "default", label: str | None = None,) -> GData:
  """Load a named gyrokinetic quantity for one frame and return a GData.

  Parameters
  ----------
  quantity : str
      Name of the quantity (e.g. 'n', 'upar', 'Tpar', 'Tperp', 'p').
  species : str
      Species name as used in the file names (e.g. 'ion', 'elc').
  name : str
      Simulation name prefix (e.g. 'gk_sheath_2x2v_p1').
  frame : int
      Frame number.
  path : str
      Directory containing the data files.
  tag : str
      Tag for the returned GData object.
  label : str or None
      Label override; if None the registry default is used (with species inserted).
  """
  if quantity not in gk_quant_registry:
    valid = sorted(gk_quant_registry.keys())
    raise ValueError(f"Unknown quantity '{quantity}'. "
                     f"Available quantities: {', '.join(valid)}.")

  quant_attr = gk_quant_registry[quantity]

  path = path.rstrip("/") + "/"

  for src, fetch_func, scale_func in zip(quant_attr["source"], quant_attr["fetch_func"], quant_attr["scale_func"]):
    file_names = [f"{path}{name}-{species}_{q}_{frame}.gkyl" for q in src]
    if not all(os.path.isfile(f) for f in file_names):
      continue

    gdatas = [GData(f) for f in file_names]
    out = fetch_func(gdatas)
    scale_func(out)

    default_label = quant_attr["label"] % species
    out_label = label if label is not None else default_label

    out.set_tag(tag)
    out.set_label(out_label)
    return out

  # None of the file sets were found.
  tried = ["[" + ", ".join(f"{path}{name}-{species}_{q}_{frame}.gkyl" for q in qs) + "]" for qs in quant_attr["source"]]
  raise FileNotFoundError(f"Could not find files for quantity '{quantity}' (species '{species}', "
                          f"frame {frame}). Tried:\n" + "\n".join(tried))

@click.command(name="gk-load-quantity")
@click.option("--quantity", "-q", required=True, type=click.STRING,
    help="Quantity to plot.")
@click.option("--name", "-n", required=True, type=click.STRING,
    help="Simulation name prefix (e.g. gk_sheath_2x2v_p1).")
@click.option("--species", "-s", required=True, type=click.STRING,
    help="Species name (e.g. ion or elc).")
@click.option("--frame", "-f", required=True, type=click.STRING,
    help="Frame number, comma-separated list, or range 'start:stop[:step]'. "
         "Use ':' for all available frames.")
@click.option("--path", "-p", default="./", type=click.STRING,
    help="Directory containing the simulation files.")
@click.option("--tag", "-t", default="default", type=click.STRING,
    help="Tag for the output dataset.")
@click.option("--label", "-l", default=None, type=click.STRING,
    help="Label override for the output dataset.")
@click.pass_context
def gk_load_quantity(ctx, **kwargs):
  """Gyrokinetics: load a pre-named quantity from simulation output files.

  \b
  Accepted quantities are:
    den, upar, Tpar, Tperp, press

  \b
  Command line example:
    pgkyl gk-load-quantity den -s ion -n gk_sheath_2x2v_p1 -f 9 interp plot

  \b
  Script example:
    from postgkyl.commands.gk_load_quantity import load_gk_quantity
    gdat = load_gk_quantity("n", "ion", "gk_sheath_2x2v_p1", frame=9)
  """
  data = ctx.obj["data"]
  verb_print(ctx, f"Loading quantity '{kwargs['quantity']}' for {kwargs['name']}")

  frames = choose_file_set(kwargs["frame"], kwargs["name"], kwargs["species"],
                           kwargs["path"], kwargs["quantity"])

  verb_print(ctx, f"Frames: {frames}")

  for frame in frames:
    out = load_gk_quantity(quantity=kwargs["quantity"], species=kwargs["species"],
        name=kwargs["name"], frame=frame, path=kwargs["path"], tag=kwargs["tag"],
        label=kwargs["label"])
    data.add(out)

  if len(frames) > 1:
    data.set_unique_labels()

  verb_print(ctx, f"Finished loading '{kwargs['quantity']}'")

