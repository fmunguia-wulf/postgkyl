"""The ``growth`` verb — fit an exponential growth rate to DynVector data.

Returns a new ``GData`` of the fitted exponential ``exp2(t)``; the fitted
growth rate is stored in ``ctx['growth_rate']``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl.tools.growth import fit_growth as _fit_growth, exp2 as _exp2

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def growth(data: "GData", *, guess=None, minn: int | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Fit ``e^(2 b t)`` to ``data`` and return the fitted exponential curve."""
  time = data.get_grid()
  values = data.get_values()
  x = time[0]
  y = values[..., 0].squeeze()

  p0 = None
  if guess is not None:
    if isinstance(guess, str):
      parts = guess.split(",")
      p0 = (float(parts[0]), float(parts[1]))
    else:
      p0 = tuple(guess)
    # end
  # end

  best_params, _r2, _n = _fit_growth(x, y, min_N=minn, p0=p0)
  t = 0.5 * (x[:-1] + x[1:])
  out_val = _exp2(t, *best_params)
  return data._result([x], out_val[..., np.newaxis], inplace=inplace, tag=tag,
      label=label, growth_rate=best_params[1])
