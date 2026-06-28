"""The ``collect`` verb — combine many datasets into one along a new time axis."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def collect(datasets, *, sumdata: bool = False, period: float | None = None,
    offset: float = 0.0, tag: str | None = None, label: str | None = None) -> "GData":
  """Collect a sequence of datasets into a single dataset.

  The per-dataset time stamp (``ctx['time']``, else ``ctx['frame']``, else the
  index) becomes a new leading axis. With ``sumdata=True`` each frame is summed
  over its spatial axes (retaining components). ``period``/``offset`` fold the
  time axis into an epoch.
  """
  from postgkyl.data.gdata import GData

  datasets = list(datasets)
  if not datasets:
    raise ValueError("collect: no datasets to collect.")
  # end

  time = []
  values = []
  grid = None
  for i, dat in enumerate(datasets):
    stamp = dat.ctx.get("time")
    if stamp is None:
      stamp = dat.ctx.get("frame")
    # end
    if stamp is None:
      stamp = i
    # end
    time.append(stamp)

    val = dat.get_values()
    if sumdata:
      axis = tuple(range(dat.get_num_dims()))
      values.append(np.nansum(val, axis=axis))
    else:
      values.append(val)
    # end
    if grid is None:
      grid = list(dat.get_grid())
    # end
  # end

  time = np.array(time)
  values = np.array(values)

  if period:
    time = (time - offset) % period
  # end

  sort_idx = np.argsort(time)
  time = time[sort_idx]
  values = values[sort_idx]

  if sumdata:
    out_grid = [time]
  else:
    out_grid = list(grid)
    out_grid.insert(0, np.array(time))
  # end

  out = GData(tag=(tag or "default"), label=(label if label is not None else "collect"))
  out.push(out_grid, values)
  return out
