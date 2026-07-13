"""File I/O — bytes <-> dataset arrays.

A leaf layer: one reader per format, dispatched by ``read()``; ``write()`` for
output. Nothing here imports ``core``/``ops``; the readers fill a plain ``ctx``
dict and return ``(grid, values)`` so the container can construct itself on top.
"""

from __future__ import annotations

from . import mapping
from .gkyl_c_reader import GkylCReader
from .gkyl_reader import GkylReader
from .gkyl_adios_reader import GkylAdiosReader
from .gkyl_h5_reader import GkylH5Reader
from .flash_h5_reader import FlashH5Reader
from .writer import save

# Reader registry — tried in order; extend by adding (name, reader) entries.
# Order is by *specificity* of ``is_compatible()``, most specific / cheapest
# first, so a file never falls into the wrong reader:
#   1. "gkyl_c"  — native .gkyl via libg0core; the magic-byte + file-type
#                  check is exact and returns modal data as a GkylArray.
#   2. "gkyl"    — pure-Python .gkyl fallback (no libg0core, partial loads,
#                  dynvectors); same exact magic-byte check as gkyl_c.
#   3. "adios"   — legacy ADIOS2 .bp output; is_compatible() actually opens
#                  the file with adios2, so a non-.bp file (including a
#                  .gkyl/.h5 file) reliably fails to parse and returns False.
#   4. "h5"      — legacy pre-ADIOS Gkeyll HDF5 output; is_compatible()
#                  requires the Gkeyll-specific "/StructGridField" or
#                  "/DataStruct/data" node, so a FLASH .h5 file (no such
#                  nodes) is correctly declined and falls through to "flash".
#   5. "flash"   — FLASH code HDF5 output; is_compatible() requires a
#                  "coordinates" node, disjoint from the Gkeyll h5 layout.
# Because 1-2 are checked with the same fast magic-byte test before 3-5 ever
# touch the (slower) adios2/tables importers, a .gkyl file never reaches an
# h5/adios reader, and vice versa.
_READERS = {
    "gkyl_c": GkylCReader,
    "gkyl": GkylReader,
    "adios": GkylAdiosReader,
    "h5": GkylH5Reader,
    "flash": FlashH5Reader,
}


def read(file_name: str, ctx: dict | None = None, **kwargs):
  """Read ``file_name`` into ``(grid, values)``, populating ``ctx`` in place.

  The reader is chosen by trying each registered reader's ``is_compatible``
  check. ``ctx`` (a plain dict) is filled with metadata — ``poly_order``,
  ``basis_type``, ``cells``, ``lower``/``upper``, ``time``/``frame``, ... —
  exactly as the legacy reader did.
  """
  if ctx is None:
    ctx = {}
  # end
  for reader_cls in _READERS.values():
    reader = reader_cls(file_name=file_name, ctx=ctx, **kwargs)
    if reader.is_compatible():
      reader.preload()
      return reader.load()
    # end
  # end
  raise NameError(
      f"'{file_name}' cannot be read with any known reader: {list(_READERS)}")
# end


__all__ = ["read", "save", "mapping", "GkylCReader", "GkylReader",
    "GkylAdiosReader", "GkylH5Reader", "FlashH5Reader"]
