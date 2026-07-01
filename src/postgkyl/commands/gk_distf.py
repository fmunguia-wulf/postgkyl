import glob

import click
import numpy as np

from postgkyl.data import GData, GInterpModal
from postgkyl.tools.gkeyll_dg_ops import GkeyllDGops
from postgkyl.utils import verb_print

# mc2nu grid deformation helpers
# This is a result of the gkyl_reader not having support for both mapc2p and mapc2p-vel grids.
# Particularly, the gkyl_reader does not support mapping phase space arrays with mapc2p
def _convert_cell_centered_to_nodal(cell_centers: np.ndarray) -> np.ndarray:
  """
  Given an array defined at cell centers, return the corresponding nodal
  values by interpolating half a cell width at the boundaries.
  """
  nodes = np.zeros(cell_centers.size + 1, dtype=cell_centers.dtype)
  nodes[1:-1] = 0.5 * (cell_centers[:-1] + cell_centers[1:])
  nodes[0]  = cell_centers[0]  + (cell_centers[0]  - nodes[1]) # Cell center plus half a cell width
  nodes[-1] = cell_centers[-1] + (cell_centers[-1] - nodes[-2]) # Cell center plus half a cell width
  return nodes

def _extract_values_along_dimension(mapped_values: np.ndarray, axis: int, cdim: int) -> np.ndarray:
  """Decompose mapped_values into a 1D array along the specified axis"""
  idx = [0] * (cdim + 1)  # Initialize indexing array. mc2nu has cdim+1 dimensions.
  idx[axis] = slice(None)  # Define a slice along the desired axis.
  idx[-1] = axis  # Select the appropriate component of mc2nu
  return mapped_values[tuple(idx)].reshape(-1)  # Apply indices and flatten to 1D.

def _apply_mc2nu_grid(uniform_grid: list, mc2nu_file: str, interp: int | None = None) -> list:
  """Replace computational configuration-space grid with non-uniform spatial coordinates."""
  mc2nu_data = GData(mc2nu_file)
  cdim = mc2nu_data.get_num_dims()

  _, mc2nu_values = GInterpModal(mc2nu_data, 1, "ms", interp).interpolate(tuple(range(cdim)))

  nonuniform_grid = list(uniform_grid)
  for d in range(cdim):
    mc2nu_single_axis = _extract_values_along_dimension(mc2nu_values, d, cdim)
    nonuniform_grid[d] = _convert_cell_centered_to_nodal(mc2nu_single_axis)
  # end
  return nonuniform_grid

def _resolve_optional_file_option(option_value: str | None) -> tuple[bool, str | None]:
  """Interpret an optional-value CLI option as (enabled, override_file)."""
  if option_value is None:
    return False, None
  if option_value == "":
    return True, None
  return True, option_value

