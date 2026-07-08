import os

import click
import numpy as np
from scipy.interpolate import PchipInterpolator

from postgkyl.data import GData
from postgkyl.utils import verb_print
import postgkyl.utils.gk_utils as gku

# We don't import _binormal_project anymore, we handle it natively and much faster here.
from .gk_rz import (
    _file_prefix, _nodes_geometry, _mapc2p_geometry, 
    _interp, _centers, _sample
)

@click.command(name="gk-fluxsurf")
@click.option("--mapc2p", "-m", default=None, type=click.STRING,
  help="Use a modal mapc2p file as the geometry source instead of the default nodes file.")
@click.option("--nodes", "-n", default=None, type=click.STRING,
  help="Path to a nodal geometry file, overriding the default lookup.")
@click.option("--x-idx", "-x", default=0, type=click.INT,
  help="The cell index in the radial (x) direction representing the flux surface. Default 0.")
@click.option("--nphi", default=128, type=click.INT,
  help="Number of toroidal angle (phi) slices. Increased default to 128 for smoother diagonal field lines.")
@click.option("--nz-interp", default=8, type=click.INT,
  help="Parallel (z) up-sampling factor used to smooth the projected 3D surfaces. Default 8.")
@click.option("--use", "-u", default=None,
  help="Specify tag of datasets to process from the stack.")
@click.option("--tag", "-t", default="fluxsurf", type=click.STRING,
  help="Tag for output datasets.")
@click.option("--label", "-l", default=None, type=click.STRING,
  help="Custom label for the result.")
@click.pass_context
def gk_fluxsurf(ctx, **kwargs):
  """
  Gyrokinetics: Extract a 2D theta-phi flux surface.
  
  This command extracts data along a specific radial flux surface (constant x)
  for 3D field-aligned data. It achieves this by performing a binormal 
  projection over a scan of toroidal angles (phi), creating a 2D grid of 
  phi vs z (where z maps along the poloidal/theta direction).
  """
  data = ctx.obj["data"]

  first_data = next(data.iterator(kwargs["use"]), None)
  if first_data is None:
    return
  
  if first_data.get_num_dims() < 3:
    ctx.fail("gk-fluxsurf requires 3D data to scan over toroidal angle (phi).")

  prefix = _file_prefix(getattr(first_data, "_file_name", None))

  mapc2p_opt = kwargs["mapc2p"]
  nodes_opt = kwargs["nodes"]
  if mapc2p_opt is not None and nodes_opt is not None:
    raise click.ClickException("Pass either --mapc2p or --nodes, not both.")

  if nodes_opt is not None:
    geo_path, geo_reader = nodes_opt, _nodes_geometry
  elif mapc2p_opt is not None:
    geo_path = mapc2p_opt if mapc2p_opt else (
      prefix + "-geo_int_mapc2p.gkyl" if prefix is not None else None)
    geo_reader = _mapc2p_geometry
  elif prefix is not None:
    geo_path, geo_reader = prefix + "-geo_int_nodes.gkyl", _nodes_geometry
    if not os.path.exists(geo_path):
      geo_path, geo_reader = prefix + "-geo_int_mapc2p.gkyl", _mapc2p_geometry
  else:
    geo_path, geo_reader = None, None

  if geo_path is None or not os.path.exists(geo_path):
    raise click.ClickException(
      "Could not find a geometry file; pass it with -n/--nodes or -m/--mapc2p.")

  x_idx = kwargs["x_idx"]
  nphi = kwargs["nphi"]
  nz_interp = max(1, kwargs["nz_interp"])

  verb_print(ctx, f"Extracting theta-phi flux surface at x-index {x_idx} using geometry {geo_path}")

  # Load fine computational grid 
  fine_grid, _ = _interp(first_data)
  xc, yc, zc = _centers(fine_grid)
  Nz = zc.size

  # Load and sample the geometry to get continuous physical phi values
  gx_gy_gz, majorR, vertZ, phi = geo_reader(geo_path)
  gx, gy, gz = gx_gy_gz
  
  # Up-sample z for a smooth parallel mapping
  zf_edges = np.linspace(fine_grid[2][0], fine_grid[2][-1], nz_interp * Nz + 1)
  zf = 0.5 * (zf_edges[:-1] + zf_edges[1:])

  # Unwrap toroidal angle coordinates to track continuous winding
  phi = np.unwrap(np.unwrap(np.unwrap(phi, axis=2), axis=1), axis=0)
  phi_grid = _sample(phi, [gx, gy, gz], [xc, yc, zf])

  # Array of toroidal angles to scan over (standard 0 to 2*pi)
  phi_tor_list = np.linspace(0, 2*np.pi, nphi, endpoint=False)

  loaded_count = 0
  for dat in data.iterator(kwargs["use"]):
    _, vals = _interp(dat)

    if x_idx >= vals.shape[0] or x_idx < 0:
      ctx.fail(f"Requested x-index {x_idx} is out of bounds for data with Nx={vals.shape[0]}")

    # 1. Up-sample the 3D field along the z (parallel) direction
    vals_zf = PchipInterpolator(zc, vals, axis=-1, extrapolate=True)(zf)

    # 2. Extract ONLY the target radial index to save massive amounts of compute
    vals_2d = vals_zf[x_idx, :, :] # Shape: (Ny, len(zf))
    phi_2d = phi_grid[x_idx, :, :] # Shape: (Ny, len(zf))
    Ny = vals_2d.shape[0]

    # 3. Allocate the 2D array for our theta-phi output grid
    flux_surf_data = np.empty((nphi, len(zf)))

    # 4. Vectorized Projection: Loop only over z, evaluate all phi_tor simultaneously
    for iz in range(len(zf)):
      phi_y = phi_2d[:, iz]
      val_y = vals_2d[:, iz]
      
      # Toroidal angle subtended by one full (periodic) binormal box.
      box = np.mean(np.diff(phi_y)) * Ny
      
      # Extend domain for periodic interpolation
      phi_ext = np.concatenate([phi_y - box, phi_y, phi_y + box])
      val_ext = np.concatenate([val_y, val_y, val_y])
      
      # Sort to prepare for numpy interpolation
      order = np.argsort(phi_ext)
      phi_ext_sorted = phi_ext[order]
      val_ext_sorted = val_ext[order]
      
      # Fold ALL requested phi angles into the local domain at once
      pt_array = phi_y[0] + np.mod(phi_tor_list - phi_y[0], box)
      
      # Interpolate and assign the entire column of toroidal angles in one call
      flux_surf_data[:, iz] = np.interp(pt_array, phi_ext_sorted, val_ext_sorted)

    out = GData(tag=kwargs["tag"], label=kwargs["label"], ctx=dat.ctx)
    
    # Push data back to the stack: Dimensions are now [phi, z]
    out.push([phi_tor_list, zf], flux_surf_data[..., np.newaxis])
    data.add(out)
    dat.deactivate()
    loaded_count += 1

  if loaded_count > 1:
    data.set_unique_labels()

  verb_print(ctx, "Finishing flux surface extraction.")