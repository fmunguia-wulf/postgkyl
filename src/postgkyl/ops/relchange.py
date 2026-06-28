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

  Computes ``(data - reference) / reference`` component-wise. When ``comp`` is
  given, every component is divided by that single reference component.
  """
  grid, values = _rel_change(reference, data, comp)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
