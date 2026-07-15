"""The ``collect`` verb — combine many datasets into one along a new time axis."""

from __future__ import annotations

import numpy as np

from postgkyl.gdatastate import flatten_datasets
from postgkyl.gdatastate.gdatastate import GDataState


def collect(*datasets, sumdata: bool = False, period: float | None = None,
    offset: float = 0.0, tag: str | None = None, label: str | None = None
    ) -> GDataState:
  """Collect many single-frame datasets into one with a new leading time axis.

  Accepts ``collect(a, b)`` or ``collect([a, b])`` (flattened via
  ``gdatastate.flatten_datasets``). The per-dataset time stamp is taken from
  ``ctx['time']``, then ``ctx['frame']``, then the dataset's position in the
  sequence as a fallback; frames are sorted by their (possibly folded) time
  stamp. The result copies the grid/ctx of the first frame (via its
  ``_result``), so it stays the caller's concrete dataset class.

  Args:
    *datasets: the datasets to collect (each NumPy-backed, sharing a grid
      and component layout), or lists/groups thereof.
    sumdata: when True, sum each frame over all of its spatial axes (keeping
      components) before stacking, so the output grid is just the time
      axis. When False the full spatial data of each frame is retained and
      the time axis becomes a new leading dimension.
    period: when given, fold the time stamps into one period via
      ``(time - offset) % period`` before sorting, producing a phase/epoch
      axis instead of an unfolded time axis.
    offset: phase offset subtracted before the modulo when ``period`` is
      used.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset (defaults to ``'collect'``).

  Returns:
    A dataset with the collected frames stacked along a new leading time
    axis.

  Raises:
    ValueError: if there are no datasets to collect, or one is native modal
      (gkyl-backed).
  """
  states = flatten_datasets(datasets)
  if not states:
    raise ValueError("collect: no datasets to collect.")
  # end

  time, values = [], []
  grid = None
  for i, dat in enumerate(states):
    if dat.backend == "gkyl":
      raise ValueError(
          f"collect operates on interpolated (NumPy) values; call .interpolate() "
          f"first on dataset {i} -- stacking raw DG coefficients would mix "
          f"basis functions.")
    # end
    stamp = dat.ctx.get("time", dat.ctx.get("frame", i))
    time.append(stamp)

    val = dat.values
    if sumdata:
      values.append(np.nansum(val, axis=tuple(range(dat.num_dims))))
    # end
    else:
      values.append(val)
    # end
    if grid is None:
      grid = list(dat.grid)
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

  out_grid = [time] if sumdata else [np.array(time)] + grid
  return states[0]._result(out_grid, values, tag=(tag or "default"),
      label=(label if label is not None else "collect"))
# end
