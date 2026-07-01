"""The ``relchange`` verb — relative change between two datasets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.rel_change import rel_change as _rel_change

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def relchange(data: "GData", reference: "GData", *, comp=None,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Relative change of ``data`` with respect to ``reference``.

  Computes ``(data - reference) / reference`` component-wise. Both datasets are
  assumed to share the same grid and component layout. When ``comp`` is given,
  every numerator component is divided by that single reference component
  instead of the matching one (useful, e.g., to normalize by a total).

  Args:
    data: GData
      The dataset whose relative change is computed.
    reference: GData
      The baseline dataset to compare against (the denominator).
    comp: int | str | None
      Optional reference component index. When given, every component is
      divided by ``reference`` component ``comp``; otherwise each component is
      divided by the matching reference component. None for component-wise.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData of the relative change (or the mutated input when
    inplace=True).
  """
  grid, values = _rel_change(reference, data, comp)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
