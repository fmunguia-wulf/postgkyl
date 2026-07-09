"""Vector rotation parallel/perpendicular to a reference (e.g. the magnetic
field).

For a field ``u`` and a rotator ``v`` (assumed three-component, last axis),
``parrotate`` computes the projection of ``u`` onto ``v``'s direction,
``(u . v_hat) v_hat``; ``perprotate`` is the remainder, ``u - (u . v_hat)
v_hat``.

Note: :mod:`postgkyl.numerics.rotation_matrix` builds a matrix whose first
row is the *elementwise sign* of its input, not a true unit vector (see its
own tests) — using it here would change the projection's numerical result,
so this module keeps the original dot-product formula instead (Doctrine:
copy numerics verbatim).
"""

from __future__ import annotations

import numpy as np


def parrotate(grid: list[np.ndarray], values: np.ndarray,
    rotator_values: np.ndarray, *, rotate_coords: str = "0:3",
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Rotate a three-component field into the direction of a rotator field.

  Args:
    grid: Nodal coordinate arrays, one per spatial dimension.
    values: Three-component field to rotate (last axis is components).
    rotator_values: Field providing the rotation direction, on the same
      grid as ``values``.
    rotate_coords: ``"start:end"`` slice of ``rotator_values``'s component
      axis to use as the rotation direction (e.g. ``"3:6"`` to rotate into
      a magnetic field stored after three electric-field components).

  Returns:
    ``(grid, values)`` holding the parallel component
    ``(u . v_hat) v_hat``.

  Raises:
    ValueError: If ``values`` or the sliced ``rotator_values`` do not have
      exactly three components.
  """
  lo, hi = rotate_coords.split(":")
  valuesrot = rotator_values[..., slice(int(lo), int(hi))]

  if values.shape[-1] != 3 or valuesrot.shape[-1] != 3:
    raise ValueError(
        "parrotate requires three-component vector fields; data has "
        f"{values.shape[-1]:d} components, rotator (after 'rotate_coords' "
        f"slicing) has {valuesrot.shape[-1]:d}")

  scale = np.sum(values * valuesrot, axis=-1) / np.sum(
      valuesrot * valuesrot, axis=-1)
  outrot = scale[..., np.newaxis] * valuesrot

  return list(grid), outrot


def perprotate(grid: list[np.ndarray], values: np.ndarray,
    rotator_values: np.ndarray, *, rotate_coords: str = "0:3",
    ) -> tuple[list[np.ndarray], np.ndarray]:
  """Rotate a three-component field perpendicular to a rotator field.

  Computed as the remainder after :func:`parrotate`:
  ``u - (u . v_hat) v_hat``.
  """
  grid, par = parrotate(grid, values, rotator_values,
      rotate_coords=rotate_coords)
  return grid, values - par
