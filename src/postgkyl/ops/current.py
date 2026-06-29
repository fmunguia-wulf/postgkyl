"""The ``current`` verb — accumulate current from species moments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.accumulate_current import accumulate_current as _accumulate_current

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def current(data: "GData", *, qbym: bool = False, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Accumulate current from species moments.

  Scales the species' momentum/flow moments by a per-species factor to form
  its contribution to the current. By default the factor is ``-1.0``; with
  ``qbym=True`` (and the species' mass and charge available in ``data``) the
  charge/mass ratio is used instead. Should be used with ``qbym=True`` for
  fluid data.

  Args:
    data: GData
      A species dataset carrying charge/mass metadata and the flow/momentum
      moments to scale.
    qbym: bool
      When True, scale by the charge-to-mass ratio (q/m); otherwise scale by
      ``-1.0``. Set True for fluid data.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the scaled current contribution (or the mutated input when
    inplace=True).
  """
  grid, values = _accumulate_current(data, qbym)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
