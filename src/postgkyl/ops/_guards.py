"""The shared field-domain guard used by field-only verbs.

Centralizes the check-and-raise boilerplate that was independently
retyped in ``moments.py``, ``agyro.py``, ``energetics.py``, ``rotate.py``,
``transform_frame.py``, and ``laguerre.py``: each verb keeps its own
``reason`` clause (why *this* verb's math has no meaning on raw modal
coefficients), but the check itself -- ``backend == "gkyl"`` -> raise with
the standard ".interp() first" message shape -- has one home.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def require_field_domain(data: "GDataState", who: str, reason: str) -> None:
  """Raise if ``data`` is native modal (gkyl-backed) DG coefficients.

  Args:
    data: The dataset to check.
    who: The verb (or argument) name to name in the error message.
    reason: The clause explaining why raw coefficients are unusable here,
      e.g. ``"rotating raw DG coefficients would mix basis functions"``.

  Raises:
    ValueError: if ``data.backend == "gkyl"``.
  """
  if data.backend == "gkyl":
    raise ValueError(
        f"{who} operates on interpolated (NumPy) values; call .interp() "
        f"first -- {reason}.")
  # end
