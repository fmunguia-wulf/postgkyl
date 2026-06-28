"""The ``pg.load`` callable + namespace.

``load`` is a small singleton so that the common case is a plain call while
related loaders hang off the same name::

    pg.load('elc_M0_0.gkyl')                 # -> GData
    pg.load.many('elc_M0_*.gkyl')            # -> DatasetGroup (sorted)
"""

from __future__ import annotations

import re
from glob import glob

from postgkyl.data.gdata import GData
from postgkyl.group import DatasetGroup


def find_output_stems(extensions: str = "bp,gkyl") -> dict:
  """Map each extension to the sorted unique Gkeyll filename stems in the CWD.

  Frame indices and a trailing ``_restart`` are stripped from each stem.
  """
  result = {}
  for ext in extensions.split(","):
    unique = []
    for fn in glob(f"*.{ext:s}"):
      stem = fn[: -(len(ext) + 1)]
      if stem.endswith("_restart"):
        stem = stem[:-8]
      # end
      stem = re.sub(r"_\d+$", "", stem)
      if stem not in unique:
        unique.append(stem)
      # end
    # end
    result[ext] = sorted(unique)
  # end
  return result


class _Loader:
  """Callable loader exposing ``__call__``, ``.many``, and ``.outputs``."""

  def __call__(self, file_name: str = "", **kwargs) -> GData:
    """Load a single file into a ``GData`` (see :class:`postgkyl.GData`)."""
    return GData(file_name, **kwargs)

  def many(self, pattern: str, **kwargs) -> DatasetGroup:
    """Load every file matching a glob ``pattern`` into a ``DatasetGroup``.

    Files are loaded in sorted order so frame sweeps stay in sequence.
    """
    files = sorted(glob(pattern))
    if not files:
      raise FileNotFoundError(f"No files match pattern: {pattern!r}")
    # end
    return DatasetGroup([GData(f, **kwargs) for f in files])

  def outputs(self, extensions: str = "bp,gkyl") -> dict:
    """Discover Gkeyll output filename stems in the current directory."""
    return find_output_stems(extensions)


load = _Loader()
