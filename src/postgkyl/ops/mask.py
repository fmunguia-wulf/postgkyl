"""The ``mask`` verb — mask out values by a mask file or by thresholds."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def mask(data: "GData", *, filename: str | None = None,
    lower: float | None = None, upper: float | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Mask out values using a Gkeyll mask file or numeric thresholds.

  - ``filename``: mask where the mask field is negative.
  - ``lower`` and ``upper``: mask values outside ``[lower, upper]``.
  - ``lower`` only / ``upper`` only: mask values below / above the threshold.
  """
  values = data.get_values()
  if filename:
    from postgkyl.data.gdata import GData as _GData
    mask_fld = _GData(filename).get_values()
    mask_rep = np.repeat(mask_fld, data.get_num_comps(), axis=-1)
    masked = np.ma.masked_where(mask_rep < 0.0, values)
  elif lower is not None and upper is not None:
    masked = np.ma.masked_outside(values, lower, upper)
  elif lower is not None:
    masked = np.ma.masked_less(values, lower)
  elif upper is not None:
    masked = np.ma.masked_greater(values, upper)
  else:
    raise ValueError(
        "mask: no masking information specified (provide filename, lower, or upper).")
  # end
  return data._result(data.get_grid(), masked, inplace=inplace, tag=tag, label=label)
