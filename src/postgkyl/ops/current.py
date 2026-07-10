"""The ``current`` verb — accumulate current from species moments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import models

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def current(data: "GDataState", *, qbym: bool = False,
    charge: float | None = None, mass: float | None = None,
    inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Accumulate current from species moments.

  Scales the species' momentum/flow moments by a per-species factor to
  form its contribution to the current. By default the factor is ``-1.0``;
  with ``qbym=True`` (and ``charge``/``mass`` given) the charge/mass ratio
  is used instead. Should be used with ``qbym=True`` for fluid data.

  Args:
    data: A species dataset carrying the flow/momentum moments to scale;
      must be NumPy-backed.
    qbym: When True, scale by the charge-to-mass ratio (q/m); otherwise
      scale by ``-1.0``. Set True for fluid data.
    charge: Particle charge, required when ``qbym`` is True.
    mass: Particle mass, required (and must be nonzero) when ``qbym`` is
      True.
    inplace: mutate and return ``data`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset of the scaled current contribution.

  Raises:
    ValueError: if ``data`` is native modal (gkyl-backed); if ``qbym`` is
      True and ``charge``/``mass`` are not both given (a nonzero ``mass``).
  """
  if data.backend == "gkyl":
    raise ValueError(
        "current operates on interpolated (NumPy) values; call .interp() "
        "first -- scaling raw DG coefficients by a per-species factor is "
        "still valid numerically, but this verb is field-domain only.")
  # end
  if qbym and (charge is None or not mass):
    raise ValueError(
        "current: qbym=True requires both 'charge' and a nonzero 'mass' "
        f"-- got charge={charge!r}, mass={mass!r}.")
  # end
  grid, values = models.accumulate_current(data.grid, data.values,
      qbym=qbym, charge=charge, mass=mass)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
