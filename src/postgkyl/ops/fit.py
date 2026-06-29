"""The ``fit`` verb — fit a model to data and return the fitted curve.

The result is a new ``GData`` holding the fitted values on the data's grid;
the per-component fit parameters and R^2 are stored in ``ctx['fit_params']``
and ``ctx['fit_R2']``. ``fit_type`` is a model name (e.g. 'linear',
'gaussian') or an RPN expression — see :mod:`postgkyl.tools.fit`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from postgkyl.tools.fit import fit as _fit, fit_evaluate as _fit_evaluate
from postgkyl.utils.nodal_to_cell_centered_grid import nodal_to_cell_centered_grid

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def fit(data: "GData", fit_type: str, *, guess=None, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Fit a model to data and return the fitted curve.

  Fits the model named (or expressed) by ``fit_type`` to each component of
  ``data`` independently and returns the fitted values evaluated on the data's
  grid. Axes that have been collapsed to a single cell (e.g. after integrate or
  select) are dropped, so 1D and 2D fits are supported. The per-component fit
  parameters and coefficients of determination are stored in the result's
  ``ctx['fit_params']`` and ``ctx['fit_R2']``.

  Args:
    data: GData
      The dataset to fit. Its grid provides the independent variable(s) and
      each component is fit separately.
    fit_type: str
      The model to fit. Either a built-in model name -- 'linear', 'quadratic',
      'plane' (2D), 'quadratic2d' (2D), 'exp_plateau', 'gaussian', 'power',
      'sinusoid', or 'tanh_transition' -- or a custom RPN expression string
      (e.g. 'x a * b +') whose free tokens (not the spatial variables 'x'/'y',
      operators, or numbers) become fit parameters.
    guess: str | Sequence[float] | None
      Initial guess for the fit parameters. A comma-separated string (e.g.
      '1,0,2') or a sequence of floats. None lets the fitter pick defaults
      (ones).
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData holding the fitted curve on the (active) grid, with
    ``ctx['fit_params']`` and ``ctx['fit_R2']`` set (or the mutated input when
    inplace=True).

  Raises:
    ValueError: If ``fit_type`` is neither a recognized model name nor a valid
      RPN expression.
  """
  grid = data.get_grid()
  values = data.get_values()
  spatial_shape = values.shape[:-1]

  if any(grid[d].shape[0] == spatial_shape[d] + 1 for d in range(len(grid))):
    cc_grid = nodal_to_cell_centered_grid(grid, spatial_shape)
  else:
    cc_grid = list(grid)
  # end

  # Drop dimensions collapsed to a single cell (e.g. after integrate/select).
  active = [d for d in range(len(cc_grid)) if cc_grid[d].shape[0] > 1]
  if len(active) < len(cc_grid):
    idx = tuple(slice(None) if d in active else 0
        for d in range(len(spatial_shape))) + (slice(None),)
    cc_grid = [cc_grid[d] for d in active]
    values = values[idx]
  # end

  if len(cc_grid) == 1:
    xdata = cc_grid[0]
  else:
    mesh = np.meshgrid(cc_grid[0], cc_grid[1], indexing="ij")
    xdata = np.array([mesh[0].flatten(), mesh[1].flatten()])
  # end

  guess_list = None
  if guess is not None:
    guess_list = [float(v) for v in guess.split(",")] if isinstance(guess, str) else list(guess)
  # end

  active_shape = tuple(cg.shape[0] for cg in cc_grid)
  fit_values_list, all_params, all_r2 = [], [], []
  for comp in range(values.shape[-1]):
    ydata = values[..., comp].flatten()
    params, _cov, r2 = _fit(xdata, ydata, fit_type, p0=guess_list)
    y_fit = _fit_evaluate(xdata, fit_type, params)
    fit_values_list.append(y_fit.reshape(active_shape + (1,)))
    all_params.append(params)
    all_r2.append(r2)
  # end

  fit_values = np.concatenate(fit_values_list, axis=-1)
  fit_grid = [grid[d] for d in active]
  return data._result(fit_grid, fit_values, inplace=inplace, tag=tag, label=label,
      fit_params=all_params, fit_R2=all_r2)
