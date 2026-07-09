"""ADIOS2 reader for Gkeyll's legacy ``.bp`` output.

Predates the native ``.gkyl`` binary format; still used by older simulation
outputs and by some diagnostic (dynvector) files. ``adios2`` is an OPTIONAL
dependency (``pip install postgkyl[adios]``): its absence must never raise at
registry-scan time, only make :meth:`GkylAdiosReader.is_compatible` return
``False`` so the next reader in the registry gets a chance.
"""

from __future__ import annotations

import re
from typing import Tuple

import numpy as np

try:
  import adios2
except ImportError:
  adios2 = None
# end

from postgkyl.numerics import idx_parser
from . import mapping


class GkylAdiosReader:
  """Provides a framework to read Gkeyll ADIOS2 output."""

  def __init__(self, file_name: str, ctx: dict | None = None,
      var_name: str = "CartGridField",
      axes: tuple | None = (None, None, None, None, None, None),
      comp: int | slice | None = None, **kwargs):
    """Initialize the instance of the ADIOS reader.

    Args:
      file_name: path to the ``.bp`` file (or directory, for the BP4 engine).
      ctx: dict passing context/metadata back to the caller.
      var_name: the field variable to read (frame files only).
      axes: partial-load selectors, one per spatial axis.
      comp: partial-load component selector.
      **kwargs: unused; keeps the constructor signature uniform across the
        reader registry.
    """
    self._file_name = str(file_name)
    self.var_name = var_name

    self.axes = axes
    self.comp = comp

    self.lower: np.ndarray | None = None
    self.upper: np.ndarray | None = None
    self.num_comps: int | None = None
    self.cells: np.ndarray | None = None

    self.is_frame = False
    self.is_diagnostic = False

    self.ctx = ctx if ctx is not None else {}
    if "grid_type" not in self.ctx:
      self.ctx["grid_type"] = "uniform"

  def is_compatible(self) -> bool:
    """Checks if the file can be read with the ADIOS2 reader."""
    if adios2 is None:
      return False
    # end
    try:
      fh = adios2.FileReader(self._file_name)
      for vn in fh.available_variables():
        if "TimeMesh" in vn:
          self.is_diagnostic = True
          fh.close()
          return True
        # end
      # end

      # ADIOS2 can also open a plain HDF5 file (it ships an HDF5 engine), so
      # a Gkeyll or FLASH .h5 file would otherwise look like a valid "frame"
      # here too. A genuine Gkeyll ADIOS frame always carries these grid
      # attributes (required by _preload_frame); their absence means this
      # file belongs to a different reader (GkylH5Reader/FlashH5Reader).
      available_attrs = fh.available_attributes()
      if "lowerBounds" not in available_attrs or "numCells" not in available_attrs:
        fh.close()
        return False
      # end

      available_var_names = ", ".join(
          f"'{vn}'" for vn in fh.available_variables())
      if self.var_name not in fh.available_variables():
        self.ctx["var_names"] = available_var_names
      # end
      self.is_frame = True
      fh.close()
      return True
    except (TypeError, AttributeError, RuntimeError, FileNotFoundError, OSError):
      return False
    # end

  def _create_offset_count(self, num_elems: np.ndarray, zs: tuple,
      comp: int | slice | None, grid: list | None = None
      ) -> Tuple[tuple, tuple]:
    num_dims = len(num_elems)
    count = np.copy(num_elems)
    offset = np.zeros(num_dims, np.int32)
    cnt = 0
    for d, z in enumerate(zs):
      if d < num_dims - 1 and z is not None:  # last dim stores comp
        z = idx_parser(z, grid[d])
        if isinstance(z, int):
          offset[d] = z
          count[d] = 1
        elif isinstance(z, slice):
          offset[d] = z.start
          count[d] = z.stop - z.start
        else:
          raise TypeError("'z' is neither number or slice")
        # end
        cnt += 1
      # end
    # end

    if comp is not None:
      comp = idx_parser(comp)
      if isinstance(comp, int):
        offset[-1] = comp
        count[-1] = 1
      elif isinstance(comp, slice):
        offset[-1] = comp.start
        count[-1] = comp.stop - comp.start
      else:
        raise TypeError("'comp' is neither number or slice")
      # end
      cnt += 1
    # end

    if cnt > 0:
      return tuple(offset), tuple(count)
    return (), ()

  def _preload_frame(self) -> None:
    fh = adios2.FileReader(self._file_name)

    # Postgkyl conventions require the attributes to be arrays even for 1D data.
    self.lower = np.atleast_1d(fh.read_attribute("lowerBounds"))
    self.upper = np.atleast_1d(fh.read_attribute("upperBounds"))
    self.cells = np.atleast_1d(fh.read_attribute("numCells"))
    available_attrs = fh.available_attributes()
    if "changeset" in available_attrs:
      self.ctx["changeset"] = fh.read_attribute_string("changeset")
    if "builddate" in available_attrs:
      self.ctx["builddate"] = fh.read_attribute_string("builddate")
    if "polyOrder" in available_attrs:
      self.ctx["poly_order"] = int(fh.read_attribute("polyOrder"))
      self.ctx["is_modal"] = True
    if "basisType" in available_attrs:
      self.ctx["basis_type"] = fh.read_attribute_string("basisType")
      self.ctx["is_modal"] = True
    if "charge" in available_attrs:
      self.ctx["charge"] = float(fh.read_attribute("charge"))
    if "mass" in available_attrs:
      self.ctx["mass"] = float(fh.read_attribute("mass"))
    if "time" in fh.available_variables():
      self.ctx["time"] = fh.read("time")
    if "frame" in fh.available_variables():
      self.ctx["frame"] = fh.read("frame")
    # end

    fh.close()

  def _load_frame(self) -> Tuple[list, np.ndarray]:
    fh = adios2.FileReader(self._file_name)

    if self.var_name not in fh.available_variables():
      fh.close()
      raise ValueError(
          f"Could not find the variable '{self.var_name}'; available "
          f"variables are: {self.ctx.get('var_names', '')}")
    # end

    num_dims = len(self.cells)
    grid = [np.linspace(self.lower[d], self.upper[d], self.cells[d] + 1)
        for d in range(num_dims)]
    var_shape = fh.available_variables()[self.var_name]["Shape"]
    num_elems = np.array([v for v in var_shape.split(",")], dtype=np.int32)
    offset, count = self._create_offset_count(num_elems, self.axes, self.comp, grid)
    if offset:
      data = fh.read(self.var_name, start=offset, count=count)
    else:
      data = fh.read(self.var_name)
    # end

    # Adjust boundaries for 'offset' and 'count' (uniform grid only -- this
    # reader never sees ctx["grid_type"] == "mapped"; that state is set later
    # by the `map` verb, never by a reader).
    dz = (self.upper - self.lower) / self.cells
    if offset:
      self.lower = self.lower + offset[:num_dims] * dz
      self.cells = self.cells - offset[:num_dims]
    # end
    if count:
      self.upper = self.lower + count[:num_dims] * dz
      self.cells = count[:num_dims]
    # end

    # Create sparse uniform grid, corrected for ghost cells. Coordinate maps
    # are applied afterwards by the ``map`` verb, not while reading.
    mapping.adjust_for_ghost_cells(self.lower, self.upper, self.cells, data.shape)
    grid = mapping.uniform_grid(self.lower, self.upper, self.cells)
    self.ctx["grid_type"] = "uniform"

    fh.close()
    return grid, data

  def _load_diagnostic(self) -> Tuple[list, np.ndarray]:
    fh = adios2.FileReader(self._file_name)

    def natural_sort(items):
      convert = lambda text: int(text) if text.isdigit() else text.lower()
      key = lambda k: [convert(c) for c in re.split("([0-9]+)", k)]
      return sorted(items, key=key)
    # end

    time_lst = natural_sort(
        vn for vn in fh.available_variables() if "TimeMesh" in vn)
    data_lst = natural_sort(
        vn for vn in fh.available_variables() if "Data" in vn)

    data, grid = np.array([[]]), np.array([])
    for i in range(len(data_lst)):
      if i == 0:
        data = np.atleast_1d(fh.read(data_lst[i]))
        grid = np.atleast_1d(fh.read(time_lst[i]))
      else:
        next_data = np.atleast_1d(fh.read(data_lst[i]))
        next_grid = np.atleast_1d(fh.read(time_lst[i]))
        # A restart can produce a chunk missing its second dimension.
        if next_data.ndim < 2:
          next_data = np.expand_dims(next_data, axis=1)
        # end
        data = np.append(data, next_data, axis=0)
        grid = np.append(grid, next_grid, axis=0)
      # end
    # end
    fh.close()

    return [np.squeeze(grid)], data

  # ---- Exposed functions -----
  def preload(self) -> None:
    """Loads metadata."""
    if self.is_frame:
      self._preload_frame()
      self.ctx["cells"] = self.cells
      self.ctx["lower"] = self.lower
      self.ctx["upper"] = self.upper
    # end

  def load(self) -> Tuple[list, np.ndarray]:
    """Loads data.

    Returns:
      A tuple including a grid list and a data NumPy array.

    Notes:
      Needs to be called after ``preload``.
    """
    if self.is_frame:
      grid, data = self._load_frame()
    elif self.is_diagnostic:
      grid, data = self._load_diagnostic()
    else:
      raise TypeError(f"'{self._file_name}' is neither a frame nor a diagnostic ADIOS2 file")
    # end

    self.ctx["num_comps"] = data.shape[-1]
    return grid, data
