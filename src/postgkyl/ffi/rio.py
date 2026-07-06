"""File loading through Gkeyll's ``gkyl_array_rio`` — the C read path.

``read_field`` performs the whole read (grid + allocate + fill, including
multi-range stitching for file_type 3) inside Gkeyll; ``read_header`` returns
the grid and the raw msgpack metadata blob without touching the payload.
Decoding the msgpack bytes is left to the caller (``io/``) — metadata policy
is an io concern, bytes are a floor concern.
"""

from __future__ import annotations

import numpy as np

from . import _lib
from .array import GkylArray

# enum gkyl_file_type ordinals used by gkyl_get_gkyl_file_type
FIELD_FILE_TYPES = (1, 3)  # single-range and multi-range field data


def file_type(file_name: str) -> int:
  """The gkyl file type (1..5), or -1 if not a gkyl file."""
  return int(_lib.require().file_type(file_name))


def read_header(file_name: str):
  """Header-only read: ``(grid_dict, file_type, meta_bytes, esznc, tot_cells)``.

  ``grid_dict`` has ``ndim``/``lower``/``upper``/``cells`` as NumPy values;
  ``meta_bytes`` is the raw msgpack blob (b"" when the file has none).
  """
  grid, ftype, meta, esznc, tot_cells = _lib.require().read_header(file_name)
  return _grid_dict(grid), ftype, meta, esznc, tot_cells


def read_field(file_name: str):
  """Full field read inside Gkeyll: ``(grid_dict, GkylArray)``."""
  grid, cap = _lib.require().read_field(file_name)
  return _grid_dict(grid), GkylArray(cap)


def _grid_dict(grid: tuple) -> dict:
  ndim, lower, upper, cells = grid
  return {
      "ndim": int(ndim),
      "lower": np.asarray(lower),
      "upper": np.asarray(upper),
      "cells": np.asarray(cells, dtype=np.int64),
  }
