"""The ``val2coord`` verb — build new datasets from columns of a DynVector."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def _get_range(str_in: str, length: int) -> np.ndarray:
  if len(str_in.split(",")) > 1:
    return np.array(str_in.split(","), dtype=int)
  elif str_in.find(":") >= 0:
    parts = str_in.split(":")
    s_idx = 0 if parts[0] == "" else int(parts[0])
    if s_idx < 0:
      s_idx = length + s_idx
    # end
    e_idx = length if parts[1] == "" else int(parts[1])
    if e_idx < 0:
      e_idx = length + e_idx
    # end
    inc = int(parts[2]) if len(parts) > 2 and parts[2] != "" else 1
    return np.arange(s_idx, e_idx, inc)
  else:
    return np.array([int(str_in)])
  # end


def val2coord(data: "GData", *, x: str, y: str, periodic: bool = False,
    tag: str | None = None, label: str | None = None):
  """Select columns of ``data`` to form new (x, y) datasets.

  ``x``/``y`` are component selectors (index, comma list, or 'lo:hi:step'). One
  output dataset is produced per selected y-component, returned as a
  :class:`postgkyl.group.DatasetGroup`.
  """
  from postgkyl.group import DatasetGroup

  values = data.get_values()
  x_comps = _get_range(x, len(values[0, :]))
  y_comps = _get_range(y, len(values[0, :]))

  if len(x_comps) > 1 and len(x_comps) != len(y_comps):
    raise ValueError(
        f"val2coord: number of x-components ({len(x_comps)}) is greater than 1 "
        f"and not equal to the number of y-components ({len(y_comps)}).")
  # end

  out = []
  for i, yc in enumerate(y_comps):
    xc = x_comps[i] if len(x_comps) > 1 else x_comps[0]
    xv = values[..., xc]
    yv = values[..., yc]
    if periodic:
      xv = np.append(xv, np.atleast_1d(xv[0]), axis=0)
      yv = np.append(yv, np.atleast_1d(yv[0]), axis=0)
    # end
    res = data._result([xv], yv[..., np.newaxis], tag=tag, label=label)
    res.color = "C0"
    out.append(res)
  # end
  return DatasetGroup(out)
