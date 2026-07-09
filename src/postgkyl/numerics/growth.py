"""Fitting exponential growth rates from a time series."""

from __future__ import annotations

from typing import Callable

import numpy as np
import scipy.optimize as opt


def exp2(x: float, a: float, b: float) -> float:
  """Custom exponential ``a * exp(2*b*x)``.

  Energy (a squared quantity) is often used for growth-rate studies, hence
  the factor of 2 in the exponent.
  """
  return a*np.exp(2*b*x)


def fit_growth(x: np.ndarray, y: np.ndarray, function: Callable = exp2,
    min_N: int | None = None, p0: tuple = (1, 1)) -> tuple[tuple, float, int]:
  """Fit ``function`` to the continuously-increasing region of ``x``/``y``.

  Scans fitting windows ``x[0:n]`` for ``n`` from ``min_N`` up to
  ``len(x)``, keeping the window with the best coefficient of
  determination (R^2, https://en.wikipedia.org/wiki/Coefficient_of_determination).

  Args:
    x: Independent variable.
    y: Dependent variable.
    function: Model to fit; defaults to :func:`exp2`.
    min_N: Minimum number of points in the fitted window. Defaults to
      ``len(x) // 10``.
    p0: Initial guess for the fit parameters.

  Returns:
    ``(best_params, best_R2, best_N)`` where ``best_params[1]`` (the
    growth rate) has been rescaled back to the original ``x`` units.

  Raises:
    RuntimeError: If ``curve_fit`` fails to converge for every window in
      the scan range.
  """
  best_R2 = 0.0
  if min_N is None:
    min_N = int(len(x)/10)
  # end
  max_N = len(x)
  best_N = min_N
  best_params = np.asarray(p0, dtype=float)

  max_x = x[-1]

  for n in np.linspace(min_N, max_N - 1, max_N - min_N):
    n = int(n)
    xn = x[0:n]/max_x  # continuously increasing fitting region
    yn = y[0:n]
    try:
      params, _ = opt.curve_fit(function, xn, yn, best_params)
      residual = yn - function(xn, *params)
      ss_res = np.sum(residual**2)
      ss_tot = np.sum((yn - np.mean(yn))**2)
      R2 = 1 - ss_res/ss_tot
      if R2 > best_R2:
        best_R2 = R2
        best_params = params
        best_N = n
      # end
    except RuntimeError:
      continue
    # end
  # end
  if best_R2 == 0.0:
    raise RuntimeError(
        "fit_growth: curve_fit failed to converge for every window in "
        f"[{min_N:d}, {max_N:d})")
  # end
  best_params[1] = best_params[1]/max_x
  return best_params, best_R2, best_N
