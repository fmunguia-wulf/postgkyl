import click
import numpy as np

from postgkyl.utils import verb_print
from postgkyl.data.dg import _getnum_nodes
from postgkyl.modalDG.kernels import expand_1d, expand_2d, expand_3d


@click.command()
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--eps", type=click.FLOAT, default=1e-2,
    help="Fraction of the half-cell width by which the evaluation point is "
         "moved inside from each cell interface (must be in [0, 1]).")
@click.pass_context
def dg(ctx, **kwargs):
  """Generate a discontinuous DG representation of the data.

  \b
  The modal DG decomposition is evaluated at two points per cell, each located
  just inside a cell interface (slightly interior, controlled by --eps). A NaN
  is inserted between every couple of points so that, when plotted, the curve is
  broken at each interface and the inter-cell discontinuities of the DG solution
  are visible.

  \b
  Example (1D plot of the M0 moment along x at frame 0):
    pgkyl prefix-ion_M0_0.gkyl dg sel --z1=0.0 --z2=0.0 pl
  """
  verb_print(ctx, "Starting dg")
  data = ctx.obj["data"]
  eps = kwargs["eps"]

  for dat in data.iterator(kwargs["use"]):
    poly_order = dat.ctx.get("poly_order")
    if not poly_order == 1:
        ctx.fail(click.style(
            "ERROR in dg: only data with poly_order=1 is supported.",
            fg="red"))

    if poly_order is None:
      ctx.fail(click.style(
          "ERROR in dg: no 'poly_order' was specified and dataset "
          f"{dat.get_label():s} does not have the required information.",
          fg="red"))

    num_dims = dat.get_num_dims()
    if num_dims > 3:
      ctx.fail(click.style(
          "ERROR in dg: only data with up to 3 dimensions is supported.",
          fg="red"))

    num_cells = dat.get_num_cells()
    values = dat.get_values()

    num_basis = int(_getnum_nodes(num_dims, poly_order, "serendipity"))
    num_eqn = int(dat.get_num_comps() // num_basis)

    # Reference evaluation nodes: just inside the two cell interfaces.
    nodes = np.array([-1.0 + eps, 1.0 - eps])
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
  verb_print(ctx, "Finishing dg")
