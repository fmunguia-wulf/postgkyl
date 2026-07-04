import os

import click
import numpy as np
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator

from postgkyl.data import GData, GInterpModal
from postgkyl.utils import verb_print
import postgkyl.utils.gk_utils as gku


def _file_prefix(file_name):
  if not file_name:
    return None
  return os.path.splitext(file_name)[0].rsplit("-", 1)[0]


def _mapc2p_geometry(path):
  """
  Interpolate a modal mapc2p (or geo R,Z,phi) file to physical R, Z, phi.
  """
  gdat = GData(path)
  if gku.is_gdata_geo_mapc2p(gdat):
    # Cartesian X, Y, Z: R = sqrt(X^2 + Y^2), phi = atan2(Y, X).
    grid, X = _interp(gdat, 0)
    _, Y = _interp(gdat, 1)
    _, Z = _interp(gdat, 2)
    return _centers(grid), np.sqrt(X**2 + Y**2), Z, np.arctan2(Y, X)

  # Components are directly R, Z, phi.
  grid, R = _interp(gdat, 0)
  _, Z = _interp(gdat, 1)
  phi = _interp(gdat, 2)[1] if R.ndim == 3 else None
  return _centers(grid), R, Z, phi


def _gauss_nodes(edges):
  """Coordinates of the p1 nodal points (cell center +/- h/(2*sqrt(3))) of a
  1D edge grid, i.e. where the values of a nodal geometry file live."""
  c = 0.5 * (edges[:-1] + edges[1:])
  off = np.diff(edges) / (2.0 * np.sqrt(3.0))
  return np.ravel(np.column_stack([c - off, c + off]))


def _nodes_geometry(path):
  """
  Read a nodal geometry file (pointwise node coordinates) to physical R, Z, phi.
  """
  gdat = GData(path)
  vals = gdat.get_values()
  # The stored grid is 2x-refined (one edge per value plus one); the values
  # themselves sit at the two p1 nodes of each cell, whose edges are every 
  # other stored grid point.
  coords = []
  for dim, g in enumerate(gdat.get_grid()):
    g = np.squeeze(g)
    if len(g) != vals.shape[dim] + 1 or vals.shape[dim] % 2:
      raise ValueError("Unrecognized nodal geometry layout in " + path)
    coords.append(_gauss_nodes(g[::2]))

  if gku.is_gdata_geo_mapc2p(gdat):
    X, Y, Z = vals[..., 0], vals[..., 1], vals[..., 2]
    return coords, np.sqrt(X**2 + Y**2), Z, np.arctan2(Y, X)

  R, Z = vals[..., 0], vals[..., 1]
  phi = vals[..., 2] if R.ndim == 3 else None
  return coords, R, Z, phi


def _interp(gdat, comp=0):
  """Interpolate component 'comp' of the DG GData object 'gdat'.

  Returns the computational grid (list of 1D node arrays) and the
  interpolated values at fine cell centers.
  """
  poly_order = gdat.ctx["poly_order"]
  basis_type = gdat.ctx["basis_type"]
  if basis_type == "serendipity":
    basis_type = "ms"

  grid, vals = GInterpModal(gdat, poly_order, basis_type).interpolate(comp)
  return [np.squeeze(g) for g in grid], np.squeeze(vals)


def _centers(nodes):
  """Cell centers from a list of 1D node arrays."""
  return [0.5 * (n[:-1] + n[1:]) for n in nodes]


def _sample(values, src_coords, dst_coords):
  """Linearly interpolate `values` onto the grid spanned by `dst_coords`."""
  mesh = np.meshgrid(*dst_coords, indexing="ij")
  return RegularGridInterpolator(
    tuple(src_coords), values, bounds_error=False, fill_value=None
  )(tuple(mesh))


