"""The ``interpolate`` verb — interpolate DG data onto a uniform mesh."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.ops._dg import make_interpolator

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def interpolate(data: "GData", *, basis: str | None = None, p: int | None = None,
    interp: int | None = None, read: bool | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Interpolate DG (modal or nodal) data onto a uniform mesh.

  ``basis`` is the short DG basis code (``ms``, ``ns``, ``mo``, ``mt``,
  ``gkhyb``, ``pkpmhyb``); ``p`` is the polynomial order; ``interp`` overrides
  the number of interpolation points. When omitted, the basis/order stored in
  ``data.ctx`` are used. The result is flagged ``interpolated=True`` so it
  becomes safe for element-wise numeric operations.
  """
  dg = make_interpolator(data, basis=basis, p=p, interp=interp, read=read)
  num_comps = int(data.get_num_comps() / dg.num_nodes)
  grid, values = dg.interpolate(tuple(range(num_comps)))
  return data._result(grid, values, inplace=inplace, tag=tag, label=label,
      interpolated=True)
