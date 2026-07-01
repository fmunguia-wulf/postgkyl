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
  """Fit an exponential growth rate to DynVector data.

  Fits the model ``a * exp(2 b t)`` to the first component of ``data`` (a time
  series / DynVector), searching over a range of fit-window lengths and
  keeping the window with the best coefficient of determination. The factor of
  two reflects that an energy-like quantity (amplitude squared) is typically
  used. The fitted curve is returned and the growth rate ``b`` is stored in
  the result's ``ctx['growth_rate']``.

  Args:
    data: GData
      Time-series data; the grid's first axis is time and the first component
      is fit.
    guess: str | Sequence[float] | None
      Initial guess ``(a, b)`` for the scaling and growth rate. A
      comma-separated string (e.g. '1,1') or a sequence of two floats. None
      uses the fitter's default.
    minn: int | None
      Minimum number of leading points to include in the fitting window. None
      defaults to one tenth of the number of samples.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the fitted exponential evaluated at cell-centered times,
    with ``ctx['growth_rate']`` set to the fitted growth rate (or the mutated
    input when inplace=True).
  """
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
