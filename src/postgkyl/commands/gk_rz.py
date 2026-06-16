import os

import click
import numpy as np
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator

from postgkyl.data import GData, GInterpModal
from postgkyl.utils import verb_print
import postgkyl.utils.gk_utils as gku


def _file_prefix(file_name):
  """Gkyl file prefix: strip the extension and the trailing '-<name>_<frame>'.

  e.g. '/path/sim_p1-field_700.gkyl' -> '/path/sim_p1'. Geometry files then
  follow as '<prefix>-mapc2p.gkyl' and '<prefix>-nodes.gkyl'.
  """
  if not file_name:
    return None
  return os.path.splitext(file_name)[0].rsplit("-", 1)[0]


def _mapc2p_geometry(path):
  """Interpolate a mapc2p (or geo R,Z,phi) file to physical R, Z, phi.

  Returns (grid, R, Z, phi) at the fine DG cell centers; phi is None for 2D
  geometry files that only carry R and Z.
  """
  gdat = GData(path)
  if gku.is_gdata_geo_mapc2p(gdat):
    # Cartesian X, Y, Z: R = sqrt(X^2 + Y^2), phi = atan2(Y, X).
    grid, X = _interp(gdat, 0)
    _, Y = _interp(gdat, 1)
    _, Z = _interp(gdat, 2)
    return grid, np.sqrt(X**2 + Y**2), Z, np.arctan2(Y, X)
  # end
  # Components are directly R, Z, phi.
  grid, R = _interp(gdat, 0)
  _, Z = _interp(gdat, 1)
  phi = _interp(gdat, 2)[1] if R.ndim == 3 else None
  return grid, R, Z, phi


def _interp(gdat, comp=0):
  """Interpolate component 'comp' of the DG GData object 'gdat'.

  Returns the computational grid (list of 1D node arrays) and the
  interpolated values at fine cell centers.
  """
  poly_order = gdat.ctx["poly_order"]
  basis_type = gdat.ctx["basis_type"]
  if basis_type == "serendipity":
    basis_type = "ms"
  # end
  grid, vals = GInterpModal(gdat, poly_order, basis_type).interpolate(comp)
  return [np.squeeze(g) for g in grid], np.squeeze(vals)


def _centers(nodes):
  """Cell centers from a list of 1D node arrays."""
  return [0.5 * (n[:-1] + n[1:]) for n in nodes]


def _load_nodes_geometry(path):
  """Load physical R, Z and toroidal angle phi from a -nodes.gkyl file.

  The nodes file stores the geometry at cell corners over the full
  computational domain (including the z = +/- pi parallel boundaries), which is
  what lets the poloidal flux surfaces close. Returns the computational
  coordinate arrays (x, alpha, z) and R, Z, phi with shape (Nx, Nalpha, Nz).
  """
  ndat = GData(path)
  vals = ndat.get_values()
  raw_grid = ndat.get_grid()
  # The nodal grid arrays carry one extra entry; collapse them to node centers.
  coords = [np.linspace(g[0], g[-1], len(g) - 1) for g in raw_grid]
  c0, c1, c2 = vals[..., 0], vals[..., 1], vals[..., 2]
  if c0.min() < 0.0:
    # Cartesian X, Y, Z nodes: R = sqrt(X^2 + Y^2), phi = atan2(Y, X).
    majorR = np.sqrt(c0**2 + c1**2)
    vertZ = c2
    phi = np.arctan2(c1, c0)
  else:
    # Nodes are already cylindrical R, Z, phi.
    majorR, vertZ, phi = c0, c1, c2
  # end
  return coords, majorR, vertZ, phi


