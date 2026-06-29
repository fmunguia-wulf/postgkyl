"""The ``map`` verb — deform a dataset's grid onto non-uniform coordinates.

A coordinate map is stored as its own DG field whose components are the physical
coordinates of each computational node: ``mapc2p`` / ``mc2nu`` map configuration
space, ``mapc2p_vel`` maps velocity space. This verb reads such a mapping field,
interpolates it, and replaces the corresponding block of grid axes of the target
dataset with the resulting non-uniform coordinates.

Unlike the load-time mapping in :mod:`postgkyl.data.mapping` (which builds the
grid *while reading* a file), ``map`` operates on already-loaded data, so it
composes with the rest of the verb pipeline. A configuration-space map deforms
the leading ``cdim`` axes; a velocity-space map deforms the trailing ``vdim``
axes. There is no dedicated "both" mode — for a combined map, apply the verb
twice, once per space::

    f.map('sim-mc2nu.gkyl', space='conf') \\
     .map('sim-mapc2p_vel.gkyl', space='vel')
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl.data import GData, GInterpModal

if TYPE_CHECKING:
  from postgkyl.data import GData as _GData
# end


def _cell_centered_to_nodal(cell_centers: np.ndarray) -> np.ndarray:
  """Convert cell-centered coordinates to nodal ones (half a cell at each end)."""
  nodes = np.zeros(cell_centers.size + 1, dtype=cell_centers.dtype)
  nodes[1:-1] = 0.5 * (cell_centers[:-1] + cell_centers[1:])
  nodes[0] = cell_centers[0] + (cell_centers[0] - nodes[1])
  nodes[-1] = cell_centers[-1] + (cell_centers[-1] - nodes[-2])
  return nodes


def _extract_axis(mapped_values: np.ndarray, axis: int, map_dim: int) -> np.ndarray:
  """Extract the 1D coordinate profile of mapped component ``axis`` along ``axis``."""
  idx = [0] * (map_dim + 1)  # the mapping field has map_dim dims + 1 component axis
  idx[axis] = slice(None)
  idx[-1] = axis
  return mapped_values[tuple(idx)].reshape(-1)


def map(data: "_GData", mapping: "str | _GData", *, space: str = "conf",
    p: int = 1, basis: str = "ms", interp: int | None = None,
    inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "_GData":
  """Replace a block of ``data``'s grid axes with non-uniform mapped coordinates.

  Reads a coordinate-mapping DG field, interpolates it, and for each of its
  dimensions replaces the matching grid axis of ``data`` with the corresponding
  non-uniform (cell-centered -> nodal) coordinate. The values array is left
  untouched; only the grid changes.

  Args:
    data: GData
      The dataset whose grid is deformed.
    mapping: str | GData
      The coordinate-mapping field, as a filename or an already-loaded GData.
      Its number of dimensions sets how many of ``data``'s axes are replaced.
    space: str
      ``'conf'`` deforms the leading axes (offset 0); ``'vel'`` deforms
      the trailing axes (offset ``data.num_dims - mapping.num_dims``). For a
      combined configuration+velocity map, apply the verb twice.
    p: int
      Polynomial order used to interpolate the mapping field (default 1).
    basis: str
      DG basis of the mapping field (default 'ms').
    interp: int | None
      Optional override for the number of interpolation points.
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

  _, map_values = GInterpModal(map_data, p, basis, interp).interpolate(
      tuple(range(map_dim)))

  new_grid = list(data.get_grid())
  for d in range(map_dim):
    coords = _extract_axis(map_values, d, map_dim)
    new_grid[offset + d] = _cell_centered_to_nodal(coords)
  # end

  return data._result(new_grid, data.get_values(), inplace=inplace,
      tag=tag, label=label)
