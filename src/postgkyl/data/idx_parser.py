import numpy as np

def _find_nearest_index(array, value):
  if array is None:
    raise TypeError("The index value is float but the 'array' from which to select the neares value is not specified.")
  # end
  idx = np.searchsorted(array, value)
  if idx == len(array):
    return int(idx - 2)
  elif idx > 0:
    return int(idx - 1)
  else:
    return int(idx)
  # end


def _find_cell_index(array, value):
  if array is None:
    raise TypeError("The index value is float but the 'array' from which to select the neares value is not specified.")
  # end
  idx = np.searchsorted(array, value)
  return int(idx)


def _is_int_str(value: str) -> bool:
  """Whether the string represents an integer (e.g. '2' or '-1'), not a float."""
  try:
    int(value)
    return True
  except ValueError:
    return False
  # end


def _resolve_negative_index(idx: int, array: np.ndarray | None, nodal: bool) -> int:
  """Translate a Python-style negative index into a positive one.

  '-1' refers to the last cell, '-2' to the one before, etc. The number
  of cells is the length of the grid array for nodal data and one less
  for cell-centered data (where the grid stores cell edges).
  """
  if idx < 0 and array is not None:
    num_cells = len(array) if nodal else len(array) - 1
    idx += num_cells
  # end
  return idx


def _string_to_index(value: str, array: np.ndarray, nodal: bool = False) -> int:
  if isinstance(value, str):
    if _is_int_str(value):
      return _resolve_negative_index(int(value), array, nodal)
    else:
      if nodal:
        return _find_cell_index(array, float(value))
      else:
        return _find_nearest_index(array, float(value))
      # end
    # end
  else:
    raise TypeError("Value is not string")
  # end


def idx_parser(value: int | float | str, array: np.ndarray | None = None,
    nodal: bool = False) -> int | slice:
  idx = None
  if isinstance(value, int):
    idx = _resolve_negative_index(value, array, nodal)
  elif isinstance(value, float):
    if nodal:
      idx = _find_cell_index(array, value)
    else:
      idx = _find_nearest_index(array, value)
    # end
  else:
    if isinstance(value, str):
      if len(value.split(",")) > 1:
        idxs = value.split(",")
        idx = tuple([_string_to_index(i, array, nodal) for i in idxs])
      elif len(value.split(":")) == 2:
        idxs = value.split(":")
        if idxs[0] == "":
          idxs[0] = str(0)
        # end
        if idxs[1] == "":
          idxs[1] = str(len(array))
        # end
        try:
          if int(idxs[1]) < 0:
            idxs[1] = str(len(array) + int(idxs[1]) + 1)
          # end
        except ValueError:
          pass
        idx = slice(_string_to_index(idxs[0], array, nodal), _string_to_index(idxs[1], array, nodal))
      else:
        idx = _string_to_index(value, array, nodal)
      # end
    # end
  # end

  return idx