def _binormal_project(vals, phi_uw, phi_tor):
  """Reconstruct a field-aligned dataset on the poloidal plane at phi = phi_tor.

  For each (x, z) column the field is sampled along the binormal direction y
  (axis 1) at the physical toroidal angle 'phi_uw' (already unwrapped along y).
  The field is periodic in y, so the (phi, value) samples are tiled periodically
  by one binormal box toroidal extent to guarantee phi_tor is bracketed, then
  interpolated. This is the real-space equivalent of the FFT phase-sum used in
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
      phi_ext = np.concatenate([phi_y - box, phi_y, phi_y + box])
      val_ext = np.concatenate([val_y, val_y, val_y])
      order = np.argsort(phi_ext)
      out[ix, iz] = np.interp(phi_tor, phi_ext[order], val_ext[order])
    # end
  # end
  return out


@click.command()
@click.option("--mapc2p", "-n", default=None, type=click.STRING,
  help="Path to the mapc2p.gkyl file. If omitted, '<prefix>-mapc2p.gkyl' is looked up from "
       "the first processed dataset's prefix.")
@click.option("--nodes", "-N", default=None, type=click.STRING,
  help="Path to the -nodes.gkyl file (default geometry source for 3D data; its full [-pi, pi] "
       "grid closes the poloidal flux surfaces). If omitted, '<prefix>-nodes.gkyl' is looked up.")
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

  The mapc2p and nodes geometry files are located automatically from the prefix
  of the first processed dataset (e.g. '<prefix>-mapc2p.gkyl', '<prefix>-nodes.gkyl'),
  so '-n'/'-N' only need to be given to override that. For 3D data the nodes file
  is used by default (it closes the poloidal flux surfaces); 2D data uses mapc2p.

  For 3D (field-aligned) data the field is reconstructed on the poloidal plane at
  toroidal angle --phi-tor (default 0) by interpolating along the binormal
  direction, up-sampled in z (--nz-interp) for smooth surfaces.
  """
  data = ctx.obj["data"]

  # Locate the geometry files from the prefix of the first processed dataset.
  first = next(data.iterator(kwargs["use"]), None)
  if first is None:
    return
  # end
  prefix = _file_prefix(getattr(first, "_file_name", None))

  mapc2p_path = kwargs["mapc2p"]
  if mapc2p_path is None and prefix is not None:
    mapc2p_path = prefix + "-mapc2p.gkyl"
  # end
  nodes_path = kwargs["nodes"]
  if nodes_path is None and prefix is not None:
    candidate = prefix + "-nodes.gkyl"
    nodes_path = candidate if os.path.exists(candidate) else None
  # end

  is_3d = first.get_num_dims() == 3

  if not is_3d:
    # ---- 2D: direct map onto R-Z using mapc2p. ----
    if mapc2p_path is None or not os.path.exists(mapc2p_path):
      raise click.ClickException("Could not find a mapc2p file; pass it with -n.")
    # end
    verb_print(ctx, "Mapping stack data to R-Z using " + mapc2p_path)
    _, majorR, vertZ, _ = _mapc2p_geometry(mapc2p_path)
    loaded_count = 0
    for dat in data.iterator(kwargs["use"]):
      _, vals = _interp(dat)
      out = GData(tag=kwargs["tag"], label=kwargs["label"], ctx=dat.ctx)
      out.push([majorR, vertZ], vals[..., np.newaxis])
      data.add(out)
      dat.deactivate()
      loaded_count += 1
    # end
    if loaded_count > 1:
      data.set_unique_labels()
    # end
    verb_print(ctx, "Finishing R-Z mapping.")
    return
  # end

  # ---- 3D: project onto the poloidal plane at phi_tor. ----
  phi_tor = kwargs["phi_tor"]
  nz_interp = max(1, kwargs["nz_interp"])

  # Field cell-center coordinates (from the field's own DG grid).
  fine_grid, _ = _interp(first)
  xc, yc, zc = _centers(fine_grid)
  Nz = zc.size

  use_nodes = nodes_path is not None and os.path.exists(nodes_path)
  if use_nodes:
    # Geometry from the nodes file: its z-grid spans the full [-pi, pi] so the
    # flux surfaces close. Interpolate it onto the field's (x, z) and (x, y, z).
    verb_print(ctx, "3D data: projecting onto phi = %g rad using nodes %s." % (phi_tor, nodes_path))
    (xn, an, zn), Rn, Zn, phin = _load_nodes_geometry(nodes_path)
    zf = np.linspace(zn[0], zn[-1], nz_interp * Nz)
    XX, ZZ = np.meshgrid(xc, zf, indexing="ij")
    rgi = lambda d: RegularGridInterpolator((xn, zn), d, bounds_error=False, fill_value=None)
    Rrz = rgi(Rn[:, 0, :])((XX, ZZ))
    Zrz = rgi(Zn[:, 0, :])((XX, ZZ))
    GX, GY, GZ = np.meshgrid(xc, yc, zf, indexing="ij")
    phi_grid = RegularGridInterpolator(
      (xn, an, zn), np.unwrap(phin, axis=1), bounds_error=False, fill_value=None
    )((GX, GY, GZ))
  else:
    if mapc2p_path is None or not os.path.exists(mapc2p_path):
      raise click.ClickException("Could not find a nodes or mapc2p file; pass one with -N or -n.")
    # end
    verb_print(ctx, "3D data: projecting onto phi = %g rad using mapc2p %s "
                    "(no nodes file: surfaces will not close at z = +/- pi)." % (phi_tor, mapc2p_path))
    _, majorR, vertZ, phi = _mapc2p_geometry(mapc2p_path)
    zf = np.linspace(zc[0], zc[-1], nz_interp * Nz)
    Rrz = PchipInterpolator(zc, majorR[:, 0, :], axis=-1, extrapolate=True)(zf)
    Zrz = PchipInterpolator(zc, vertZ[:, 0, :], axis=-1, extrapolate=True)(zf)
    phi_grid = PchipInterpolator(zc, np.unwrap(phi, axis=1), axis=-1, extrapolate=True)(zf)
  # end

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
  # end

  if loaded_count > 1:
    data.set_unique_labels()
  # end

  verb_print(ctx, "Finishing R-Z mapping.")
