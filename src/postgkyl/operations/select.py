"""The ``select`` verb — subselect coordinates and components."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl import dg
from postgkyl.numerics import idx_parser

if TYPE_CHECKING:
  from postgkyl.gdatastate.gdatastate import GDataState
# end


def select(data: "GDataState", *, comp=None,
    z0=None, z1=None, z2=None, z3=None, z4=None, z5=None,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """Select part of a dataset by coordinate (``z0``-``z5``) and/or component.

  Each selector accepts an int index, a float coordinate value, or a slice
  string ``"start:end"``; ``comp`` additionally accepts ``"a,b"``. Unspecified
  axes are kept in full. The selected dimension is retained (length-1), matching
  the legacy behaviour.

  A curvilinear axis (a multi-dimensional grid array, produced by ``.map()``
  with ``space="conf"``) has no single 1-D coordinate array to search, so a
  coordinate/slice-string selector on that axis raises; an integer index
  still works, as does a separable (1-D) mapped axis (``.map(space="vel")``).

  Raises:
    ValueError: if ``data`` holds native modal DG coefficients (nodal/quad
      representations of gkyl-backed data are point values and slice fine),
      or a coordinate/slice selector targets a curvilinear grid axis.
  """
  if data.backend == "gkyl" and data.ctx.get("representation", "modal") == "modal":
    raise ValueError(
        "select operates on interpolated (NumPy) values, or on gkyl-native "
        "nodal/quad representations; call .interpolate()/.to_nodal()/"
        ".to_quad() first -- slicing raw modal DG coefficients would mix "
        "basis functions.")
  # end
  zs = (z0, z1, z2, z3, z4, z5)
  grid = list(data.grid)
  values = data.values
  num_dims = data.num_dims
  values_idx = [slice(0, values.shape[d]) for d in range(num_dims + 1)]

  for d, z in enumerate(zs):
    if d >= num_dims or z is None:
      continue
    # end
    grid_arr = grid[d]
    curvilinear = grid_arr.ndim > 1  # a .map()-deformed, non-separable axis
    if curvilinear and not isinstance(z, int):
      raise ValueError(
          f"select: z{d}'s grid axis is multi-dimensional (curvilinear, "
          "produced by .map()); coordinate values and slice strings have "
          f"no single coordinate array to match against -- pass an "
          f"integer index for z{d} instead.")
    # end
    # grid holds edges (cells+1) -> is_matching is usually False; a
    # curvilinear array's own axis k corresponds to absolute dimension
    # `offset + k` (map.py's mapped block), not to axis d of `grid` itself
    # -- ctx["mapped_axes"] records each absolute dimension's block offset
    # so the N-D array can be indexed on its own relative axis.
    rel = d - data.ctx.get("mapped_axes", {}).get(d, 0) if curvilinear else d
    len_grid = grid_arr.shape[rel] if curvilinear else grid_arr.shape[0]
    is_matching = values.shape[d] == len_grid
    idx = z if curvilinear else idx_parser(z, grid_arr, is_matching)
    if isinstance(idx, int):
      if idx < 0:
        idx = values.shape[d] + idx
      # end
      v_idx = slice(idx, idx + 1)
      g_idx = slice(idx, idx + 1) if is_matching else slice(idx, idx + 2)
    # end
    elif isinstance(idx, slice):
      v_idx = idx
      g_idx = idx if is_matching else slice(idx.start, idx.stop + 1)
    # end
    else:
      raise TypeError("Coordinate selector must be a single index or a slice.")
    # end
    if curvilinear:  # slice only the N-D grid array's own relative axis
      grid[d] = grid_arr[tuple(g_idx if k == rel else slice(None)
          for k in range(grid_arr.ndim))]
    # end
    else:
      grid[d] = grid_arr[g_idx]
    # end
    values_idx[d] = v_idx
  # end

  if comp is not None:
    values_idx[-1] = idx_parser(comp)
  # end

  values_out = values[tuple(values_idx)]
  if num_dims == values_out.ndim:  # restore the squeezed component axis
    values_out = values_out[..., np.newaxis]
  # end

  if data.backend == "gkyl":
    # A nodal/quad representation stays gkyl-native (REFACTOR_GKEYLL_FFI.md
    # §3b): ``values`` above was only a read-only NumPy *view* of the native
    # array for slicing purposes -- wrap the sliced result back into a
    # native GkylArray so the dataset doesn't silently fall out of the gkyl
    # backend (and lose its representation) just for having been selected.
    values_out = dg.rep.wrap(values_out)
  # end

  return data._result(grid, values_out, inplace=inplace, tag=tag, label=label)
# end
