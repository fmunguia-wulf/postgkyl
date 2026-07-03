"""File I/O — bytes <-> dataset arrays.

A leaf layer: one reader per format, dispatched by ``read()``; ``write()`` for
output. Nothing here imports ``core``/``ops``; the readers fill a plain ``ctx``
dict and return ``(grid, values)`` so the container can construct itself on top.
"""

from __future__ import annotations

from . import mapping
from .gkyl_c_reader import GkylCReader
from .gkyl_reader import GkylReader
from .writer import write

# Reader registry — tried in order; extend by adding (name, reader) entries.
# The Gkeyll-native reader goes first: it returns modal data as a native
# GkylArray. The pure-Python reader is the no-libg0core fallback and the
# handler for partial loads and dynvector files.
_READERS = {
    "gkyl_c": GkylCReader,
    "gkyl": GkylReader,
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


__all__ = ["read", "write", "mapping", "GkylCReader", "GkylReader"]
