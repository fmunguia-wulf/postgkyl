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

  Stacks many single-frame datasets into one dataset that has a new leading
  (time) axis. The per-dataset time stamp is taken from ``ctx['time']``, then
  ``ctx['frame']``, then the position in the sequence as a fallback. Frames are
  sorted by their (possibly folded) time stamp.

  Args:
    datasets: Iterable[GData]
      The datasets to collect. Each is assumed to share the same grid and
      component layout. Must be non-empty.
    sumdata: bool
      When True, sum each frame over all of its spatial axes (keeping
      components) before stacking, so the output grid is just the time axis.
      When False, the full spatial data of each frame is retained and the time
      axis is inserted as a new leading dimension.
    period: float | None
      When given (truthy), fold the time stamps into one period via
      ``(time - offset) % period`` before sorting, producing a phase/epoch
      axis. None leaves the time axis unfolded.
    offset: float
      Phase offset subtracted before the modulo when ``period`` is used.
      Defaults to 0.0.
    tag: str | None
      Tag for the returned dataset. Defaults to 'default' when None.
    label: str | None
      Label for the returned dataset. Defaults to 'collect' when None.

  Returns:
    A new GData with the collected frames stacked along a new leading time
    axis.

  Raises:
    ValueError: If ``datasets`` is empty.
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
