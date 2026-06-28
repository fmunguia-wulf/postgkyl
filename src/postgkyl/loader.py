"""The ``pg.load`` callable + namespace.

``load`` is a small singleton so that the common case is a plain call while
related loaders hang off the same name::

    pg.load('elc_M0_0.gkyl')                 # -> GData
    pg.load.many('elc_M0_*.gkyl')            # -> DatasetGroup (sorted)

The loader methods mirror the full :class:`postgkyl.GData` constructor
signature explicitly (rather than forwarding ``**kwargs``) so that editors and
language servers such as Pylance surface the individual arguments and their
documentation on autocomplete.
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

  def __call__(self, file_name: str = "",
      comp: int | str | None = None,
      z0: int | str | None = None, z1: int | str | None = None,
      z2: int | str | None = None, z3: int | str | None = None,
      z4: int | str | None = None, z5: int | str | None = None,
      var_name: str = "CartGridField",
      tag: str = "default", label: str = "",
      ctx: dict | None = None,
      comp_grid: bool = False, mapc2p_name: str = "", mapc2p_vel_name: str = "",
      reader_name: str = "", load: bool = True, click_mode: bool = False) -> GData:
    """Load a single file into a :class:`postgkyl.GData`.

    Args:
      file_name: str
        The name of Gkeyll output file. Currently supported are 'h5',
        ADIOS 'bp', and binary 'gkyl' files. Can be ommited for empty
        class.
      comp: int or 'int:int'
        Load only the specified component index or a slice of
        idices. Supported only for the ADIOS 'bp' files.
      z0 - z5: int or 'int:int'
        Load only the specified  index or a slice of
        idices in a direction. Supported only for the ADIOS 'bp' files.
      var_name: str
        Specify custom ADIOS variable name (default is 'CartGridField').
      tag: str
        Specify dataset tag for use in the command line mode.
      label: str
        Specify dataset label for use in the command line mode.
      ctx: dict
        Copy content of the specified ctx dictionary.
      comp_grid: bool
        A flag to ignore grid mapping.
      mapc2p_name: str
        The name of the file containg the c2p mapping.
      mapc2p_vel_name: str
        The name of the file containg the c2p mapping just for velocity.
      reader_name: str
        Reader can be specified to bypass the automatic selection.
      load: bool = True
        Automatically the data to memory; when set to False, data can be loaded later
        using the load() method.
      click_mode: bool = False
        Enables command-line behavior like prompting when a
        var_name is either missing or doesn't match any available.

    Returns:
      A populated :class:`postgkyl.GData` instance.
    """
    return GData(file_name, comp=comp,
        z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5,
        var_name=var_name, tag=tag, label=label, ctx=ctx,
        comp_grid=comp_grid, mapc2p_name=mapc2p_name,
        mapc2p_vel_name=mapc2p_vel_name, reader_name=reader_name,
        load=load, click_mode=click_mode)

  def many(self, pattern: str,
      comp: int | str | None = None,
      z0: int | str | None = None, z1: int | str | None = None,
      z2: int | str | None = None, z3: int | str | None = None,
      z4: int | str | None = None, z5: int | str | None = None,
      var_name: str = "CartGridField",
      tag: str = "default", label: str = "",
      ctx: dict | None = None,
      comp_grid: bool = False, mapc2p_name: str = "", mapc2p_vel_name: str = "",
      reader_name: str = "", load: bool = True,
      click_mode: bool = False) -> DatasetGroup:
    """Load every file matching a glob ``pattern`` into a ``DatasetGroup``.

    Files are loaded in sorted order so frame sweeps stay in sequence. Every
    argument after ``pattern`` is forwarded to :class:`postgkyl.GData` for each
    matched file (see :meth:`__call__` for the per-argument documentation).

    Args:
      pattern: str
        A glob pattern (e.g. ``'elc_M0_*.gkyl'``) matched against the
        filesystem; matches are loaded in sorted order.

    Returns:
      A :class:`postgkyl.DatasetGroup` of the loaded datasets.

    Raises:
      FileNotFoundError: if no files match ``pattern``.
    """
    files = sorted(glob(pattern))
    if not files:
      raise FileNotFoundError(f"No files match pattern: {pattern!r}")
    # end
    return DatasetGroup([GData(f, comp=comp,
        z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5,
        var_name=var_name, tag=tag, label=label, ctx=ctx,
        comp_grid=comp_grid, mapc2p_name=mapc2p_name,
        mapc2p_vel_name=mapc2p_vel_name, reader_name=reader_name,
        load=load, click_mode=click_mode) for f in files])

  def outputs(self, extensions: str = "bp,gkyl") -> dict:
    """Discover Gkeyll output filename stems in the current directory.

    Args:
      extensions: str
        Comma-separated list of file extensions to scan (default
        ``'bp,gkyl'``).

    Returns:
      A dict mapping each extension to a sorted list of unique stems.
    """
    return find_output_stems(extensions)


load = _Loader()
