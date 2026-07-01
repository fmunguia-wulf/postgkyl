"""The ``dg_local_poly`` verb — discontinuous cellwise DG polynomial.

Evaluates the modal DG decomposition at ``npoints`` per cell from one face to
the other and inserts a NaN at every cell interface so that, when plotted, the
curve breaks at each interface and the inter-cell discontinuities of the DG
solution become visible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl.data.dg import _getnum_nodes
from postgkyl.modalDG.kernels import (expand_1d, expand_2d, expand_3d,
    expand_4d, expand_5d, expand_6d)

if TYPE_CHECKING:
  from postgkyl.data import GData
# end

_EXPAND = {1: expand_1d, 2: expand_2d, 3: expand_3d,
    4: expand_4d, 5: expand_5d, 6: expand_6d}


def _dg_local_poly_arrays(data: "GData", npoints: int) -> tuple:
  """Compute the (grid, values) of the cellwise DG polynomial representation."""
  poly_order = data.ctx.get("poly_order")
  if poly_order is None:
    raise ValueError("dg_local_poly: no 'poly_order' is available on dataset "
        f"{data.get_label():s}; it could not be auto-detected.")
  # end

  num_dims = data.get_num_dims()
  num_cells = data.get_num_cells()
  values = data.get_values()

  num_basis = int(_getnum_nodes(num_dims, poly_order, "serendipity"))
  num_eqn = int(data.get_num_comps() // num_basis)

  # Reference evaluation nodes spanning the cell, just inside the interfaces.
  nodes = np.linspace(-1.0, 1.0, npoints)
  num_nodes = len(nodes)
  expand = _EXPAND[num_dims][int(poly_order - 1)]

  # Evaluate the modal decomposition of each field at the interior nodes.
  int_values = np.zeros(tuple(np.int32(num_cells * num_nodes)) + (num_eqn,))
  for m in range(num_eqn):
    # Raw modal coefficients of field m, shape (..., num_basis).
    q = values[..., m * num_basis:(m + 1) * num_basis]
    for idx in np.ndindex(*([num_nodes] * num_dims)):
      slices = tuple(slice(i, None, num_nodes) for i in idx) + (m,)
      coords = tuple(nodes[i] for i in idx)
      int_values[slices] = expand(q, *coords)
    # end
  # end

  # Build the grid with the physical coordinates of the nodes.
  grid_in = data.get_grid()
  lower, upper = data.get_bounds()
  int_grid = []
  for d in range(num_dims):
    g = np.squeeze(np.asarray(grid_in[d]))
    if g.ndim == 1 and g.shape[0] == num_cells[d] + 1:
      edges_d = g
    else:
      edges_d = np.linspace(lower[d], upper[d], num_cells[d] + 1)
    # end
    cell_center = 0.5 * (edges_d[:-1] + edges_d[1:])
    dx = edges_d[1:] - edges_d[:-1]
    coords = (cell_center[:, np.newaxis]
        + nodes[np.newaxis, :] * dx[:, np.newaxis] / 2).reshape(-1)
    int_grid.append(coords)
  # end

  # Insert a NaN between every couple of points along each dimension to break
  # the curve at the cell interfaces.
  for d in range(num_dims):
    sep = np.arange(num_nodes, num_nodes * num_cells[d], num_nodes)
    int_values = np.insert(int_values, sep, np.nan, axis=d)
    int_grid[d] = np.insert(int_grid[d], sep, int_grid[d][sep - 1])
  # end

  return int_grid, int_values


def dg_local_poly(data: "GData", *, npoints: int = 2, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Discontinuous cellwise DG polynomial representation of the data.

  The modal DG decomposition is evaluated with ``npoints`` per cell from one
  face to the other, with a NaN inserted at every cell interface so that a plot
  breaks the curve at each interface and shows the DG discontinuities.

  Args:
    data: GData
      The dataset holding raw modal DG coefficients (needs ``poly_order`` in
      its ``ctx``).
    npoints: int
      Number of evaluation points per cell (default 2).
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the cellwise polynomial (or the mutated input when
    inplace=True).
  """
  grid, values = _dg_local_poly_arrays(data, npoints)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
