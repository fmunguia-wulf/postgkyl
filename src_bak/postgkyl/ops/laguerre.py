"""The ``laguerre_compose`` verb — compose PKPM Laguerre coefficients."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.laguerre_compose import laguerre_compose as _laguerre_compose

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def laguerre_compose(distribution: "GData", variables, *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Compose PKPM Laguerre coefficients into a full distribution function.

  Reconstructs the full distribution function ``f(x, v_par, v_perp)`` from the
  PKPM Laguerre expansion coefficients ``F0`` and ``F1`` (stored as the two
  components of ``distribution``) together with the PKPM temperature-over-mass
  field carried in ``variables``.

  Args:
    distribution: GData
      The two-component PKPM Laguerre expansion coefficients ``F0(x, v_par)``
      and ``F1(x, v_par)``.
    variables: GData
      The PKPM variables dataset providing T/m(x) (used as the first
      component).
    inplace: bool
      When True, mutate and return ``distribution``; otherwise return a new
      GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData holding the composed ``f(x, v_par, v_perp)`` (or the mutated
    ``distribution`` when inplace=True).
  """
  grid, values = _laguerre_compose(distribution, variables)
  return distribution._result(grid, values, inplace=inplace, tag=tag, label=label)
