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

import os
import re
from glob import glob

from postgkyl.data.gdata import GData
from postgkyl.group import DatasetGroup


def find_output_stems(extensions: str = "bp,gkyl", path: str = ".") -> dict:
  """Map each extension to the sorted unique Gkeyll filename stems in ``path``.

  Frame indices and a trailing ``_restart`` are stripped from each stem.
  """
  result = {}
  for ext in extensions.split(","):
    unique = []
    for fn in glob(f"{path}/*.{ext:s}"):
      stem = os.path.basename(fn)[: -(len(ext) + 1)]
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
      comp_grid: bool = False,
      reader_name: str = "", load: bool = True, cli_mode: bool = False) -> GData:
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
      reader_name: str
        Reader can be specified to bypass the automatic selection.
      load: bool = True
        Automatically the data to memory; when set to False, data can be loaded later
        using the load() method.
      cli_mode: bool = False
        Enables command-line behavior like prompting when a
        var_name is either missing or doesn't match any available.

    Returns:
      A populated :class:`postgkyl.GData` instance.
    """
    return GData(file_name, comp=comp,
        z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5,
        var_name=var_name, tag=tag, label=label, ctx=ctx,
        comp_grid=comp_grid, reader_name=reader_name,
        load=load, cli_mode=cli_mode)

  def many(self, pattern: str,
      comp: int | str | None = None,
      z0: int | str | None = None, z1: int | str | None = None,
      z2: int | str | None = None, z3: int | str | None = None,
      z4: int | str | None = None, z5: int | str | None = None,
      var_name: str = "CartGridField",
      tag: str = "default", label: str = "",
      ctx: dict | None = None,
      comp_grid: bool = False,
      reader_name: str = "", load: bool = True,
      cli_mode: bool = False) -> DatasetGroup:
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
        comp_grid=comp_grid, reader_name=reader_name,
        load=load, cli_mode=cli_mode) for f in files])

  def gk_distf(self, name: str, species: str,
      frame: int | str | list | tuple,
      *, tag: str = "f", suffix: str = "",
      use_c2p_vel: bool = False, use_mc2nu: bool = False, use_mapc2p: bool = False,
      block_idx: int | None = None, interp: int | None = None,
      jf_file: str | None = None, mapc2p_vel_file: str | None = None,
      jacobvel_file: str | None = None, mc2nu_file: str | None = None,
      mapc2p_file: str | None = None,
      jacobtot_inv_file: str | None = None) -> "GData | DatasetGroup":
    """Load and interpolate a gyrokinetic distribution function.

    The script-side equivalent of the CLI ``gk_distf`` command: it reads the
    saved ``Jf`` (distribution times one or more Jacobians) together with the
    velocity/configuration Jacobians, divides them out, and interpolates onto a
    nodal grid, optionally applying velocity- and position-space coordinate
    mappings. Unlike :meth:`__call__` it returns *interpolated* data ready for
    array math and plotting.

    A single ``frame`` returns a :class:`postgkyl.GData`; a list/tuple of frames
    or a range string (e.g. ``'0:10'``) returns a :class:`postgkyl.DatasetGroup`
    (one member per frame, labelled by frame number), mirroring
    :meth:`many`.

    Args:
      name: str
        Simulation name prefix (e.g. ``'gk_lorentzian_mirror'``).
      species: str
        Species name (e.g. ``'ion'`` or ``'elc'``).
      frame: int | str | list | tuple
        Frame index, comma-separated indices, or a ``'start:stop[:step]'`` /
        ``':'`` range (range bounds default to the frames found on disk).
      tag: str
        Tag for the resulting dataset(s).
      suffix: str
        Use ``<name>-<species>_<suffix>_<frame>.gkyl`` as the input distribution.
      use_c2p_vel: bool
        Convert velocity-space computational coordinates to physical ones using
        the ``mapc2p_vel`` mapping.
      use_mc2nu: bool
        Convert non-uniform computational coordinates to field-aligned ones.
      use_mapc2p: bool
        Convert position-space computational coordinates to Cartesian/cylindrical.
      block_idx: int | None
        Use block-specific files with a ``_b<idx>`` prefix.
      interp: int | None
        Interpolate onto a general mesh of the specified amount.
      jf_file, mapc2p_vel_file, jacobvel_file, mc2nu_file, mapc2p_file,
      jacobtot_inv_file: str | None
        Explicit filename overrides; each defaults to the standard naming
        convention derived from ``name``/``species``/``block_idx`` when omitted.

    Returns:
      A :class:`postgkyl.GData` for a single frame, otherwise a
      :class:`postgkyl.DatasetGroup` with one member per frame.
    """
    from postgkyl.loaders.gk_distf import load_gk_distf, resolve_frames

    frames = resolve_frames(frame, name=name, species=species,
        suffix=suffix, block_idx=block_idx)
    datasets = []
    for f in frames:
      out = load_gk_distf(name=name, species=species, frame=f,
          tag=tag, suffix=suffix,
          use_c2p_vel=use_c2p_vel, use_mc2nu=use_mc2nu, use_mapc2p=use_mapc2p,
          block_idx=block_idx, interp=interp,
          jf_file=jf_file, mapc2p_vel_file=mapc2p_vel_file,
          jacobvel_file=jacobvel_file, mc2nu_file=mc2nu_file,
          mapc2p_file=mapc2p_file, jacobtot_inv_file=jacobtot_inv_file)
      if len(frames) > 1:
        out.set_label(str(f))
      # end
      datasets.append(out)
    # end

    if len(datasets) == 1 and not isinstance(frame, (list, tuple)):
      return datasets[0]
    # end
    return DatasetGroup(datasets)

  def pkpm(self, name: str, species: str, idx: str | int, poly_order: int, *,
      tag: str | None = None, label: str | None = None) -> GData:
    """Load, interpolate, and frame-transform Gkeyll PKPM data.

    The script-side equivalent of the CLI ``pkpm`` command: it loads the PKPM
    distribution and its companion ``pkpm_vars`` file, interpolates them, and
    applies the Laguerre-compose + frame-transform pipeline, returning a
    :class:`postgkyl.GData` ready for array math and plotting.

    Args:
      name: str
        Root name (file prefix) of the simulation.
      species: str
        Species name.
      idx: str | int
        Frame/file number.
      poly_order: int
        Polynomial order of the DG representation.
      tag: str | None
        Optional tag for the resulting dataset.
      label: str | None
        Optional label for the resulting dataset.

    Returns:
      A populated, interpolated :class:`postgkyl.GData` instance.
    """
    from postgkyl.loaders.pkpm import load_pkpm
    return load_pkpm(name, species, idx, poly_order, tag=tag, label=label)

  def gk_quantity(self, quantity: str, species: str | None, name: str,
      frame: int | str | None = None, *, path: str = "./",
      tag: str = "default", label: str | None = None,
      **extra) -> "GData | DatasetGroup":
    """Load a pre-named gyrokinetic quantity from simulation output files.

    The script-side equivalent of the CLI ``gk-load-quantity`` command: it
    resolves ``quantity`` through the gyrokinetic quantity registry, loads the
    required source files, computes the quantity, and returns ready data.

    A single resulting dataset is returned as a :class:`postgkyl.GData`;
    multiple (several species and/or frames) are returned as a
    :class:`postgkyl.DatasetGroup`.

    Args:
      quantity: str
        Registered quantity name (use ``pg.load.gk_quantities()`` to list).
      species: str | None
        Species name or comma-separated list; ``None`` for species-independent
        quantities.
      name: str
        Simulation name prefix (e.g. ``'gk_sheath_2x2v_p1'``).
      frame: int | str | None
        Frame number, comma-separated indices, or a ``'start:stop[:step]'`` /
        ``':'`` range (``None`` selects all available frames).
      path: str
        Directory containing the simulation files.
      tag: str
        Tag for the output dataset(s).
      label: str | None
        Label override; defaults to the quantity's registered label.
      **extra:
        Extra per-quantity parameters (e.g. ``dir=1``, ``mass=0.1``).

    Returns:
      A :class:`postgkyl.GData` for a single result, otherwise a
      :class:`postgkyl.DatasetGroup`.
    """
    from postgkyl.loaders.gk_quantity import load_gk_quantity
    datasets = load_gk_quantity(quantity, species, name, frame, path=path,
        tag=tag, label=label, **extra)
    if len(datasets) == 1:
      return datasets[0]
    # end
    return DatasetGroup(datasets)

  def gk_quantities(self) -> list:
    """Return the list of registered gyrokinetic quantity names."""
    from postgkyl.loaders.gk_quantity import available_quantities
    return available_quantities()

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
