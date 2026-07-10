"""The ``laguerre_compose`` verb — compose PKPM Laguerre coefficients."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import models
from ._guards import require_field_domain as _require_field_domain

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

_REASON = "composing raw DG coefficients would mix basis functions"


def laguerre_compose(distribution: "GDataState", variables: "GDataState", *,
    inplace: bool = False, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Compose PKPM Laguerre coefficients into a full distribution function.

  Reconstructs the full distribution function ``f(x, v_par, v_perp)`` from
  the PKPM Laguerre expansion coefficients ``F0`` and ``G`` (stored as the
  two components of ``distribution``) together with the PKPM
  temperature-over-mass field carried in ``variables``.

  Args:
    distribution: The two-component PKPM Laguerre expansion coefficients
      ``F0(x, v_par)`` and ``G(x, v_par)``; must be NumPy-backed.
    variables: The PKPM variables dataset providing T/m(x) (used as the
      first component); must be NumPy-backed.
    inplace: mutate and return ``distribution`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset holding the composed ``f(x, v_par, v_perp)``.

  Raises:
    ValueError: if either input is native modal (gkyl-backed).
  """
  _require_field_domain(distribution, "laguerre_compose", _REASON)
  _require_field_domain(variables, "laguerre_compose", _REASON)
  grid, values = models.laguerre_compose(distribution.grid,
      distribution.values, variables.values)
  return distribution._result(grid, values, inplace=inplace, tag=tag,
      label=label)