def _binormal_project(vals, phi_uw, phi_tor):
  """Reconstruct a field-aligned dataset on the poloidal plane at phi = phi_tor.

  For each (x, z) column the field is sampled along the binormal direction y
  (axis 1) at the physical toroidal angle 'phi_uw' (unwrapped, i.e. continuous
  in all directions). The field is periodic in y, so it is also periodic in
  toroidal angle with period 'box' (the toroidal extent of one binormal box);
  phi_tor is folded into the interval covered by each column before
  interpolating, which stitches the simulated wedge periodically around the
  torus. This is the real-space equivalent of the FFT phase-sum used in
  field-aligned poloidal projections.

  'vals' and 'phi_uw' have shape (Nx, Ny, Nz). Returns a (Nx, Nz) array.
  """
  Nx, Ny, Nz = vals.shape
  out = np.empty((Nx, Nz))
  for ix in range(Nx):
    for iz in range(Nz):
      phi_y = phi_uw[ix, :, iz]
      val_y = vals[ix, :, iz]
      # Toroidal angle subtended by one full (periodic) binormal box.
      box = np.mean(np.diff(phi_y)) * Ny
      # Fold phi_tor into [phi_y[0], phi_y[0] + box)
      pt = phi_y[0] + np.mod(phi_tor - phi_y[0], box)
      phi_ext = np.concatenate([phi_y - box, phi_y, phi_y + box])
      val_ext = np.concatenate([val_y, val_y, val_y])
      order = np.argsort(phi_ext)
      out[ix, iz] = np.interp(pt, phi_ext[order], val_ext[order])

  return out


@click.command()
@click.option("--mapc2p", "-m", default=None, type=click.STRING,
  help="Use a modal mapc2p file as the geometry source instead of the default nodes file; "
       "pass '' to look up '<prefix>-geo_int_mapc2p.gkyl' from the first processed dataset's prefix.")
@click.option("--nodes", "-n", default=None, type=click.STRING,
  help="Path to a nodal geometry file, overriding the default '<prefix>-geo_int_nodes.gkyl' lookup.")
@click.option("--z-axis", "-z", default=0.0, type=click.FLOAT,
  help="Vertical position of the magnetic axis (m), added to the geometry Z."
       "mapc2p files store Z relative to the axis; pass Z_axis from the simulation input "
       "file to plot in machine coordinates. Default 0.")
@click.option("--use", "-u", default=None,
  help="Specify tag of datasets to process from the stack.")
@click.option("--tag", "-t", default="rz", type=click.STRING,
  help="Tag for output datasets.")
@click.option("--label", "-l", default=None, type=click.STRING,
  help="Custom label for the result.")
@click.option("--phi-tor", "-p", default=0.0, type=click.FLOAT,
  help="Toroidal angle (radians) of the poloidal plane to project 3D data onto. Default 0.")
@click.option("--nz-interp", default=8, type=click.INT,
  help="Parallel (z) up-sampling factor used to smooth the projected 3D surfaces. Default 8.")
