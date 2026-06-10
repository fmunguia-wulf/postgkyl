import click
import numpy as np
import os
import re
import glob

from postgkyl.data import GData, GInterpModal
from postgkyl.utils import verb_print
import postgkyl.utils.gk_utils as gku

def get_interp_data_from_gdata(gdata_in, comp_in):
  # Get interpolated data given the GData object.
  poly_order = gdata_in.ctx["poly_order"]
  basis_type = gdata_in.ctx["basis_type"]
  if basis_type == "serendipity":
    basis_type = "ms"
  # end
  pg_interp = GInterpModal(gdata_in, poly_order, basis_type)
  x_out, data_out = pg_interp.interpolate(comp_in)
  for i in range(len(x_out)):
    x_out[i] = np.squeeze(x_out[i])
  # end
  data_out = np.squeeze(data_out)
  return x_out, data_out

@click.command()
@click.option("--quantity", "-q", required=True, type=click.STRING, default=None,
  help="Quantity to plot (a file or one of the default names).")
@click.option("--name", "-n", type=click.STRING, default=None,
  help="Simulation name (also the file prefix, e.g. gk_sheath_1x2v_p1).")
@click.option("--comp", "-c", default=0,
  help="Component in quantity.")
@click.option("--species", "-s", type=click.STRING, default=None,
  help="Species name.")
@click.option("--frame", "-f", type=click.STRING,
  help="Frame number, comma separated values, or range. Use ':' for all frames and 'start:stop[:step]' for ranges.")
@click.option("--path", "-p", type=click.STRING, default='./.',
  help="Path to simulation data.")
@click.option("--multib", "-m", type=click.STRING, is_flag=False, flag_value="-1", default="-10",
  help="Multiblock. Optional: pass block indices as comma-separated list or slice (start:stop:step). If no indices are given, all blocks are used.")
@click.option("--tag", "-t", default="rz", type=click.STRING,
  help="Tag for output dataset.")
@click.option("--label", "-l", default=None, type=click.STRING,
  help="Custom label for the result.")
@click.option("--wall_file", type=click.STRING, default=None,
  help="Vacuum vessel wall (.csv format). [Ignored]")
@click.option("--xlim", default=None, type=click.STRING,
  help="Set limits for the x-coordinate (lower,upper) [Ignored]")
@click.option("--ylim", default=None, type=click.STRING,
  help="Set limits for the y-coordinate (lower,upper). [Ignored]")
@click.option("--xlabel", type=click.STRING, default="R (m)",
  help="Label for the x axis. [Ignored]")
@click.option("--ylabel", type=click.STRING, default="Z (m)",
  help="Label for the y axis. [Ignored]")
@click.option("--zlabel", type=click.STRING, default=None,
  help="Label for the color bar. [Ignored]")
@click.option("--title", type=click.STRING, default=None,
  help="Title for the figure. [Ignored]")
@click.option("--saveas", type=click.STRING, default=None,
  help="Name of figure file. [Ignored]")
@click.option("--no_show", is_flag=True, default=False,
  help="Suppreses showing the figure. [Ignored]")
