"""
Loading pre-named gyrokinetic quantities.
"""
import glob
import os
from collections.abc import Iterable, Iterator

import click

from postgkyl.data import GData
from postgkyl.utils.gk_quantities.registry import gk_quant_registry, gk_conf_frame_files, gk_geo_files
from postgkyl.utils import verb_print

def _iter_existing_files(stem: str, frames: Iterable[int]) -> Iterator[str]:
  """Create an iterator over files that have the name <stem><frame>.gkyl and exist."""
  for frame in frames:
    file_path = f"{stem}{frame}.gkyl"
    if os.path.isfile(file_path):
      yield file_path

def _get_avail_frames_qfile(path, name, species, qname, **kwargs):
  """
  Create a set of available frames for the file <path><name>-<species>_<qname>_#.gkyl.
  Optional: pass a list of frames to look for in kwargs["frames"].
  """
  frames_avail: set[int] = set()
  if qname in gk_conf_frame_files:
    stem = f"{path}{name}-{qname}_"
  else:
    stem = f"{path}{name}-{species}_{qname}_"

  if kwargs.get('frames'):
    frame_iter = _iter_existing_files(stem, iter(kwargs["frames"]))
  else:
    frame_iter = glob.glob(f"{glob.escape(stem)}*.gkyl")

  for f in frame_iter:
    suffix = f.removeprefix(stem)[:-5]
    if suffix.isdigit():
      frames_avail.add(int(suffix))
    # end
  # end
  return frames_avail

def _get_src_combo_and_frames(path, name, species, qattr, **kwargs):
  """
  Create a set of available frames for the files <path><name>-<species>_<dependency>_#.gkyl
  that the quantity whose attribute dictionary depends on.
  Optional: pass a list of frames to look for in kwargs["frames"].
  """
  frames_avail: set[int] = set()
  combo_idx = 0
  # Check each combination of sources.
  for cidx in range(len(qattr["source"])):
    combo = qattr["source"][cidx]
    # Check each source for this combo.
    for src in combo:
      if isinstance(src, str) and src in gk_geo_files:
        # Geo files have no frame number; just check the file exists.
        if not os.path.isfile(f"{path}{name}-{src}.gkyl"):
          frames_avail: set[int] = set()
          break
        continue

      if isinstance(src, str):
        frames_avail_q = _get_avail_frames_qfile(path, name, species, src, **kwargs)
      else:
        _, frames_avail_q = _get_src_combo_and_frames(path, name, species, src, **kwargs)

      if frames_avail_q == {-1}:
        # Dict source is a geo-only quantity: doesn't constrain frames, just needs to exist.
        combo_idx = cidx
        continue

      if frames_avail_q:
        if not frames_avail:
          frames_avail = frames_avail_q.copy()
        else:
          # Check this has the same frames as previously checked files in this combo.
          # if it doesn't, go to the next combo.
          if not (frames_avail_q == frames_avail):
            frames_avail: set[int] = set()
            break

        combo_idx = cidx
      else:
        break
    else:
      # If all sources were geo files, frames_avail is still empty.
      # Mark the combo as valid with {-1}.
      if not frames_avail:
        frames_avail = {-1}
        combo_idx = cidx

    if frames_avail:
      break

  return combo_idx, frames_avail

def _choose_source(path: str, name: str, species: str, quant_attr: dict, frame_inp: str | None) -> list[int]:
  """Identify source combination and frames needed to get the requested quantity."""

  frame_list = list()
  if frame_inp is not None:
    frame_inp = frame_inp.strip()
    if "," in frame_inp:
      frame_list = [int(f.strip()) for f in frame_inp.split(",")]
    elif ":" not in frame_inp:
      frame_list = [int(frame_inp)]
  # end

  # Discover available frames from any of the possible source combinations.
  combo_idx, frames_avail = _get_src_combo_and_frames(path, name, species, quant_attr, frames=frame_list)

  if not frames_avail:
    raise FileNotFoundError(f"No files found for the requested quantity "
                            f"(path='{path}', name='{name}').")

  # Geo-only quantities have no frame number; return a single None sentinel.
  if frames_avail == {-1}:
    return combo_idx, [None]

  frames_avail_sorted = sorted(frames_avail)
  parts = frame_inp.split(":")
  if len(frame_list) == 0:
    lower = int(parts[0]) if parts[0] else frames_avail_sorted[0]
    upper = int(parts[1]) if parts[1] else frames_avail_sorted[-1] + 1
    step  = int(parts[2]) if len(parts) == 3 and parts[2] else 1
    frame_list = [f for f in frames_avail_sorted if lower <= f < upper and (f - lower) % step == 0]

  return combo_idx, frame_list

