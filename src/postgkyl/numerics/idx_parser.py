"""Parse index / value / slice selectors into NumPy indices (pure)."""

from __future__ import annotations

import numpy as np


def _find_nearest_index(array, value):
  if array is None:
    raise TypeError("Float selector given but no coordinate array to match against.")
  # end
  idx = np.searchsorted(array, value)
  if idx == len(array):
    return int(idx - 2)
  # end
  elif idx > 0:
    return int(idx - 1)
  # end
  else:
    return int(idx)
# end
  # end


def _find_cell_index(array, value):
  if array is None:
    raise TypeError("Float selector given but no coordinate array to match against.")
  # end
  return int(np.searchsorted(array, value))
# end


def _string_to_index(value: str, array: np.ndarray, nodal: bool = False) -> int:
  if not isinstance(value, str):
    raise TypeError("Value is not a string")
  # end
  if value.lstrip("-").isdigit():
    return int(value)
  # end
  return _find_cell_index(array, float(value)) if nodal else _find_nearest_index(array, float(value))
# end


def idx_parser(value: int | float | str, array: np.ndarray | None = None,
    nodal: bool = False) -> int | slice | tuple:
  """Turn an int/float/str selector into an int index, ``slice``, or tuple.

  - int -> used as-is
  - float -> nearest (or containing, if ``nodal``) cell index
  - ``"a,b,c"`` -> tuple of indices
  - ``"a:b"`` -> ``slice``
  - ``"a"`` -> single index
  """
  if isinstance(value, int):
    return value
  # end
  if isinstance(value, float):
    return _find_cell_index(array, value) if nodal else _find_nearest_index(array, value)
  # end
  if isinstance(value, str):
    if len(value.split(",")) > 1:
      return tuple(_string_to_index(i, array, nodal) for i in value.split(","))
    # end
    if len(value.split(":")) == 2:
      lo, hi = value.split(":")
      if lo == "":
        lo = "0"
      # end
      if hi == "":
        hi = str(len(array))
      # end
      try:
        if int(hi) < 0:
          hi = str(len(array) + int(hi) + 1)
        # end
      # end
      except ValueError:
        pass
      # end
      return slice(_string_to_index(lo, array, nodal), _string_to_index(hi, array, nodal))
    # end
    return _string_to_index(value, array, nodal)
  # end
  raise TypeError(f"Unsupported selector type: {type(value)!r}")
# end
