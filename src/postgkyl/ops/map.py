"""The ``map`` verb — deform a dataset's grid onto non-uniform coordinates.

A coordinate map is stored as its own DG field whose components are the physical
coordinates of each computational node: ``mapc2p`` / ``mc2nu`` map configuration
space, ``mapc2p_vel`` maps velocity space. This verb reads such a mapping field,
interpolates it, and replaces the corresponding block of grid axes of the target
dataset with the resulting non-uniform coordinates.

Coordinate mapping used to happen *while reading* a file (the old ``c2p`` /
``c2p_vel`` load options). It now lives here, as an ordinary verb that operates
on already-loaded — typically already-interpolated — data, so it composes with
the rest of the verb pipeline and keeps the readers free of grid math.

A configuration-space map (``space='conf'``) deforms the leading ``cdim`` axes
and is fully *curvilinear*: each physical coordinate is interpolated over all of
the map's dimensions, so non-separable maps (e.g. a rotation) are handled. A
velocity-space map (``space='vel'``) deforms the trailing ``vdim`` axes and is
*separable* (each velocity coordinate depends only on its own index). There is
no dedicated "both" mode — for a combined map, apply the verb twice, once per
space::

    f.map('sim-mc2nu.gkyl', space='conf') \\
     .map('sim-mapc2p_vel.gkyl', space='vel')
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.data import GData
from postgkyl.data.dg import interp_c2p_conf_grid, interp_c2p_vel_grid

if TYPE_CHECKING:
  from postgkyl.data import GData as _GData
# end


def map(data: "_GData", mapping: "str | _GData", *, space: str = "conf",
    interp: "int | None" = None, inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "_GData":
  """Replace a block of ``data``'s grid axes with non-uniform mapped coordinates.

  Reads a coordinate-mapping DG field, interpolates it onto node coordinates,
  and replaces the matching grid axes of ``data``. The values array is left
  untouched; only the grid changes. The interpolation resolution is matched to
  ``data``'s current grid automatically (so this lines up with already-
  interpolated data); pass ``interp`` to override it.

  Args:
    data: GData
      The dataset whose grid is deformed.
    mapping: str | GData
      The coordinate-mapping field, as a filename or an already-loaded GData.
      Its number of dimensions sets how many of ``data``'s axes are replaced;
      the basis is inferred from its component count.
    space: str
      ``'conf'`` deforms the leading axes (offset 0) curvilinearly; ``'vel'``
      deforms the trailing axes (offset ``data.num_dims - mapping.num_dims``)
      separably. For a combined map, apply the verb twice.
    interp: int | None
      Number of interpolation points per cell for the mapping field. When None
      (the default), it is derived per axis from ``data``'s value shape so the
      mapped grid aligns with the (already-interpolated) data.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A GData carrying the deformed grid (a new GData unless inplace=True).
  """
  map_data = mapping if isinstance(mapping, GData) else GData(mapping)
  map_dim = map_data.get_num_dims()
  num_dims = data.get_num_dims()

  if space == "conf":
    offset = 0
  elif space == "vel":
    offset = num_dims - map_dim
  else:
    raise ValueError(
        f"map: 'space' must be 'conf' or 'vel', got {space!r}.")
  # end

  if offset < 0 or offset + map_dim > num_dims:
    raise ValueError(
        f"map: a {map_dim}D {space} map does not fit a {num_dims}D dataset.")
  # end

  # Match the mapping's interpolation resolution to the target grid so the new
  # axes line up with the data: a field interpolated at num_interp points/cell
  # has cells*num_interp value points, and the mapping (on the same cells)
  # needs the same factor to produce cells*num_interp+1 aligned nodes.
  value_cells = data.get_values().shape
  map_cells = map_data.get_num_cells()
  if interp is None:
    num_interp = [int(value_cells[offset + d] // map_cells[d])
        for d in range(map_dim)]
  else:
    num_interp = [int(interp)] * map_dim
  # end

  if space == "conf":
    # Curvilinear maps share a single interpolation matrix across dims; the
    # per-cell factor is uniform over configuration space.
    coords = interp_c2p_conf_grid(map_data, num_interp[0])
  else:
    coords = interp_c2p_vel_grid(map_data, num_interp)
  # end

  new_grid = list(data.get_grid())
  for d in range(map_dim):
    new_grid[offset + d] = coords[d]
  # end

  return data._result(new_grid, data.get_values(), inplace=inplace,
      tag=tag, label=label)