@click.pass_context
def gk_rz(ctx, **kwargs):
  """
  \b
  Gyrokinetics: Interpolate DG dataset(s) and map them to the R-Z plane.
  Assumes DG data (not yet interpolated) has been loaded onto the stack by a
  preceding command.

  The geometry is automatically found from the prefix of the first processed
  dataset: the pointwise '<prefix>-geo_int_nodes.gkyl' is preferred (exact node
  coordinates, robust at coarse z resolution), falling back to the modal
  '<prefix>-geo_int_mapc2p.gkyl'. Use '-n path' to point at a specific nodes
  file, '-m path' at a specific mapc2p file, or "-m ''" to force the default
  mapc2p lookup.

  For 3D (field-aligned) data the field is reconstructed on the poloidal plane at
  toroidal angle --phi-tor (default 0) by interpolating along the binormal
  direction, up-sampled in z (--nz-interp) for smooth surfaces.
  """
  data = ctx.obj["data"]

  # Locate the geometry files from the prefix of the first processed dataset.
  first = next(data.iterator(kwargs["use"]), None)
  if first is None:
    return

  prefix = _file_prefix(getattr(first, "_file_name", None))

  # Geometry source: the pointwise nodes file by default (exact node values;
  # the modal mapc2p representation loses amplitude where the toroidal winding
  # is under-resolved), the modal mapc2p file on request or as fallback.
  mapc2p_opt = kwargs["mapc2p"]
  nodes_opt = kwargs["nodes"]
  if mapc2p_opt is not None and nodes_opt is not None:
    raise click.ClickException("Pass either --mapc2p or --nodes, not both.")

  if nodes_opt is not None:
    geo_path, geo_reader = nodes_opt, _nodes_geometry
  elif mapc2p_opt is not None:
    # An empty value requests the default '<prefix>-geo_int_mapc2p.gkyl'.
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
      "Could not find a geometry file; pass it with -N/--nodes or -n/--mapc2p.")

  is_3d = first.get_num_dims() == 3

  if not is_3d:
    # ---- 2D: direct map onto R-Z using mapc2p. ----

    verb_print(ctx, "Mapping stack data to R-Z using " + geo_path)
    geo_coords, majorR, vertZ, _ = geo_reader(geo_path)
    vertZ = vertZ + kwargs["z_axis"]
    loaded_count = 0
    for dat in data.iterator(kwargs["use"]):
      field_grid, vals = _interp(dat)
      # Evaluate R, Z at the field cell corners (its node arrays) so pcolormesh
      # gets explicit cell edges, not non-monotonic curvilinear cell centers.
      R = _sample(majorR, geo_coords, field_grid)
      Z = _sample(vertZ, geo_coords, field_grid)
      out = GData(tag=kwargs["tag"], label=kwargs["label"], ctx=dat.ctx)
      out.push([R, Z], vals[..., np.newaxis])
      data.add(out)
      dat.deactivate()
      loaded_count += 1
  
    if loaded_count > 1:
      data.set_unique_labels()
  
    verb_print(ctx, "Finishing R-Z mapping.")
    return

  # ---- 3D: project onto the poloidal plane at phi_tor. ----
  phi_tor = kwargs["phi_tor"]
  nz_interp = max(1, kwargs["nz_interp"])

  # Field cell-center coordinates (from the field's own DG grid).
  fine_grid, _ = _interp(first)
  xc, yc, zc = _centers(fine_grid)
  Nz = zc.size

  verb_print(ctx, "3D data: projecting onto phi = %g rad using geometry %s"
                  % (phi_tor, geo_path))
  gx_gy_gz, majorR, vertZ, phi = geo_reader(geo_path)
  vertZ = vertZ + kwargs["z_axis"]
  gx, gy, gz = gx_gy_gz

  # Up-sampled z: edges (zf_edges) for the plotting grid, centers (zf) for the
  # field reconstruction.
  xn = fine_grid[0]
  zf_edges = np.linspace(zc[0], zc[-1], nz_interp * Nz + 1)
  zf = 0.5 * (zf_edges[:-1] + zf_edges[1:])

  # Interpolate the geometry.
  Rrz = _sample(majorR[:, 0, :], [gx, gz], [xn, zf_edges])
  Zrz = _sample(vertZ[:, 0, :], [gx, gz], [xn, zf_edges])
  # Make phi continuous in all three directions before interpolating.
  phi = np.unwrap(np.unwrap(np.unwrap(phi, axis=2), axis=1), axis=0)
  phi_grid = _sample(phi, [gx, gy, gz], [xc, yc, zf])

  loaded_count = 0
  for dat in data.iterator(kwargs["use"]):
    _, vals = _interp(dat)
    # Up-sample the field in z onto the projection grid, then reconstruct at phi_tor.
    vals_zf = PchipInterpolator(zc, vals, axis=-1, extrapolate=True)(zf)
    proj = _binormal_project(vals_zf, phi_grid, phi_tor)
    out = GData(tag=kwargs["tag"], label=kwargs["label"], ctx=dat.ctx)
    out.push([Rrz, Zrz], proj[..., np.newaxis])
    data.add(out)
    dat.deactivate()
    loaded_count += 1

  if loaded_count > 1:
    data.set_unique_labels()

  verb_print(ctx, "Finishing R-Z mapping.")
