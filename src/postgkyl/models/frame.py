"""Distribution-function frame transform — shift a particle distribution
function's velocity grid by a bulk velocity."""

from __future__ import annotations

import numpy as np


def transform_frame(f_grid: list[np.ndarray], f_values: np.ndarray,
    u_values: np.ndarray, c_dim: int,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Shift a distribution function to a different frame of reference.

  Shifts the velocity-space grid of a distribution function by a supplied
  bulk velocity (a magnetic-field-direction shift is not yet supported).

  Args:
    f_grid: Nodal coordinate arrays, one per configuration- and
      velocity-space dimension (configuration dimensions first).
    f_values: Particle distribution function values (unchanged by the
      shift; only the velocity grid moves).
    u_values: Bulk velocity array, ``num_dims - c_dim`` components, on the
      configuration-space grid.
    c_dim: Number of configuration-space dimensions.

  Returns:
    ``(grid, values)``: a per-cell-shifted velocity grid (one nodal array
    per dimension, matching the input's dimensionality) and the unchanged
    distribution-function values.
  """
  v_dim = len(f_grid) - c_dim
  out_grid = np.meshgrid(*f_grid, indexing="ij")

  if c_dim == 1:
    for v_idx in range(v_dim):
      nx = f_grid[0].shape[0]

      ext_u = np.zeros(nx)
      ext_u[:-1] += u_values[..., v_idx]
      ext_u[1:] += u_values[..., v_idx]
      ext_u[1:-1] = ext_u[1:-1] / 2

      for i in range(nx):
        out_grid[c_dim + v_idx][i, ...] += ext_u[i]

  elif c_dim == 2:
    for v_idx in range(v_dim):
      nx = f_grid[0].shape[0]
      ny = f_grid[1].shape[0]

      ext_u = np.zeros((nx, ny))
      ext_u[:-1, :-1] += u_values[..., v_idx]
      ext_u[1:, 1:] += u_values[..., v_idx]
      ext_u[1:-1, 1:-1] = ext_u[1:-1, 1:-1] / 2

      for i in range(nx):
        for j in range(ny):
          out_grid[c_dim + v_idx][i, j, ...] += ext_u[i, j]

  else:
    for v_idx in range(v_dim):
      nx = f_grid[0].shape[0]
      ny = f_grid[1].shape[0]
      nz = f_grid[2].shape[0]

      ext_u = np.zeros((nx, ny, nz))
      ext_u[:-1, :-1, :-1] += u_values[..., v_idx]
      ext_u[1:, 1:, 1:] += u_values[..., v_idx]
      ext_u[1:-1, 1:-1, 1:-1] = ext_u[1:-1, 1:-1, 1:-1] / 2

      for i in range(nx):
        for j in range(ny):
          for k in range(nz):
            out_grid[c_dim + v_idx][i, j, k, ...] += ext_u[i, j, k]

  return out_grid, f_values
