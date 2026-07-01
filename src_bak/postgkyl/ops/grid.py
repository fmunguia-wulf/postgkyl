"""The ``grid`` verb — turn a dataset's grid into a dataset of coordinates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def grid(data: "GData", *, inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GData":
  """Turn a dataset's grid into a dataset of coordinate values.

  Builds a new dataset whose values, at each node, are the physical
  coordinates of ``data``'s grid (one component per dimension). Handles
  uniform meshes, separable (velocity) mappings, and full curvilinear
  mapped grids produced by the ``map`` verb.

  Args:
    data: GData
      The dataset whose grid is converted to coordinate values.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData with one component per dimension holding the physical
    coordinates (or the mutated input when inplace=True).
  """
  grid_in = data.get_grid()
  num_dims = data.get_num_dims()
  num_cells = data.get_num_cells()

  grid_out = [np.arange(nc + 2) for nc in num_cells]

  shape = np.append(np.copy(num_cells) + 1, num_dims)
  values = np.zeros(shape)
  if num_dims == 1:
    values[..., 0] = grid_in[0]
  elif len(grid_in[0].shape) == 1:  # uniform mesh or separable mapping
    for d, t in enumerate(np.meshgrid(*grid_in, indexing="ij")):
      values[..., d] = t
    # end
  else:  # curvilinear mapped grid
    for d, t in enumerate(grid_in):
      values[..., d] = t
    # end
  # end
  return data._result(grid_out, values, inplace=inplace, tag=tag, label=label)