def load_gk_distf(
  name: str, species: str, frame: int,
  tag: str = "f", suffix: str = "", use_c2p_vel: bool = False,
  use_mc2nu: bool = False, use_mapc2p: bool = False, block_idx: int | None = None,
  interp: int | None = None,
  Jf_file: str | None = None,
  mapc2p_vel_file: str | None = None,
  jacobvel_file: str | None = None,
  mc2nu_file: str | None = None,
  mapc2p_file: str | None = None,
  jacobtot_inv_file: str | None = None, ) -> GData:
  """Build a real distribution function from saved JxJvBf data."""

  prefix = f"{name}_b{block_idx}" if block_idx is not None else name
  frame_infix = f"{suffix}_" if suffix else ""

  if Jf_file is None:
    Jf_file = f"{prefix}-{species}_{frame_infix}{frame}.gkyl"
  # end
  if mapc2p_vel_file is None:
    mapc2p_vel_file = f"{prefix}-{species}_mapc2p_vel.gkyl"
  # end
  if jacobvel_file is None:
    jacobvel_file = f"{prefix}-{species}_jacobvel.gkyl"
  # end
  if mc2nu_file is None:
    mc2nu_file = f"{prefix}-geo_corn_mc2nu_pos_deflated.gkyl"
  # end
  if mapc2p_file is None:
    mapc2p_file = f"{prefix}-geo_corn_mapc2p_deflated.gkyl"
  # end
  if jacobtot_inv_file is None:
    jacobtot_inv_file = f"{prefix}-geo_int_jacobtot_inv.gkyl"
  # end

  Jf_data           = GData(Jf_file, mapc2p_vel_name=mapc2p_vel_file if use_c2p_vel else None)
  jacobvel_data     = GData(jacobvel_file)
  jacobtot_inv_data = GData(jacobtot_inv_file)

  # Divide Jf by jacobvel to get f * J_x * B.
  fJxB_data = GData(ctx=Jf_data.ctx) # Inside a GData object so we can interpolate
  fJxB_values = Jf_data.get_values() / jacobvel_data.get_values()
  fJxB_data.push(Jf_data.get_grid(), fJxB_values)

  if interp == 0:
    # No interpolation: weak multiply by reciprocal of (J_x*B).
    out_grid = fJxB_data.get_grid()
    f_data = GData(ctx=fJxB_data.ctx)
    f_data.push(out_grid, np.zeros_like(fJxB_data.get_values()))
    GkeyllDGops().multiply_conf_phase(f_data, jacobtot_inv_data, fJxB_data)
    f_values = f_data.get_values()
  else:
    # Interpolate f * J_x * B and jacobtot_inv to the same grid.
    out_grid, fJxB_values    = GInterpModal(fJxB_data, 1, "gkhyb", interp).interpolate()
    _, jacobtot_inv_values   = GInterpModal(jacobtot_inv_data, 1, "ms", interp).interpolate()
    fJxB_values              = np.squeeze(fJxB_values)
    jacobtot_inv_values      = np.squeeze(jacobtot_inv_values)

    # Reshape jacobtot_inv to have 1 component over velocity dimensions, then multiply.
    vdim = fJxB_values.ndim - jacobtot_inv_values.ndim
    jacobtot_inv_reshaped = jacobtot_inv_values.reshape(jacobtot_inv_values.shape + (1,) * vdim)
    f_values = fJxB_values * jacobtot_inv_reshaped
    # Add 1 dimension to represent 1 component
    f_values = f_values.reshape(f_values.shape + (1,))

  if use_mc2nu:
    out_grid = _apply_mc2nu_grid(out_grid, mc2nu_file, interp)
    if use_c2p_vel:
      Jf_data.ctx["grid_type"] = "c2p_vel + mc2nu"
    else:
      Jf_data.ctx["grid_type"] = "mc2nu"
    # end
  elif use_mapc2p:
    out_grid = _apply_mc2nu_grid(out_grid, mapc2p_file, interp)
    if use_c2p_vel:
      Jf_data.ctx["grid_type"] = "c2p_vel + mapc2p"
    else:
      Jf_data.ctx["grid_type"] = "mapc2p"
    # end
  # end

  out = GData(tag=tag, ctx=Jf_data.ctx)
  out.push(out_grid, f_values)
  return out
# end

@click.command()
@click.option("--name", "-n", required=True, type=click.STRING,
  help="Simulation name prefix (e.g. gk_lorentzian_mirror).")
@click.option("--species", "-s", required=True, type=click.STRING,
  help="Species name (e.g. ion or elc).")
@click.option("--suffix", default="", type=click.STRING,
  help="Use <name>-<species>_<suffix>_<frame>.gkyl as the input distribution.")
@click.option("--Jf-file", default=None, type=click.STRING,
  help="Jf filename override. If omitted, the default naming convention is used.")
@click.option("--jacobvel-file", default=None, type=click.STRING,
  help="jacobvel filename override. If omitted, the default naming convention is used.")
@click.option("--jacobtot-inv-file", default=None, type=click.STRING,
  help="jacobtot_inv filename override. If omitted, the default naming convention is used.")
@click.option("--frame", "-f", required=True, type=click.STRING,
  help="Frame number, comma separated values, or range. Use ':' for all frames\n"
       " and 'start:stop[:step]' for ranges.")
@click.option("--interp", "-i", type=click.INT,
  help="Interpolation onto a general mesh of specified amount. User -i 0 for no interpolation.")
@click.option("--c2p-vel", "-v", default=None, flag_value="", type=click.STRING,
  help="Convert velocity-space computational to physical coordinates, using mapping\n"
       "in (optionally) given file (default *_mapc2p_vel.gkyl).")
