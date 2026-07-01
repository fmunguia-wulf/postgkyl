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

  Returns a dataset whose values are a ``numpy.ma`` masked array. Exactly one
  of the masking modes is applied, with ``filename`` taking precedence:

  - ``filename``: mask cells where the mask field (read from the file and
    repeated across components) is negative.
  - ``lower`` and ``upper``: mask values outside the closed range
    ``[lower, upper]``.
  - ``lower`` only: mask values below ``lower``.
  - ``upper`` only: mask values above ``upper``.

  Args:
    data: GData
      The dataset to mask.
    filename: str | None
      Path to a Gkeyll mask file; cells where its field is negative are
      masked. Takes precedence over ``lower``/``upper`` when given.
    lower: float | None
      Lower threshold. Combined with ``upper`` masks outside the range;
      alone masks values below it.
    upper: float | None
      Upper threshold. Combined with ``lower`` masks outside the range;
      alone masks values above it.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData whose values are a masked array (or the mutated input when
    inplace=True).

  Raises:
    ValueError: If none of ``filename``, ``lower``, or ``upper`` is provided.
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
