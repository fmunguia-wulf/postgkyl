"""The ``select`` (``sel``) verb — subselect coordinates and components."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl.numerics import idx_parser

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def select(data: "GDataState", *, comp=None,
    z0=None, z1=None, z2=None, z3=None, z4=None, z5=None,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """Select part of a dataset by coordinate (``z0``-``z5``) and/or component.

  Each selector accepts an int index, a float coordinate value, or a slice
  string ``"start:end"``; ``comp`` additionally accepts ``"a,b"``. Unspecified
  axes are kept in full. The selected dimension is retained (length-1), matching
  the legacy behaviour.
  """
  zs = (z0, z1, z2, z3, z4, z5)
  grid = list(data.grid)
  values = data.values
  num_dims = data.num_dims
  values_idx = [slice(0, values.shape[d]) for d in range(num_dims + 1)]

  for d, z in enumerate(zs):
    if d >= num_dims or z is None:
      continue
    # end
    len_grid = grid[d].shape[0]
    is_matching = values.shape[d] == len_grid  # grid holds edges (cells+1) -> usually False
    idx = idx_parser(z, grid[d], is_matching)
    if isinstance(idx, int):
      if idx < 0:
        idx = values.shape[d] + idx
      v_idx = slice(idx, idx + 1)
      g_idx = slice(idx, idx + 1) if is_matching else slice(idx, idx + 2)
    elif isinstance(idx, slice):
      v_idx = idx
      g_idx = idx if is_matching else slice(idx.start, idx.stop + 1)
    else:
      raise TypeError("Coordinate selector must be a single index or a slice.")
    # end
    grid[d] = grid[d][g_idx]
    values_idx[d] = v_idx
  # end

  if comp is not None:
    values_idx[-1] = idx_parser(comp)
  # end

  values_out = values[tuple(values_idx)]
  if num_dims == values_out.ndim:  # restore the squeezed component axis
    values_out = values_out[..., np.newaxis]
  # end

  return data._result(grid, values_out, inplace=inplace, tag=tag, label=label)
