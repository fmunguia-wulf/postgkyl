"""Loader for Gkeyll gyrokinetic distribution functions.

Reads the saved ``Jf`` (distribution times one or more Jacobians) together
with the velocity/configuration Jacobians, divides them out, and
interpolates onto a nodal grid, optionally applying velocity- and
position-space coordinate mappings.

Ported from ``src_bak/postgkyl/loaders/gk_distf.py``. The Jf / jacobvel
division happens on the *raw* (pre-interpolation) coefficient arrays, exactly
as in ``src_bak`` -- this is not a general DG weak divide, it relies on
``jacobvel`` being stored piecewise-constant per cell (a single component),
so dividing every one of Jf's basis coefficients by that one constant is
exact scalar division, cell by cell. ``resolve_frames``' range-discovery now
calls the shared :mod:`postgkyl.diagnostics.discovery` helper instead of its
own glob.
"""

from __future__ import annotations

import numpy as np

from postgkyl import ops
from postgkyl.api import GData

from .. import discovery


def resolve_frames(
    frame: "int | str | list | tuple",
    *, name: str, species: str, suffix: str = "", block_idx: int | None = None,
) -> list:
  """Expand a frame specification into a concrete sorted list of frame indices.

  Args:
    frame: An ``int`` (single frame); a ``list``/``tuple`` of ints; a string
      with a single number (``"7"``) or comma-separated numbers
      (``"0,2,4"``); or a ``'start:stop[:step]'`` / ``':'`` range (range
      bounds default to the first/last frame discovered on disk).
    name: Simulation name prefix.
    species: Species name.
    suffix: Distribution-file suffix (see :func:`load_gk_distf`).
    block_idx: Use block-specific files with a ``_b<idx>`` prefix.

  Returns:
    A sorted list of concrete frame indices.
  """
  if isinstance(frame, int):
    return [frame]
  # end
  if isinstance(frame, (list, tuple)):
    return [int(f) for f in frame]
  # end

  frame_spec = str(frame).strip()
  if "," in frame_spec:
    return [int(f.strip()) for f in frame_spec.split(",")]
  # end
  if ":" not in frame_spec:
    return [int(frame_spec)]
  # end

  prefix = f"{name}_b{block_idx}" if block_idx is not None else name
  frame_infix = f"{suffix}_" if suffix else ""
  stem = f"{prefix}-{species}_{frame_infix}"
  available = sorted(discovery.available_frames(stem))
  parts = frame_spec.split(":")
  lower = int(parts[0]) if parts[0] else available[0]
  upper = int(parts[1]) if parts[1] else available[-1] + 1
  step = int(parts[2]) if len(parts) == 3 and parts[2] else 1
  return [f for f in available if lower <= f < upper and (f - lower) % step == 0]


def load_gk_distf(
    name: str, species: str, frame: int, *,
    tag: str = "f", suffix: str = "", use_c2p_vel: bool = False,
    use_mc2nu: bool = False, use_mapc2p: bool = False, block_idx: int | None = None,
    interp: int | None = None,
    jf_file: str | None = None,
    mapc2p_vel_file: str | None = None,
    jacobvel_file: str | None = None,
    mc2nu_file: str | None = None,
    mapc2p_file: str | None = None,
    jacobtot_inv_file: str | None = None,
) -> GData:
  """Build a real distribution function from saved ``Jf`` data.

  Args:
    name: Simulation name prefix.
    species: Species name.
    frame: Frame index.
    tag: Tag for the resulting dataset.
    suffix: Use ``<name>-<species>_<suffix>_<frame>.gkyl`` as the input.
    use_c2p_vel: Convert velocity-space computational coordinates to
      physical ones using the ``mapc2p_vel`` mapping.
    use_mc2nu: Convert non-uniform computational coordinates to
      field-aligned ones.
    use_mapc2p: Convert position-space computational coordinates to
      Cartesian/cylindrical.
    block_idx: Use block-specific files with a ``_b<idx>`` prefix.
    interp: Interpolate onto a general mesh of the specified amount
      (default: ``poly_order + 1`` points per cell).
    jf_file, mapc2p_vel_file, jacobvel_file, mc2nu_file, mapc2p_file,
    jacobtot_inv_file: Explicit filename overrides; each defaults to the
      standard naming convention derived from ``name``/``species``/
      ``block_idx`` when omitted.

  Returns:
    A :class:`~postgkyl.api.gdata.GData` holding the interpolated
    distribution function.
  """
  prefix = f"{name}_b{block_idx}" if block_idx is not None else name
  frame_infix = f"{suffix}_" if suffix else ""

  if jf_file is None:
    jf_file = f"{prefix}-{species}_{frame_infix}{frame}.gkyl"
  # end
  if mapc2p_vel_file is None:
    mapc2p_vel_file = f"{prefix}-{species}_mapc2p_vel.gkyl"
  # end
  if jacobvel_file is None:
    jacobvel_file = f"{prefix}-{species}_jacobvel.gkyl"
  # end
  if mc2nu_file is None:
    mc2nu_file = f"{prefix}-mc2nu_pos_deflated.gkyl"
  # end
  if mapc2p_file is None:
    mapc2p_file = f"{prefix}-mapc2p_deflated.gkyl"
  # end
  if jacobtot_inv_file is None:
    jacobtot_inv_file = f"{prefix}-jacobtot_inv.gkyl"
  # end

  jf_data = GData(jf_file)
  jacobvel_data = GData(jacobvel_file)
  jacobtot_inv_data = GData(jacobtot_inv_file)

  # Divide Jf by jacobvel to get f * J_x * B (raw coefficients: exact
  # because jacobvel is piecewise-constant per cell).
  fjxb_values = jf_data.get_values() / jacobvel_data.get_values()
  fjxb_data = GData(ctx=jf_data.ctx)
  fjxb_data.push(jf_data.get_grid(), fjxb_values)

  # Interpolate f * J_x * B and jacobtot_inv onto the same (refined) grid.
  interpolated = fjxb_data.interp(basis="gkhyb", p=1, interp=interp)
  jacobtot_inv_interp = jacobtot_inv_data.interp(basis="ms", p=1, interp=interp)
  out_grid = interpolated.get_grid()
  fjxb_interp_values = np.squeeze(interpolated.get_values())
  jacobtot_inv_values = np.squeeze(jacobtot_inv_interp.get_values())

  # Reshape jacobtot_inv to have 1 component over velocity dimensions, then
  # multiply.
  vdim = fjxb_interp_values.ndim - jacobtot_inv_values.ndim
  jacobtot_inv_reshaped = jacobtot_inv_values.reshape(
      jacobtot_inv_values.shape + (1,) * vdim)
  f_values = fjxb_interp_values * jacobtot_inv_reshaped
  f_values = f_values.reshape(f_values.shape + (1,))  # component axis

  out = GData(tag=tag, ctx=jf_data.ctx)
  out.push(out_grid, f_values)

  # Coordinate maps run on the already-interpolated data via the shared map
  # verb. Velocity space (c2p_vel) deforms the trailing axes; configuration
  # space (mc2nu / mapc2p) deforms the leading ones.
  grid_type = []
  if use_c2p_vel:
    out = ops.map(out, mapc2p_vel_file, space="vel")
    grid_type.append("c2p_vel")
  # end
  if use_mc2nu:
    out = ops.map(out, mc2nu_file, space="conf")
    grid_type.append("mc2nu")
  elif use_mapc2p:
    out = ops.map(out, mapc2p_file, space="conf")
    grid_type.append("mapc2p")
  # end
  if grid_type:
    out.ctx["grid_type"] = " + ".join(grid_type)
  # end
  return out
