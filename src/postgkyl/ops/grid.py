"""The ``grid`` verb — turn a dataset's grid into a dataset of coordinates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def grid(data: "GData", *, inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GData":
  """Create a dataset whose values are the physical coordinates of ``data``'s grid."""
  grid_in = data.get_grid()
  num_dims = data.get_num_dims()
  num_cells = data.get_num_cells()

  grid_out = [np.arange(nc + 2) for nc in num_cells]

  shape = np.append(np.copy(num_cells) + 1, num_dims)
  values = np.zeros(shape)
  if num_dims == 1:
    values[..., 0] = grid_in[0]
  elif len(grid_in[0].shape) == 1:  # uniform mesh or vel c2p mapping
    for d, t in enumerate(np.meshgrid(*grid_in, indexing="ij")):
      values[..., d] = t
    # end
  else:  # c2p mapping
    for d, t in enumerate(grid_in):
      values[..., d] = t
    # end
  # end
  return data._result(grid_out, values, inplace=inplace, tag=tag, label=label)
