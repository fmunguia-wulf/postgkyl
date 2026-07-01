"""Pure-array helpers for element-wise dataset arithmetic."""

from __future__ import annotations

import numpy as np


def grids_compatible(grid_a: list, grid_b: list, rtol: float = 1e-9) -> bool:
  """Whether two nodal grids describe the same mesh (same shapes & nodes)."""
  if len(grid_a) != len(grid_b):
    return False
  return all(a.shape == b.shape and np.allclose(a, b, rtol=rtol)
             for a, b in zip(grid_a, grid_b))
