"""The ``growth`` verb — fit an exponential growth rate to DynVector data.

Returns a dataset of the fitted exponential ``exp2(t)``; the fitted growth
rate is stored in ``ctx['growth_rate']``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl import numerics

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def growth(data: "GDataState", *, guess=None, minn: int | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """Fit an exponential growth rate to DynVector (time-series) data.

  Fits ``a * exp(2 b t)`` (``numerics.exp2``) to the first component of
  ``data``, searching over a range of fit-window lengths and keeping the
  window with the best coefficient of determination. The factor of two
  reflects that an energy-like quantity (amplitude squared) is typically
  used.

  Args:
    data: time-series data; must be NumPy-backed. The grid's first axis is
      time and the first component is fit.
    guess: initial guess ``(a, b)`` for the scaling and growth rate -- a
      comma-separated string (e.g. ``'1,1'``) or a sequence of two floats.
      None uses the fitter's default.
    minn: minimum number of leading points to include in the fitting
      window. None defaults to one tenth of the number of samples.
    inplace: mutate and return ``data`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset of the fitted exponential evaluated at cell-centered times,
    with ``ctx['growth_rate']`` set to the fitted growth rate.

  Raises:
    ValueError: if ``data`` is native modal (gkyl-backed).
    RuntimeError: if the fit fails to converge for every candidate window.
  """
  if data.backend == "gkyl":
    raise ValueError(
        "growth operates on interpolated (NumPy) values; call .interp() "
        "first -- fitting raw DG coefficients would mix basis functions.")
  # end
  time = data.grid
  values = data.values
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

  kwargs = {"min_N": minn}
  if p0 is not None:
    kwargs["p0"] = p0
  # end
  best_params, _r2, _n = numerics.fit_growth(x, y, **kwargs)
  t = 0.5 * (x[:-1] + x[1:])
  out_val = numerics.exp2(t, *best_params)
  return data._result([x], out_val[..., np.newaxis], inplace=inplace, tag=tag,
      label=label, growth_rate=best_params[1])
