"""The ``laguerre_compose`` verb — compose PKPM Laguerre coefficients."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.laguerre_compose import laguerre_compose as _laguerre_compose

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def laguerre_compose(distribution: "GData", variables, *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Compose PKPM Laguerre coefficients of ``distribution`` with ``variables``
  (the PKPM vars dataset) into a full ``f(x, v_par, v_perp)``."""
  grid, values = _laguerre_compose(distribution, variables)
  return distribution._result(grid, values, inplace=inplace, tag=tag, label=label)
