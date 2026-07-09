"""Distribution-function reconstruction from Laguerre moments (PKPM).

Composes the full distribution function ``f(x, v_par, v_perp)`` out of the
Laguerre expansion coefficients ``F0(x, v_par)``, ``F1(x, v_par)`` (hardcoded
for ``l=0``, ``n=0,1``) and the PKPM ``T/m`` moment. See Jimmy Juno's slides:
https://drive.google.com/file/d/1548tLF9o7vyW3bkrsq6FvAMV-8XJvKtY/view
"""

from __future__ import annotations

import numpy as np


def laguerre_compose(f_grid: list[np.ndarray], f_values: np.ndarray,
    t_over_m_values: np.ndarray,
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Compose PKPM expansion coefficients into a single distribution function.

  Args:
    f_grid: ``[x, v_par]`` nodal coordinate arrays.
    f_values: 2-component Laguerre expansion coefficients ``(F0, G)``.
    t_over_m_values: PKPM ``T / m`` moment, single component.

  Returns:
    ``([x, v_par, v_perp], values)``: the extended grid (``v_perp`` a copy
    of the ``v_par`` axis) and the composed distribution function, with a
    trailing singleton component axis.
  """
  x, vpar = f_grid[0], f_grid[1]
  vperp = np.copy(vpar)

  x_cc = (x[:-1] + x[1:]) / 2
  vpar_cc = (vpar[:-1] + vpar[1:]) / 2
  vperp_cc = (vpar[:-1] + vpar[1:]) / 2

  _, _, vperp_3D = np.meshgrid(x_cc, vpar_cc, vperp_cc, indexing="ij")

  F0 = f_values[..., 0]
  G = f_values[..., 1]
  T_m = t_over_m_values[..., 0]

  F1 = F0 - (G.transpose() / T_m).transpose()

  # Adding the np.newaxis allows the subsequent np.multiply (called when
  # doing * on numpy arrays) to work. The arrays need to have the same
  # number of axes, e.g. one cannot multiply (3, 3) and (3,) arrays but can
  # multiply (3, 3) with (3, 1) or (1, 3).
  F0, F1 = F0[..., np.newaxis], F1[..., np.newaxis]
  # T_m gains two new axes here (F0/F1 gain only one above), one deeper than
  # needed to broadcast against vperp_3D — an extra, constant-along-itself
  # trailing axis leaks into the returned array's shape. Preserved verbatim
  # from src_bak/postgkyl/tools/laguerre_compose.py; pinned by
  # tests/test_models_laguerre.py.
  T_m = T_m[..., np.newaxis, np.newaxis]

  # Hardcoded for l=0, n=0,1 in
  # https://drive.google.com/file/d/1548tLF9o7vyW3bkrsq6FvAMV-8XJvKtY/view
  f = (F0 + F1 * (1 - vperp_3D**2 / 2 / T_m)) / (2 * np.pi * T_m) * np.exp(
      -(vperp_3D**2) / 2 / T_m)

  f = f[..., np.newaxis]  # Adding the component index

  return [x, vpar, vperp], f
