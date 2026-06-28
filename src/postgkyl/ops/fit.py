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
from postgkyl.output.nodal_to_cell_centered_grid import nodal_to_cell_centered_grid

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def fit(data: "GData", fit_type: str, *, guess=None, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Fit ``fit_type`` to ``data`` and return the fitted curve as a ``GData``."""
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
