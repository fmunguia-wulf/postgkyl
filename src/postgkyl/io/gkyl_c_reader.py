"""``.gkyl`` reading through Gkeyll itself (the primary read path).

``GkylCReader`` delegates the whole read — header, grid, allocation, payload,
multi-range stitching — to ``libg0core.so`` via :mod:`postgkyl.gpython.rio` and
returns the data as a **native** :class:`~postgkyl.gpython.array.GkylArray`, so
modal datasets start life in the modal domain. Python's only jobs are decoding
the msgpack metadata blob into ``ctx`` (same key policy as the pure-Python
reader) and building the NumPy edge grid.

It declines (``is_compatible() -> False``) when the FFI is unavailable, the
file is not a field file (types 1/3), or a partial load (``axes=``/``comp=``)
was requested — those fall through to the pure-Python :class:`GkylReader`.
"""

from __future__ import annotations

import numpy as np
import msgpack

from postgkyl import gpython
from . import mapping


class GkylCReader:
  """Reader protocol implementation backed by ``gkyl_array_rio``."""

  def __init__(self, file_name: str, ctx: dict | None = None,
      representation: str | None = None, **kwargs):
    self.file_name = str(file_name)
    self.ctx = ctx if ctx is not None else {}
    self._representation_override = representation
    # Any partial-load request (axes=, comp=, ...) -> defer to the Python reader.
    self._partial = any(v is not None for v in kwargs.get("axes") or ()) or \
        kwargs.get("comp") is not None or \
        bool({k for k in kwargs if k not in ("axes", "comp")})
  # end

  def is_compatible(self) -> bool:
    if self._partial or not gpython.available():
      return False
    # end
    try:
      return gpython.rio.file_type(self.file_name) in gpython.rio.FIELD_FILE_TYPES
    # end
    except (OSError, RuntimeError):
      return False
    # end
  # end

  def preload(self) -> None:
    grid, _, meta, esznc, _ = gpython.rio.read_header(self.file_name)
    has_basis = False
    if meta:
      for key, val in msgpack.unpackb(meta).items():
        if key in ("polyOrder", "poly_order"):
          self.ctx["poly_order"] = val
        # end
        elif key in ("basisType", "basis_type"):
          self.ctx["basis_type"] = val
          self.ctx["is_modal"] = True
          has_basis = True
        # end
        else:
          # Covers "representation" too, if the writer stamped one directly:
          # a file's own metadata is the next-best source of truth once no
          # explicit override was given.
          self.ctx[key] = val
        # end
      # end
    # end
    if has_basis and "representation" not in self.ctx:
      self.ctx["representation"] = "modal"
    # end
    if self._representation_override is not None:
      # The writer stamps every field with basis/order metadata, even
      # non-DG diagnostic outputs (e.g. a per-cell CFL rate); this lets a
      # caller correct a mistagged file to what its values actually are.
      # Wins over both the file's own metadata and the "modal" default.
      self.ctx["representation"] = self._representation_override
    # end
    self.ctx["cells"] = grid["cells"]
    self.ctx["lower"] = grid["lower"]
    self.ctx["upper"] = grid["upper"]
    self.ctx["num_comps"] = esznc // 8  # payload is float64
  # end

  def load(self):
    grid, arr = gpython.rio.read_field(self.file_name)
    cells = grid["cells"]
    if arr.size != int(np.prod(cells)):
      raise IOError(
          f"'{self.file_name}': stored cells {arr.size} do not match the "
          f"domain {tuple(cells)} (ghost-cell layout?) — not supported by "
          "the Gkeyll read path yet")
    # end
    edges = mapping.uniform_grid(grid["lower"], grid["upper"], cells)
    self.ctx["grid_type"] = "uniform"
    return edges, arr
  # end
# end