@click.pass_context
def gk_rz(ctx, **kwargs):
  """
  \b
  Gyrokinetics: Load a quantity from a 2x or 3x simulation on the R-Z plane, and push it to the stack.
  The quantity (-q) can be specified as a file name, e.g.
    - <simulation_name>-<species_name>_M0_?.gkyl
    - <simulation_name>_b?-<species_name>_M0_?.gkyl
  where ? is either a number or *, or one of the default names:
    den, upar, tpar, tperp, temp, qpar, qperp,
    m0, m1, m2par, m2perp, m2, m3par, m3perp, m3,
    phi, bmag, jacobgeo
  in combination with the simulation name (-n) and frame (-f) and, if needed,
  species (-s).

  \b
  The default assumes these are in the current directory.
  Alternatively, the path to the files can be specified.

  \b
  If simulation is multiblock, you can:
    1) Pass * for the block index in the file name, OR
    2) Use --multib/-m to specify desired blocks (-m w/o a number plots all blocks).
  """

  data = ctx.obj["data"]  # Data stack.

  kwargs["path"] = kwargs["path"] + '/' # For safety.

  if (kwargs["quantity"][-len(gku.file_fmt):] == gku.file_fmt):
    # Quantity is a file (i.e. ends in .gkyl).
    # Extract the simulation name if it hasn't been provided. If it has, make
    # sure it matches.
    quantity_sim_name = kwargs["quantity"].split('-', 1)[0]
    if kwargs["name"] != None:
      if quantity_sim_name != kwargs["name"]:
        ctx.fail("gk_rz: Error. Input 'quantity' is a file but the simulation name prefix (before the first '-') doesn't match the 'name' input.")
    else:
      kwargs["name"] = quantity_sim_name

    if kwargs["quantity"][0] == "/":
      # Absolute path included. Don't append path.
      file_path_prefix = kwargs["quantity"]
    else:
      file_path_prefix = kwargs["path"] + kwargs["quantity"] # File name root including path.
    #end
  else:
    ctx.fail("gk_rz: Error. Quantity must be a .gkyl file path. Non-file quantity names are not yet supported.")
  # end

  verb_print(ctx, "Loading GK R-Z data from " + file_path_prefix)

  # Find matching files using glob
  glob_pattern = file_path_prefix.replace('?', '*')
  all_files = glob.glob(glob_pattern)

  if not all_files:
    click.echo(f"gk_rz: No files matching pattern '{glob_pattern}' found.")
    return

  # Extract available frames and blocks
  available_frames = set()
  available_blocks = set()
  file_info = []

  for fn in all_files:
    block_match = re.search(r'_b(\d+)-', fn)
    block_idx = int(block_match.group(1)) if block_match else None

    frame_match = re.search(r'_(\d+)\.gkyl$', fn)
    frame_idx = int(frame_match.group(1)) if frame_match else None

    if block_idx is not None:
      available_blocks.add(block_idx)
    if frame_idx is not None:
      available_frames.add(frame_idx)

    file_info.append({
      'file': fn,
      'block': block_idx,
      'frame': frame_idx
    })

  # Determine frames to load
  available_frames = sorted(list(available_frames))
  if kwargs.get("frame"):
    frame_spec = kwargs["frame"].strip()
    if "," in frame_spec:
      frames = [int(f.strip()) for f in frame_spec.split(",")]
    elif ":" not in frame_spec:
      frames = [int(frame_spec)]
    else:
      parts = frame_spec.split(":")
      lower = int(parts[0]) if parts[0] else available_frames[0]
      upper = int(parts[1]) if parts[1] else available_frames[-1] + 1
      step  = int(parts[2]) if len(parts) == 3 and parts[2] else 1
      frames = [f for f in available_frames if lower <= f < upper and (f - lower) % step == 0]
  else:
    frames = available_frames if available_frames else [None]

  # Determine blocks to load
  available_blocks = sorted(list(available_blocks))
  if available_blocks:
    if kwargs.get("multib") == "-10":
      blocks = [0]
    elif kwargs.get("multib") == "-1":
      blocks = available_blocks
    else:
      multib_spec = kwargs["multib"].strip()
      if "," in multib_spec:
        blocks = [int(b.strip()) for b in multib_spec.split(",")]
      elif ":" in multib_spec:
        slice_obj = gku.parse_slice_string(multib_spec)
        blocks = list(range(*slice_obj.indices(available_blocks[-1] + 1)))
      else:
        blocks = [int(multib_spec)]
  else:
    blocks = [None]

  # Load datasets
  loaded_count = 0
  for frame in frames:
    for block in blocks:
      matched_file = None
      for info in file_info:
        if info['block'] == block and info['frame'] == frame:
          matched_file = info['file']
          break

      if not matched_file:
        for info in file_info:
          if (block is None or info['block'] == block) and (frame is None or info['frame'] == frame):
            matched_file = info['file']
            break

      if not matched_file:
        continue

      # Construct c2p mapping file path
      prefix = f"{kwargs['name']}_b{block}" if block is not None else kwargs["name"]
      mapc2p_file = prefix + "-mapc2p_deflated" + gku.file_fmt
      mapc2p_file_path = kwargs["path"] + mapc2p_file
      if not os.path.exists(mapc2p_file_path):
        mapc2p_file = kwargs["name"] + "-mapc2p_deflated" + gku.file_fmt
        mapc2p_file_path = kwargs["path"] + mapc2p_file

      if os.path.exists(mapc2p_file_path):
        grid, vals, gdat = gku.read_gfile(matched_file, mapc2p=mapc2p_file_path)
      else:
        grid, vals, gdat = gku.read_gfile(matched_file)

      grid_int, vals_int = get_interp_data_from_gdata(gdat, kwargs["comp"])

      # Push to stack
      out = GData(
        tag=kwargs["tag"],
        label=kwargs["label"],
        comp_grid=ctx.obj["compgrid"],
        ctx=gdat.ctx
      )
      vals_int = vals_int[..., np.newaxis]
      out.push(grid_int, vals_int)
      data.add(out)
      loaded_count += 1

  if loaded_count > 1:
    data.set_unique_labels()

  verb_print(ctx, "Finishing GK R-Z data load.")

