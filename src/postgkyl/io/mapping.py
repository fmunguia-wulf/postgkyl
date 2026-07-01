"""Read-time grid construction for Gkeyll output.

A Gkeyll field stores only its *values*; at read time the grid is built
uniformly from the stored bounds (corrected for ghost cells). Coordinate
(computational-to-physical) mappings are applied afterwards by the ``map`` verb
(not part of this minimal port).
"""

from __future__ import annotations

import numpy as np


def adjust_for_ghost_cells(lower: np.ndarray, upper: np.ndarray,
    cells: np.ndarray, data_shape: tuple) -> tuple:
  """Shrink the cell count / extend the bounds to account for ghost cells.

  When the stored data has fewer cells along a dimension than ``cells``
  advertises, the difference is ghost cells; the bounds are pushed out by the
  ghost-cell width so the resulting grid still maps onto the data. ``lower``,
  ``upper`` and ``cells`` are mutated in place and also returned.
  """
  num_dims = len(cells)
  dz = (upper - lower) / cells
  for d in range(num_dims):
    if cells[d] != data_shape[d]:
      ngl = int(np.floor((cells[d] - data_shape[d]) * 0.5))
      ngu = int(np.ceil((cells[d] - data_shape[d]) * 0.5))
      cells[d] = data_shape[d]
      lower[d] = lower[d] - ngl * dz[d]
      upper[d] = upper[d] + ngu * dz[d]
    # end
  # end
  return lower, upper, cells


def uniform_grid(lower: np.ndarray, upper: np.ndarray,
    cells: np.ndarray) -> list:
  """A uniform nodal grid: ``cells[d] + 1`` edges per dimension."""
  return [np.linspace(lower[d], upper[d], cells[d] + 1)
      for d in range(len(cells))]