def _get_src_gdata_qfile(src: str, path: str, name: str, species: str, frame: int) -> GData:
  """Get the populated GData for a source, assuming it is a string to be incorporated into a file name."""
  if src in gk_geo_files:
    file_name = f"{path}{name}-{src}.gkyl"
  elif src in gk_conf_frame_files:
    file_name = f"{path}{name}-{src}_{frame}.gkyl"
  else:
    file_name = f"{path}{name}-{species}_{src}_{frame}.gkyl"
  return GData(file_name)

def _get_src_gdata_qdict(src, path: str, name: str, species: str, frame: int) -> GData:
  """Get the populated Gdata for a soucce, assuming it is a either a dictionary or a string."""
  if isinstance(src, str):
    return _get_src_gdata_qfile(src, path, name, species, frame)
  else:
    src_combo_idx, _ = _choose_source(path, name, species, src, str(frame))

    src_combo, fetch_func = src["source"][src_combo_idx], src["fetch_func"][src_combo_idx]

    # Loop over sources in combo.
    derived_src_gdata = list()
    for derived_src in src_combo:
      if isinstance(derived_src, str):
        derived_src_gdata.append(_get_src_gdata_qfile(derived_src, path, name, species, frame))
      else:
        derived_src_gdata.append(_get_src_gdata_qdict(derived_src, path, name, species, frame))

    out = fetch_func(derived_src_gdata)
    return out

@click.command(name="gk-load-quantity")
@click.option("--quantity", "-q", required=False, type=click.STRING,
    help="Quantity to plot.")
@click.option("--alist", is_flag=True, default=False,
  help="Print out the list of accepted quantities.")
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
    help="Extra comma-separated key=value pairs of extra commands, e.g. dir=1,mass=0.1. Purpose depends on -q.")
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

  if kwargs['alist']:
    # Print accepted quantities and exit.
    valid = sorted(gk_quant_registry.keys())
    print(f"Available quantities: {', '.join(valid)}.")
    return

  data = ctx.obj["data"]
  verb_print(ctx, f"Loading quantity '{kwargs['quantity']}' for {kwargs['name']}")

  quantity = kwargs["quantity"]

  if quantity not in gk_quant_registry:
    valid = sorted(gk_quant_registry.keys())
    raise ValueError(f"Unknown quantity '{quantity}'. "
                     f"Available quantities: {', '.join(valid)}.")

  quant_attr = gk_quant_registry[quantity]

  # Parse --extra into a dict, auto-converting numeric values.
  user_extra = {}
  if kwargs.get("extra"):
    for pair in kwargs["extra"].split(","):
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

  path = kwargs["path"].rstrip("/") + "/"

  # Determine which source combination and frames to use.
  src_combo_idx, frames = _choose_source(path, kwargs["name"], kwargs["species"], quant_attr, kwargs["frame"])
  src_combo, fetch_func = quant_attr["source"][src_combo_idx], quant_attr["fetch_func"][src_combo_idx]

  verb_print(ctx, f"Will compute: {quantity} using source {src_combo_idx}" )
  verb_print(ctx, f"Frames: {frames}")

  for frame in frames:

    # Load required datasets (sources).
    gdatas = list()
    for src in src_combo:
      if isinstance(src, str):
        gdatas.append(_get_src_gdata_qfile(src, path, kwargs["name"], kwargs["species"], frame))
      else:
        gdatas.append(_get_src_gdata_qdict(src, path, kwargs["name"], kwargs["species"], frame))

    out = fetch_func(gdatas, **user_extra) # Compute quantity.

    # Set label and tag.
    label_tmpl = quant_attr["label"]
    if "%s" in label_tmpl:
      if quantity == "ExB_vel":
        default_label = label_tmpl % str(user_extra["dir"])
      else:
        default_label = label_tmpl % kwargs["species"][0] 
    else:
      default_label = label_tmpl
    # end

    out_label = kwargs["label"] if kwargs["label"] is not None else default_label

    if len(frames) > 1:
      out_label += f" f{frame}"
      
    out.set_tag(kwargs["tag"])
    out.set_label(out_label)

    data.add(out) # Push data to stack.

  verb_print(ctx, f"Finished loading '{quantity}'")

