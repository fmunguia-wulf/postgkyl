"""Grid construction for Gkeyll output — uniform and coordinate-mapped (c2p).

A Gkeyll field stores only its *values*; the grid is either built uniformly
from the stored bounds or read from a companion ``mapc2p`` file. The readers
differ in *how* they read that companion file (the binary reader nests another
``GkylReader``; the ADIOS reader uses ``adios2``), but the grid *math* — how
those node values become a per-dimension grid, and how a uniform grid accounts
for ghost cells — is identical. That shared math lives here so it is written and
tested once, and the readers only decide which strategy to apply.

Grid strategies (mirrored by ``ctx['grid_type']``):
  - ``uniform``  : evenly spaced from bounds, corrected for ghost cells.
  - ``c2p``      : node coordinates from a configuration-space mapping file.
  - ``c2p_vel``  : uniform configuration grid + non-uniform velocity grid.
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


def c2p_grid(nodes: np.ndarray, num_dims: int) -> list:
  """Split a configuration-space ``mapc2p`` node array into a per-dim grid.

  The mapping file packs every dimension's node coordinates on the last axis;
  this slices that axis into ``num_dims`` equal blocks.
  """
  num_comps = nodes.shape[-1]
  num_coeff = num_comps / num_dims
  return [nodes[..., int(d * num_coeff):int((d + 1) * num_coeff)]
      for d in range(num_dims)]


def c2p_vel_grid(nodes: np.ndarray, lower: np.ndarray, upper: np.ndarray,
    cells: np.ndarray, num_dims: int) -> tuple:
  """Build a grid from a velocity-space mapping (uniform config + mapped vel).

  Configuration dimensions get a uniform grid from the bounds; velocity
  dimensions get their (non-uniform) node coordinates from ``nodes``.

  Returns ``(grid, num_cdim, num_vdim)``.
  """
  num_vdim = len(nodes.shape) - 1
  num_cdim = num_dims - num_vdim

  # Uniform configuration-space grid.
  grid = [np.linspace(lower[d], upper[d], cells[d] + 1)
      for d in range(num_cdim)]

  # Non-uniform velocity-space grid.
  num_comps = nodes.shape[-1]
  num_coeff = num_comps / num_vdim
  for d in range(num_vdim):
    idx = [0] * (num_vdim + 1)
    idx[d] = slice(None)
    idx[-1] = slice(int(d * num_coeff), int((d + 1) * num_coeff))
    grid.append(nodes[tuple(idx)])
  # end
  return grid, num_cdim, num_vdim
