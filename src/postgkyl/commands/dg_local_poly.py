from typing import Optional

import typer
from typing_extensions import Annotated
import numpy as np

from postgkyl.utils import verb_print
from postgkyl.data.dg import _getnum_nodes
from postgkyl.modalDG.kernels import expand_1d, expand_2d, expand_3d, expand_4d, expand_5d, expand_6d


def dg_local_poly(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    npoints: Annotated[Optional[int], typer.Option("--npoints", "-n", help="Number of evaluation points per cell.")] = 2,
):
  """
  Generate a discontinuous DG polynomial cellwise representation of the data.
  The modal DG decomposition is evaluated with npoints per cell from one face
  to the other. A NaN is inserted at every cell interface so that, when plotted,
  the curve is broken at each interface and the inter-cell discontinuities of the DG solution
  are visible.
  Example (1D plot of the M0 moment along x at frame 0):
    pgkyl sim_3x2v_p1-ion_M0_0.gkyl dg-local-poly sel --z1=0.0 --z2=0.0 pl
  """
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting dg-local-poly")
  data = ctx.obj["data"]

  for dat in data.iterator(kwargs["use"]):
    poly_order = dat.ctx.get("poly_order")

    if poly_order is None:
      ctx.fail(typer.style(
          "ERROR in dg-local-poly: no 'poly_order' was specified and dataset "
          f"{dat.get_label():s} does not have the required information.",
          fg="red"))

    num_dims = dat.get_num_dims()

    num_cells = dat.get_num_cells()
    values = dat.get_values()

    num_basis = int(_getnum_nodes(num_dims, poly_order, "serendipity"))
    num_eqn = int(dat.get_num_comps() // num_basis)

    # Reference evaluation nodes: just inside the two cell interfaces.
    nodes = np.linspace(-1.0, 1.0, kwargs["npoints"])
    num_nodes = len(nodes)

    # Evaluate the modal decomposition of each field at the interface nodes.
    int_values = np.zeros(tuple(np.int32(num_cells * num_nodes)) + (num_eqn,))
    for m in range(num_eqn):
      # Raw modal coefficients of field m, shape (..., num_basis).
      q = values[..., m * num_basis:(m + 1) * num_basis]
      if num_dims == 1:
        for i, x in enumerate(nodes):
          int_values[i::num_nodes, m] = expand_1d[int(poly_order - 1)](q, x)
      elif num_dims == 2:
        for i, x in enumerate(nodes):
          for j, y in enumerate(nodes):
            int_values[i::num_nodes, j::num_nodes, m] = expand_2d[
                int(poly_order - 1)](q, x, y)
      elif num_dims == 3:
        for i, x in enumerate(nodes):
          for j, y in enumerate(nodes):
            for k, z in enumerate(nodes):
              int_values[i::num_nodes, j::num_nodes, k::num_nodes, m] = expand_3d[
                  int(poly_order - 1)](q, x, y, z)
      elif num_dims == 4:
        for i, x in enumerate(nodes):
          for j, y in enumerate(nodes):
            for k, z in enumerate(nodes):
              for l, v1 in enumerate(nodes):
                int_values[i::num_nodes, j::num_nodes, k::num_nodes, l::num_nodes,
                           m] = expand_4d[int(poly_order - 1)](q, x, y, z, v1)
      elif num_dims == 5:
        for i, x in enumerate(nodes):
          for j, y in enumerate(nodes):
            for k, z in enumerate(nodes):
              for l, v1 in enumerate(nodes):
                for m1, v2 in enumerate(nodes):
                  int_values[i::num_nodes, j::num_nodes, k::num_nodes,
                             l::num_nodes, m1::num_nodes, m] = expand_5d[
                                 int(poly_order - 1)](q, x, y, z, v1, v2)
      elif num_dims == 6:
        for i, x in enumerate(nodes):
          for j, y in enumerate(nodes):
            for k, z in enumerate(nodes):
              for l, v1 in enumerate(nodes):
                for m1, v2 in enumerate(nodes):
                  for n1, v3 in enumerate(nodes):
                    int_values[i::num_nodes, j::num_nodes, k::num_nodes,
                               l::num_nodes, m1::num_nodes, n1::num_nodes,
                               m] = expand_6d[int(poly_order - 1)](q, x, y, z, v1,
                                                                   v2, v3)
    # Build the grid with the physical coordinates of the nodes.
    grid_in = dat.get_grid()
    lower, upper = dat.get_bounds()
    int_grid = []
    for d in range(num_dims):
      g = np.squeeze(np.asarray(grid_in[d]))
      if g.ndim == 1 and g.shape[0] == num_cells[d] + 1:
        edges_d = g
      else:
        edges_d = np.linspace(lower[d], upper[d], num_cells[d] + 1)
      cell_center = 0.5 * (edges_d[:-1] + edges_d[1:])
      dx = edges_d[1:] - edges_d[:-1]
      coords = (cell_center[:, np.newaxis]
                + nodes[np.newaxis, :] * dx[:, np.newaxis] / 2).reshape(-1)
      int_grid.append(coords)

    # Insert a NaN between every couple of points along each dimension to break
    # the curve at the cell interfaces.
    for d in range(num_dims):
      sep = np.arange(num_nodes, num_nodes * num_cells[d], num_nodes)
      int_values = np.insert(int_values, sep, np.nan, axis=d)
      int_grid[d] = np.insert(int_grid[d], sep, int_grid[d][sep - 1])

    dat.push(int_grid, int_values)
  verb_print(ctx, "Finishing dg-local-poly")