@click.option("--mc2nu", "-m", default=None, flag_value="", type=click.STRING,
  help="Convert non-uniform computational to field-aligned coordinates using mapping \n"
       "in (optionally) given file (default: *-geo_corn_mc2nu_pos_deflated.gkyl).")
@click.option("--mapc2p", "-p", default=None, flag_value="", type=click.STRING,
  help="Convert position-space computational to Cartesian (GKYL_GEOMETRY_MAPC2P) or \n"
       "cylindrical (GKYL_GEOMETRY_TOKAMAK, GKYL_GEOMETRY_MIRROR) coordinates, using \n"
       "mapping in (optionally) given file (default: *-geo_corn_mapc2p.gkyl)") 
@click.option("--block", "-b", default=None, type=click.INT,
  help="Use block-specific files with _b<idx> prefix, e.g. -b 1 loads <name>_b1-*.gkyl.")
@click.option("--tag", "-t", default="f", type=click.STRING,
  help="Tag for output dataset.")
@click.pass_context
def gk_distf(ctx, **kwargs):
  """
  Gyrokinetics: load the distribution function from files containing the 
  distribution (f) times one or multiple Jacobians (J). The Jacobians are
  divided out in order to output f. The distribution is interpolated, and
  the interpolation can optionally use mappings to convert from computational
  to physical coordinates.

  \b
  Command line example:
    pgkyl gk-distf -n gk_lorentzian_mirror -s ion -f 0

  \b
  Script example:
    import postgkyl as pg
    from postgkyl.commands import load_gk_distf
    
    distf = pg.commands.load_gk_distf(name="gk_lorentzian_mirror", species="ion", frame=0)
  """
  data = ctx.obj["data"]

  verb_print(ctx, "Building distribution function for " + kwargs["name"])

  frame_spec = kwargs["frame"].strip()
  if "," in frame_spec:
    frames = [int(f.strip()) for f in frame_spec.split(",")] # List of frames specified on input
  elif ":" not in frame_spec:
    frames = [int(frame_spec)] # Stick to the frame specified on input
  else:
    # Figure out how many frames are possible to read based on what files are available
    prefix = f"{kwargs['name']}_b{kwargs['block']}" if kwargs["block"] is not None else kwargs["name"]
    frame_infix = f"{kwargs['suffix']}_" if kwargs["suffix"] else ""
    stem = f"{prefix}-{kwargs['species']}_{frame_infix}"
    available = sorted({
      int(f.removeprefix(stem)[:-5])
      for f in glob.glob(f"{glob.escape(stem)}*.gkyl")
      if f.removeprefix(stem)[:-5].isdigit()
    })
    # Slice the data accordingly
    parts = frame_spec.split(":")
    lower = int(parts[0]) if parts[0] else available[0]
    upper = int(parts[1]) if parts[1] else available[-1] + 1
    step  = int(parts[2]) if len(parts) == 3 and parts[2] else 1
    frames = [f for f in available if lower <= f < upper and (f - lower) % step == 0]
  # end
  verb_print(ctx, f"Loading frames: {frames}")

  use_c2p_vel, mapc2p_vel_file = _resolve_optional_file_option(kwargs["c2p_vel"])
  use_mc2nu, mc2nu_file = _resolve_optional_file_option(kwargs["mc2nu"])
  use_mapc2p, mapc2p_file = _resolve_optional_file_option(kwargs["mapc2p"])

  for frame in frames:
    out = load_gk_distf(
      name=kwargs["name"], species=kwargs["species"], frame=frame,
      tag=kwargs["tag"], suffix=kwargs["suffix"],
      use_c2p_vel=use_c2p_vel,
      use_mc2nu=use_mc2nu, use_mapc2p=use_mapc2p,
      block_idx=kwargs["block"],
      interp=kwargs["interp"],
      Jf_file=kwargs.get("Jf-file"),
      mapc2p_vel_file=mapc2p_vel_file,
      jacobvel_file=kwargs["jacobvel_file"],
      mc2nu_file=mc2nu_file,
      mapc2p_file=mapc2p_file,
      jacobtot_inv_file=kwargs["jacobtot_inv_file"],
    )
    data.add(out)
  # end

  if len(frames) > 1:
    data.set_unique_labels()
  # end
# end
