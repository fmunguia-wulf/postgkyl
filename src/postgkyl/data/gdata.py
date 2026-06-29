"""Module including Gkeyll data class"""

from typing import Literal, Tuple
import numbers
import numpy as np

try:
  import adios2
  has_adios = True
except ModuleNotFoundError:
  has_adios = False
# end

from postgkyl.data.gkyl_reader import GkylReader
from postgkyl.data.gkyl_adios_reader import GkylAdiosReader
from postgkyl.data.gkyl_h5_reader import GkylH5Reader
from postgkyl.data.flash_h5_reader import FlashH5Reader
from postgkyl.data.write import write as write_impl
import postgkyl.gk.gkeyll_enums as gkenums


class GData(object):
  """Provides interface to (not only) Gkeyll output data.

  GData serves as a baseline interface to Gkeyll data. It is used for
  loading Gkeyll data and serves is input to many Postgkyl
  functions. Represents a dataset in the Postgkyl command line mode.

  Examples:
    import postgkyl as pg
    data = pg.GData('file.gkyl', comp=1)

  """

  def __init__(self, file_name: str = "",
      comp: int | str | None = None,
      z0: int | str | None = None, z1: int | str | None = None,
      z2: int | str | None = None, z3: int | str | None = None,
      z4: int | str | None = None, z5: int | str | None = None,
      var_name: str = "CartGridField",
      tag: str = "default", label: str = "",
      ctx: dict | None = None,
      comp_grid: bool = False, mapc2p_name: str = "", mapc2p_vel_name: str = "",
      reader_name: str = "", load: bool = True, click_mode: bool = False):
    """Initializes the Data class with a Gkeyll output file.

    Args:
      fileName: str
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
    """
    self._grid = None
    self._values = None  # (N+1)D narray of values

    # Context dictionary to store metadata, filled by the reader.
    self.ctx = {}
    
    # Allow to copy input context variable
    if ctx:
      for key in ctx:
        self.ctx[key] = ctx[key]

    self._tag = tag
    self._comp_grid = comp_grid  # flag to disregard the mapped grid
    self._label = ""
    self._custom_label = label
    self._var_name = var_name
    self._file_name = str(file_name)
    self._mapc2p_name = mapc2p_name
    self._mapc2p_vel_name = mapc2p_vel_name
    self.color = None

    self._neighbors = []

    self._status = True

    zs = (z0, z1, z2, z3, z4, z5)

    readers = {
      "gkyl": GkylReader,
      "adios": GkylAdiosReader,
      "h5": GkylH5Reader,
      "flash": FlashH5Reader,
    }
    if self._file_name:
      reader_set = False
      if reader_name in readers:
        # Keep only the user-specified reader
        reader = readers[reader_name]
        readers.clear()
        readers[reader_name] = reader
      # end
      for key, rd in readers.items():
        self._reader = rd(file_name=self._file_name, ctx=self.ctx, var_name=var_name,
          c2p=mapc2p_name, c2p_vel=mapc2p_vel_name, axes=zs, comp=comp,
          click_mode=click_mode)
        if self._reader.is_compatible():
          reader_set = True
          break
        # end
      # end
      if not reader_set:
        raise NameError(f"'file_name' was specified ({self._file_name}) but cannot be read with {list(readers)}")
      # end

      self._reader.preload()
      if load:
        self._grid, self._values = self._reader.load()
      # end
    # end

  # ---- Tag ----
  def get_tag(self) -> str:
    return self._tag

  def set_tag(self, tag: str = "") -> None:
    if tag:
      self._tag = tag
    # end

  tag = property(get_tag, set_tag)

  # ---- Label ----
  def get_label(self) -> str:
    if self._custom_label:
      return self._custom_label
    else:
      return self._label
    # end

  def set_label(self, label: str) -> None:
    self._label = label

  label = property(get_label, set_label)

  def get_custom_label(self):
    return self._custom_label

  # ---- Status ----
  def activate(self) -> None:
    self._status = True

  def deactivate(self) -> None:
    self._status = False

  def get_status(self) -> bool:
    return self._status

  status = property(get_status)

  # ---- Input file ----
  def get_input_file(self) -> str:
    if not has_adios:
      raise ModuleNotFoundError("ADIOS2 is not installed")
    # end

    fh = adios2.open(self._file_name, "rra")
    input_file = fh.read_attribute_string("inputfile")[0]
    fh.close()
    return input_file

  # ---- Number of Cells ----
  def get_num_cells(self) -> np.ndarray:
    if self.ctx.get("cells") is not None:
      return self.ctx["cells"]
    elif self._values is not None:
      num_dims = len(self._values.shape) - 1
      cells = np.zeros(num_dims, np.int32)
      for d in range(num_dims):
        cells[d] = int(self._values.shape[d])
      # end
      return cells
    else:
      return 0
    # end

  num_cells = property(get_num_cells)

  # ---- Number of Components ----
  def get_num_comps(self) -> int:
    if self.ctx.get("num_comps"):
      return self.ctx["num_comps"]
    elif self._values is not None:
      return int(self._values.shape[-1])
    else:
      return 0
    # end

  num_comps = property(get_num_comps)

  # ---- Number of Dimensions -----
  def get_num_dims(self, squeeze: bool = False) -> int:
    if self.ctx.get("cells") is not None:
      num_dims = len(self.ctx["cells"])
    elif self._values is not None:
      num_dims = int(len(self._values.shape) - 1)
    else:
      return 0
    # end
    if squeeze:
      cells = self.get_num_cells()
      for d in range(num_dims):
        if cells[d] == 1:
          num_dims = num_dims - 1
        # end
      # end
    # end
    return num_dims

  num_dims = property(get_num_dims)

  # ---- Grid Bounds ----
  def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
    if "lower" in self.ctx.keys() and "upper" in self.ctx.keys():
      return self.ctx["lower"], self.ctx["upper"]
    elif self._grid is not None:
      num_dims = len(self._values.shape) - 1
      lo, up = np.zeros(num_dims), np.zeros(num_dims)
      for d in range(num_dims):
        lo[d] = self._grid[d].min()
        up[d] = self._grid[d].max()
      # end
      return lo, up
    else:
      return None, None
    # end

  bounds = property(get_bounds)

  # ---- Grid and Values ----
  def get_grid(self) -> list:
    return self._grid

  def set_grid(self, grid: list) -> None:
    self._grid = grid
    num_dims = self.get_num_dims()
    lo, up = np.zeros(num_dims), np.zeros(num_dims)
    for d in range(num_dims):
      lo[d] = self._grid[d].min()
      up[d] = self._grid[d].max()
    self.ctx["lower"] = lo
    self.ctx["upper"] = up

  grid = property(get_grid, set_grid)

  def get_grid_type(self) -> str:
    return self.ctx["grid_type"]

  def get_values(self) -> np.ndarray:
    return self._values

  def set_values(self, values) -> None:
    self._values = values
    if "cells" not in self.ctx or not np.array_equal(values.shape[:-1], self.ctx["cells"]):
      self.ctx["cells"] = values.shape[:-1]
    if "num_comps" not in self.ctx or values.shape[-1] != self.ctx["num_comps"]:
      self.ctx["num_comps"] = values.shape[-1]

  values = property(get_values, set_values)

  def __getitem__(self, comp):
    """Subscript the dataset by component, then by grid index.

    The values array is stored as an (N+1)D array with shape
    ``(cells_0, ..., cells_{N-1}, num_comps)`` where the last axis is the
    component axis. The first subscript selects the component(s) along that
    last axis; chaining a second subscript then indexes the leading grid
    axes of the returned array.

    Examples:
      data[2][:]  -> component 2, all grid values along it
      data[:][0]  -> all components at z0 = 0

    Args:
      comp: int or slice
        Component index or slice to select along the component axis.

    Returns:
      A numpy array view selecting the requested component(s). Subsequent
      subscripts apply standard numpy indexing to the grid axes.
    """
    if self._values is None:
      raise ValueError("GData values are not loaded; cannot subscript.")
    return self._values[..., comp]

  def __setitem__(self, comp, value):
    """Assign to component(s) of the dataset in place.

    Mirrors :meth:`__getitem__`: the subscript selects the component(s)
    along the last (component) axis and writes ``value`` into them.

    Example:
      data[2:4] = data[2:4] * mi / eV  # rescale components 2 and 3

    Args:
      comp: int or slice
        Component index or slice to assign along the component axis.
      value:
        Array (or scalar) broadcastable to the selected component(s).
    """
    if self._values is None:
      raise ValueError("GData values are not loaded; cannot subscript.")
    self._values[..., comp] = value

  def push(self, grid, values):
    self.set_values(values)
    self.set_grid(grid)
    return self

  # ---- Neighboring Blocks ----
  def set_neighbors(self, dataspace):
    data_list = list(dataspace)
    num_dims = self.get_num_dims()
    for dim in range(num_dims):
      self._neighbors.append([None, None])
      for data in data_list:
        if num_dims == 1:
          if np.isclose(self.get_grid()[dim][0], data.get_grid()[dim][-1]):
            self._neighbors[dim][0] = data
          elif np.isclose(self.get_grid()[dim][-1], data.get_grid()[dim][0]):
            self._neighbors[dim][1] = data
        elif num_dims == 2:
          if np.isclose(self.get_grid()[dim][0], data.get_grid()[dim][-1]) and np.isclose(self.get_grid()[not dim][0], data.get_grid()[not dim][0]):
            self._neighbors[dim][0] = data
          elif np.isclose(self.get_grid()[dim][-1], data.get_grid()[dim][0]) and np.isclose(self.get_grid()[not dim][0], data.get_grid()[not dim][0]):
            self._neighbors[dim][1] = data
        elif num_dims == 3:
          rem_dims = list(range(num_dims)).remove(dim)
          if np.isclose(self.get_grid()[dim][0], data.get_grid()[dim][-1]) and np.isclose(self.get_grid()[rem_dims[0]][0], data.get_grid()[rem_dims[0]][0]) and np.isclose(self.get_grid()[rem_dims[1]][0], data.get_grid()[rem_dims[1]][0]):
            self._neighbors[dim][0] = data
          elif np.isclose(self.get_grid()[dim][0], data.get_grid()[dim][-1]) and np.isclose(self.get_grid()[rem_dims[0]][0], data.get_grid()[rem_dims[0]][0]) and np.isclose(self.get_grid()[rem_dims[1]][0], data.get_grid()[rem_dims[1]][0]):
            self._neighbors[dim][1] = data
        # end
      # end
    # end

  def _dict_has_key_from_group(self, dict_in, group_members_in):
    """
    Check if a dictionary with key-value pairs, where the key is the name of a group and
    the value a list of group members (as strings), has a member from a given
    group.
    """
    return not dict_in.keys().isdisjoint(group_members_in)

  # ---- Info -----
  def info(self, index: int = 0, header: bool = True) -> str:
    """Prints GData object information.

    Prints time (only when available), number of components, dimension
    spans, extremes for a GData object.

    Args:
      index: int = 0
        Dataset index shown in the header (the dataset's position within its
        tag); defaults to 0 for a standalone dataset.
      header: bool = True
        Prepend a ``label (tag#index)`` header line. The CLI sets this False
        because it prints its own colored header.

    Returns:
      output: str
        A list of strings with the informations
    """
    values = self.values
    num_comps = self.num_comps
    num_dims = self.num_dims
    num_cells = self.num_cells
    lower, upper = self.bounds

    # Groups of metadata.
    info_groups = {
      "time_info" : ["time","frame"],
      "grid_info" : ["lower","upper","cells","grid_type"],
      "basis_info" : ["poly_order","basis_type","is_modal","num_comps"],
      "build_info" : ["changeset","builddate"], 
      "geometry_info": ["geometry_type", "geqdsk_sign_convention"],
      "species_info": ["mass","charge","adiabatic_gamma","vdim"],
    }

    output = ""

    if header:
      lbl = self.get_label()
      output += f"{lbl:s}{' ' if lbl else '':s}({self.get_tag():s}#{index:d})\n"
    # end

    printed_keys = []

    if "time" in self.ctx.keys():
      printed_keys.append("time")
      output += f"├─ Time: {self.ctx['time']:e}\n"
    # end

    if "frame" in self.ctx.keys():
      printed_keys.append("frame")
      output += f"├─ Frame: {self.ctx['frame']:d}\n"
    # end

    output += f"├─ Number of components: {num_comps:d}\n"
    output += f"├─ Number of dimensions: {num_dims:d}\n"
    if self._dict_has_key_from_group(self.ctx, info_groups["grid_info"]):
      output += f"├─ Grid: ({self.get_grid_type():s})\n"
      if "lower" in self.ctx.keys() and "upper" in self.ctx.keys() and "cells" in self.ctx.keys():
        for d in range(num_dims - 1):
          output += f"│  ├─ Dim {d:d}: Num. cells: {num_cells[d]:d}; "
          output += f"Lower: {lower[d]:e}; Upper: {upper[d]:e}\n"
        # end
      # end

      output += f"│  └─ Dim {num_dims - 1:d}: Num. cells: {num_cells[-1]:d}; "
      output += f"Lower: {lower[-1]:e}; Upper: {upper[-1]:e}"
    # end

    if values is not None:
      maximum = np.nanmax(values)
      max_idx = np.unravel_index(np.nanargmax(values), values.shape)
      minimum = np.nanmin(values)
      min_idx = np.unravel_index(np.nanargmin(values), values.shape)
      # Cast indices to plain Python ints so they format as (218,) rather
      # than (np.int64(218),).
      max_pos = tuple(int(i) for i in max_idx[:num_dims])
      min_pos = tuple(int(i) for i in min_idx[:num_dims])
      output += f"\n├─ Maximum: {maximum:e} at {str(max_pos):s}"
      if num_comps > 1:
        output += f" component {int(max_idx[-1]):d}\n"
      else:
        output += "\n"
      # end
      output += f"├─ Minimum: {minimum:e} at {str(min_pos):s}"
      if num_comps > 1:
        output += f" component {int(min_idx[-1]):d}"
      # end
    # end

    if self._dict_has_key_from_group(self.ctx, info_groups["basis_info"]):
      output += "\n├─ DG info:"
      if "poly_order" in self.ctx.keys():
        printed_keys.append("poly_order")
        output += f"\n│  ├─ Polynomial Order: {self.ctx['poly_order']:d}"
      # end
      if "basis_type" in self.ctx.keys():
        printed_keys.append("basis_type")
        if self.ctx["is_modal"]:
          output += f"\n│  └─ Basis Type: {self.ctx['basis_type']:s} (modal)"
        else:
          output += f"\n│  └─ Basis Type: {self.ctx['basis_type']:s}"
        # end
      # end
    # end

    if self._dict_has_key_from_group(self.ctx, info_groups["build_info"]):
      output += "\n├─ Created with Gkeyll:"
      if "changeset" in self.ctx.keys():
        printed_keys.append("changeset")
        output += f"\n│  ├─ Changeset: {self.ctx['changeset']:s}"
      # end
      if "builddate" in self.ctx.keys():
        printed_keys.append("builddate")
        output += f"\n│  └─ Build Date: {self.ctx['builddate']:s}"
      # end
    # end

    if self._dict_has_key_from_group(self.ctx, info_groups["geometry_info"]):
      output += "\n├─ Geometry info:"
      if "geometry_type" in self.ctx.keys():
        printed_keys.append("geometry_type")
        output += f"\n│  ├─ Type: {gkenums.gkyl_geometry_id[self.ctx['geometry_type']]:s}"
      # end
      if "geqdsk_sign_convention" in self.ctx.keys():
        printed_keys.append("geqdsk_sign_convention")
        output += f"\n│  ├─ GEQDSK sign convention: {self.ctx['geqdsk_sign_convention']:d}"
      # end
    # end
      
    # Print any other keys in the context that were not printed above
    for key, val in self.ctx.items():
      if key not in sum(info_groups.values(), []):
        output += f"\n├─ {key:s}: {val}"
      # end
    # end

    if self._dict_has_key_from_group(self.ctx, info_groups["species_info"]):
      output += "\n├─ Species properties:"
      if "mass" in self.ctx.keys():
        printed_keys.append("mass")
        output += f"\n│  ├─ Mass: {self.ctx['mass']:e}"
      # end
      if "charge" in self.ctx.keys():
        printed_keys.append("charge")
        output += f"\n│  ├─ Charge: {self.ctx['charge']:e}"
      # end
      if "gas_gamma" in self.ctx.keys():
        printed_keys.append("gas_gamma")
        output += f"\n│  ├─ Adiabatic index: {self.ctx['gas_gamma']:e}"
      # end
      if "vdim" in self.ctx.keys():
        printed_keys.append("vdim")
        output += f"\n│  ├─ Velocity dimensions: {self.ctx['vdim']:d}"
      # end
    # end

    print(output)
    print()
    return output

  # ---- Write ----
  def write(self, out_name: str = "",
      extension: Literal["gkyl", "bp", "txt", "npy", "vts"] = "gkyl",
      mode: str = "", var_name: str = "", append: bool = False,
      cleaning: bool = True, norm_axes: bool = False) -> None:
    """Writes data in a file.

    The available formats are Gkeyll .gkyl (default), ADIOS .bp file, ASCII .txt file,
    NumPy .npy file, or VTK structured grid .vts file.

    Args:
      out_name: str
        Specify output file name.
      extension: str = "gkyl"
        Specify file extension (extension).
      var_name: str
        Specify variable name for Adios.
      append: bool = False
        Allows for writing multiple datasets into one file.
      cleaning: bool = True
        Remove temporary files after writing.
      norm_axes: bool = False
        Normalize axes to [-1, 1] for VTK output.

    Returns:
      None
    """
    write_impl(self, out_name=out_name, extension=extension, mode=mode,
      var_name=var_name, append=append, cleaning=cleaning, norm_axes=norm_axes)

  # ---- Context (metadata) ----
  def get_ctx(self) -> dict:
    return self.ctx

  # ====================================================================
  # Fluent / Python-native ergonomics (see REFACTOR_PLAN.md)
  # ====================================================================

  # ---- Copy ----
  def copy(self, data: bool = True) -> "GData":
    """Return a deep copy of this dataset without re-reading any file.

    Args:
      data: bool = True
        When True, the grid and values arrays are copied too. When False,
        only the metadata (tag, label, ctx, ...) is copied and the new
        object has no arrays yet (used internally by ``_result``).
    """
    new = GData(tag=self._tag, label=self._custom_label, ctx=self.ctx)
    new.set_label(self._label)
    new._var_name = self._var_name
    new._file_name = self._file_name
    new._comp_grid = self._comp_grid
    new.color = self.color
    if data and self._values is not None:
      grid_copy = [np.array(g, copy=True) for g in self._grid]
      new.push(grid_copy, np.array(self._values, copy=True))
    # end
    return new

  # ---- Result helper ----
  def _result(self, grid, values, inplace: bool = False,
      tag: str | None = None, label: str | None = None, **ctx_updates) -> "GData":
    """Centralizes the 'mutate self' vs. 'emit a new GData' branch.

    Every verb in ``postgkyl.ops`` funnels its computed (grid, values)
    through here so that the in-place/new-dataset behavior is defined in a
    single place instead of being copy-pasted across commands.
    """
    target = self if inplace else self.copy(data=False)
    target.push(grid, values)
    if tag is not None:
      target.set_tag(tag)
    # end
    if label is not None:
      target._custom_label = label
    # end
    if ctx_updates:
      target.ctx.update(ctx_updates)
    # end
    return target

  # ---- Interpolation state ----
  @property
  def is_interpolated(self) -> bool:
    """Whether the values are safe for element-wise numeric operations.

    Data is operable when it was never modal DG data (e.g. plain numpy
    values or dynvectors) or when it has been explicitly interpolated to a
    nodal/uniform mesh (``ctx['interpolated']`` set by ``ops.interpolate``).
    Raw modal DG coefficients are *not* operable.
    """
    return (not self.ctx.get("is_modal", False)) or self.ctx.get("interpolated", False)

  # ---- Fluent verbs (delegate to postgkyl.ops; lazy import avoids cycles) ----
  def select(self, *, comp=None, z0=None, z1=None, z2=None, z3=None, z4=None, z5=None,
      inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
    """Subselect part of the dataset (coordinate indices/values and components).

    Each coordinate selector ``z0``-``z5`` and ``comp`` accepts an integer
    index, a float coordinate value, or a slice string
    ``'start:end:stride'``; ``comp`` additionally accepts comma-separated
    indices. Unspecified axes are kept in full.

    See :func:`postgkyl.ops.select`.

    Args:
      comp: int or float or str
        Component(s) to keep: an integer index, a comma-separated list of
        indices, or a 'start:end:stride' slice string.
      z0 - z5: int or float or str
        Index, coordinate value, or 'start:end:stride' slice for each
        direction; left unset keeps the whole axis.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The subselected dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.select(self, comp=comp, z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5,
        inplace=inplace, tag=tag, label=label)

  sel = select

  def interpolate(self, basis: str | None = None, p: int | None = None,
      interp: int | None = None, read: bool | None = None,
      inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
    """Interpolate DG (modal or nodal) data onto a uniform mesh.

    Converts the stored DG basis coefficients into nodal values on a uniform
    mesh. When the basis, polynomial order, and interpolation points are not
    given, the values stored in ``data.ctx`` are used. The result is flagged
    ``interpolated=True`` so it becomes safe for element-wise numeric
    operations.

    See :func:`postgkyl.ops.interpolate`.

    Args:
      basis: str or None
        Short DG basis code ('ms', 'ns', 'mo', 'mt', 'gkhyb', 'pkpmhyb');
        defaults to the basis stored in the context.
      p: int or None
        Polynomial order; defaults to the order stored in the context.
      interp: int or None
        Override for the number of interpolation points per direction.
      read: bool or None
        Force reading (True) or recomputing (False) the interpolation
        matrices; None uses the default behavior.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The interpolated dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.interpolate(self, basis=basis, p=p, interp=interp, read=read,
        inplace=inplace, tag=tag, label=label)

  interp = interpolate

  def differentiate(self, basis: str | None = None, p: int | None = None,
      interp: int | None = None, read: bool | None = None, direction: int | None = None,
      inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
    """Interpolate a derivative of DG data onto a uniform mesh.

    Like :meth:`interpolate`, but interpolates a spatial derivative of the DG
    field. ``direction`` selects which axis to differentiate along (default:
    all). The result is flagged ``interpolated=True``.

    See :func:`postgkyl.ops.differentiate`.

    Args:
      basis: str or None
        Short DG basis code ('ms', 'ns', 'mo', 'mt', 'gkhyb', 'pkpmhyb');
        defaults to the basis stored in the context.
      p: int or None
        Polynomial order; defaults to the order stored in the context.
      interp: int or None
        Override for the number of interpolation points per direction.
      read: bool or None
        Force reading (True) or recomputing (False) the interpolation
        matrices; None uses the default behavior.
      direction: int or None
        Axis index along which to take the derivative; None differentiates
        along every direction.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The differentiated, interpolated dataset (a new GData unless inplace
        is True).
    """
    from postgkyl import ops
    return ops.differentiate(self, basis=basis, p=p, interp=interp, read=read,
        direction=direction, inplace=inplace, tag=tag, label=label)

  diff = differentiate

  def dg_local_poly(self, *, npoints: int = 2, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Discontinuous cellwise DG polynomial representation of the data.

    Evaluates the modal DG decomposition at ``npoints`` per cell and inserts a
    NaN at every cell interface, so a plot breaks the curve at each interface
    and shows the inter-cell DG discontinuities.

    See :func:`postgkyl.ops.dg_local_poly`.

    Args:
      npoints: int = 2
        Number of evaluation points per cell.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The cellwise-polynomial dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.dg_local_poly(self, npoints=npoints, inplace=inplace, tag=tag,
        label=label)

  def map(self, mapping, *, space: str = "conf", p: int = 1,
      basis: str = "ms", interp: int | None = None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Deform this dataset's grid onto non-uniform mapped coordinates.

    Reads a coordinate-mapping DG field and replaces a block of grid axes with
    the resulting non-uniform coordinates, leaving the values untouched. A
    configuration-space map (``space='conf'``) deforms the leading axes; a
    velocity-space map (``space='vel'``) deforms the trailing axes. For a
    combined map, chain two calls (one per space).

    See :func:`postgkyl.ops.map`.

    Args:
      mapping: str or GData
        The coordinate-mapping field (filename or loaded GData); its number of
        dimensions sets how many axes are replaced.
      space: str
        ``'conf'`` or ``'vel'`` (see above).
      p: int
        Polynomial order used to interpolate the mapping field.
      basis: str
        DG basis of the mapping field.
      interp: int or None
        Override for the number of interpolation points.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The dataset with its grid deformed (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.map(self, mapping, space=space, p=p, basis=basis,
        interp=interp, inplace=inplace, tag=tag, label=label)

  def integrate(self, axis=None, *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Integrate the data over one or more axes.

    Integrates the values over the requested axes, collapsing each integrated
    dimension. When ``axis`` is None, integrates over all dimensions.

    See :func:`postgkyl.ops.integrate`.

    Args:
      axis: int or tuple or str or None
        Axis or axes to integrate over: an integer, a tuple of integers, or a
        'i,j' / 'i:j' string. None integrates over every dimension.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The integrated dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.integrate(self, axis=axis, inplace=inplace, tag=tag, label=label)

  def fft(self, *, psd: bool = False, iso: bool = False, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Fourier transform (1D) of the data, optionally as a power spectrum.

    Computes the 1D Fourier transform of the values; ``psd`` instead returns
    the power spectral density |FT|^2 over positive frequencies, and ``iso``
    bins that PSD into a 1D isotropic spectrum.

    See :func:`postgkyl.ops.fft`.

    Args:
      psd: bool = False
        Return the power spectral density |FT|^2 over positive frequencies
        instead of the raw transform.
      iso: bool = False
        Bin the PSD into a 1D isotropic (radial) spectrum.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The transformed dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.fft(self, psd=psd, iso=iso, inplace=inplace, tag=tag, label=label)

  def magsq(self, *, coords: str = "0:3", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Magnitude squared of a range of components.

    Sums the squares of the components selected by ``coords`` to form a single
    scalar component (e.g. ``Ex^2 + Ey^2 + Ez^2``).

    See :func:`postgkyl.ops.magsq`.

    Args:
      coords: str = "0:3"
        Component range as a 'lo:hi' slice string; the components in
        ``[lo, hi)`` are squared and summed.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The single-component magnitude-squared dataset (a new GData unless
        inplace is True).
    """
    from postgkyl import ops
    return ops.magsq(self, coords=coords, inplace=inplace, tag=tag, label=label)

  def mask(self, *, filename: str | None = None, lower: float | None = None,
      upper: float | None = None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Mask out values using a mask file or numeric thresholds.

    Returns a masked-array dataset. Exactly one masking source must be given:
    a Gkeyll mask file (masks where the mask field is negative), or numeric
    thresholds (``lower``/``upper``).

    See :func:`postgkyl.ops.mask`.

    Args:
      filename: str or None
        Path to a Gkeyll mask file; values are masked where the mask field is
        negative.
      lower: float or None
        Lower threshold. With ``upper`` set too, values outside
        ``[lower, upper]`` are masked; alone, values below ``lower`` are
        masked.
      upper: float or None
        Upper threshold. Alone, values above ``upper`` are masked.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The masked dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.mask(self, filename=filename, lower=lower, upper=upper,
        inplace=inplace, tag=tag, label=label)

  def relchange(self, reference: "GData", *, comp=None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Relative change of this dataset with respect to ``reference``.

    Computes ``(self - reference) / reference`` component-wise. When ``comp``
    is given, every component of ``self`` is divided by that single reference
    component.

    See :func:`postgkyl.ops.relchange`.

    Args:
      reference: GData
        The reference dataset to compare against.
      comp: int or str or None
        Single reference component to use as the denominator for all
        components; None pairs components one-to-one.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The relative-change dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.relchange(self, reference, comp=comp, inplace=inplace, tag=tag, label=label)

  def current(self, *, qbym: bool = False, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Accumulate the electric current from species moments.

    Sums charge times flow over the species stored in this dataset to form the
    total current density.

    See :func:`postgkyl.ops.current`.

    Args:
      qbym: bool = False
        Use the charge/mass ratio (q/m) instead of the charge q when
        accumulating.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The current dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.current(self, qbym=qbym, inplace=inplace, tag=tag, label=label)

  def agyro(self, bfield: "GData", *, measure: str = "frobenius", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Agyrotropy from this pressure tensor and a magnetic/EM field.

    Measures how far the pressure tensor (this dataset) departs from
    gyrotropy about the field direction taken from ``bfield``.

    See :func:`postgkyl.ops.agyro`.

    Args:
      bfield: GData
        Dataset providing the magnetic / electromagnetic field used to define
        the gyration axis.
      measure: str = "frobenius"
        Agyrotropy measure: 'frobenius' (Frobenius norm of the agyrotropic
        tensor) or 'swisdak' (Swisdak 2015).
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The agyrotropy dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.agyro(self, bfield, measure=measure, inplace=inplace, tag=tag, label=label)

  def energetics(self, ion: "GData", field: "GData", *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Decompose the plasma energy into its components.

    Computes the kinetic, thermal, and electromagnetic energy contributions
    for a two-species plasma, with this dataset taken as the electrons. The
    result is a 7-component dataset carrying the EM field's grid and metadata.

    See :func:`postgkyl.ops.energetics`.

    Args:
      ion: GData
        The ion species moment dataset.
      field: GData
        The electromagnetic field dataset (provides the output grid/metadata).
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The 7-component energetics dataset (a new GData unless inplace is
        True).
    """
    from postgkyl import ops
    return ops.energetics(self, ion, field, inplace=inplace, tag=tag, label=label)

  def parrotate(self, rotator: "GData", *, coords: str = "0:3", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Component of this vector field parallel to ``rotator``.

    Projects this vector field onto the unit direction of ``rotator``:
    ``(u . v_hat) v_hat``.

    See :func:`postgkyl.ops.parrotate`.

    Args:
      rotator: GData
        Dataset whose selected components define the direction vector.
      coords: str = "0:3"
        Component range ('lo:hi') of ``rotator`` that forms the direction
        vector (e.g. '3:6' to rotate along the magnetic field of an EM array).
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The parallel-component dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.parrotate(self, rotator, coords=coords, inplace=inplace, tag=tag, label=label)

  def perprotate(self, rotator: "GData", *, coords: str = "0:3", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Component of this vector field perpendicular to ``rotator``.

    Removes the part of this vector field along the unit direction of
    ``rotator``: ``u - (u . v_hat) v_hat``.

    See :func:`postgkyl.ops.perprotate`.

    Args:
      rotator: GData
        Dataset whose selected components define the direction vector.
      coords: str = "0:3"
        Component range ('lo:hi') of ``rotator`` that forms the direction
        vector (e.g. '3:6' to rotate along the magnetic field of an EM array).
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The perpendicular-component dataset (a new GData unless inplace is
        True).
    """
    from postgkyl import ops
    return ops.perprotate(self, rotator, coords=coords, inplace=inplace, tag=tag, label=label)

  def transform_frame(self, bulk: "GData", *, cdim: int, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Shift this (PKPM) distribution function into the ``bulk`` frame.

    Transforms this distribution function into the frame moving with the
    ``bulk`` velocity.

    See :func:`postgkyl.ops.transform_frame`.

    Args:
      bulk: GData
        Dataset providing the bulk velocity to shift into.
      cdim: int
        Number of configuration-space dimensions.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The frame-shifted distribution (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.transform_frame(self, bulk, cdim=cdim, inplace=inplace, tag=tag, label=label)

  def euler(self, variable: str, *, gas_gamma: float = 5.0 / 3, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Extract a five-moment (Euler) primitive or derived variable.

    Computes a primitive/derived fluid variable from five-moment data.

    See :func:`postgkyl.ops.euler`.

    Args:
      variable: str
        Name of the variable to compute. One of: 'density', 'xvel', 'yvel',
        'zvel', 'vel', 'pressure', 'ke', 'temp', 'sound', 'mach'.
      gas_gamma: float = 5.0 / 3
        Adiabatic index used for pressure, kinetic energy, temperature, sound
        speed, and Mach number.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The requested variable as a dataset (a new GData unless inplace is
        True).
    """
    from postgkyl import ops
    return ops.euler(self, variable, gas_gamma=gas_gamma, inplace=inplace, tag=tag, label=label)

  def tenmoment(self, variable: str, *, gas_gamma: float = 5.0 / 3, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Extract a ten-moment primitive or derived variable.

    Computes a primitive/derived fluid variable from ten-moment data,
    including the full pressure tensor and its components.

    See :func:`postgkyl.ops.tenmoment`.

    Args:
      variable: str
        Name of the variable to compute. One of: 'density', 'xvel', 'yvel',
        'zvel', 'vel', 'pressure', 'ke', 'temp', 'sound', 'mach',
        'pressureTensor', 'pxx', 'pxy', 'pxz', 'pyy', 'pyz', 'pzz'.
      gas_gamma: float = 5.0 / 3
        Adiabatic index used for pressure, kinetic energy, temperature, sound
        speed, and Mach number.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The requested variable as a dataset (a new GData unless inplace is
        True).
    """
    from postgkyl import ops
    return ops.tenmoment(self, variable, gas_gamma=gas_gamma, inplace=inplace, tag=tag, label=label)

  def mhd(self, variable: str, *, gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
      inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
    """Extract an ideal-MHD primitive or derived variable.

    Computes a primitive/derived variable from ideal-MHD state data,
    including magnetic-field components and magnetic pressure.

    See :func:`postgkyl.ops.mhd`.

    Args:
      variable: str
        Name of the variable to compute. One of: 'density', 'xvel', 'yvel',
        'zvel', 'vel', 'Bx', 'By', 'Bz', 'Bi', 'magpressure', 'pressure',
        'temp', 'sound', 'mach'.
      gas_gamma: float = 5.0 / 3
        Adiabatic index used for pressure, temperature, sound speed, and Mach
        number.
      mu_0: float = 1.0
        Vacuum permeability used for magnetic pressure and the derived
        thermodynamic quantities.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The requested variable as a dataset (a new GData unless inplace is
        True).
    """
    from postgkyl import ops
    return ops.mhd(self, variable, gas_gamma=gas_gamma, mu_0=mu_0, inplace=inplace,
        tag=tag, label=label)

  def velocity(self, momentum: "GData", *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Compute velocity from this density and a ``momentum`` dataset.

    Divides the ``momentum`` moments by this density (``momentum / density``)
    to obtain the flow velocity.

    See :func:`postgkyl.ops.velocity`.

    Args:
      momentum: GData
        The momentum moment dataset (numerator).
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The velocity dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.velocity(self, momentum, inplace=inplace, tag=tag, label=label)

  # Note: no fluent ``grid`` method — ``GData.grid`` is the grid-array property.
  # Use ``pg.ops.grid(data)`` for the grid-as-dataset verb.

  def val2coord(self, *, x: str, y: str, periodic: bool = False,
      tag: str | None = None, label: str | None = None):
    """Build new (x, y) datasets from columns of a DynVector.

    Selects component columns of this dataset to use as the x- and y-data of
    new datasets. One output dataset is produced per selected y-component and
    returned as a :class:`postgkyl.group.DatasetGroup`.

    See :func:`postgkyl.ops.val2coord`.

    Args:
      x: str
        Component selector for the x-data: an index, a comma-separated list,
        or a 'lo:hi:step' slice string.
      y: str
        Component selector for the y-data, in the same formats as ``x``. If
        more than one x-component is given, the count must match ``y``.
      periodic: bool = False
        Append the first point to the end of each curve to close periodic
        data.
      tag: str or None
        Tag to assign to the resulting datasets.
      label: str or None
        Label to assign to the resulting datasets.

    Returns:
      DatasetGroup
        A group containing one (x, y) dataset per selected y-component.
    """
    from postgkyl import ops
    return ops.val2coord(self, x=x, y=y, periodic=periodic, tag=tag, label=label)

  def extract_input(self) -> str:
    """Return the decoded input file embedded in this dataset's file.

    Reads and base64-decodes the input file embedded in the underlying Gkeyll
    output (when present).

    See :func:`postgkyl.ops.extract_input`.

    Args:
      none

    Returns:
      str
        The decoded input file text, or an empty string when none is present.
    """
    from postgkyl import ops
    return ops.extract_input(self)

  def laguerre_compose(self, variables, *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Compose PKPM Laguerre coefficients into a full distribution.

    Combines the Laguerre coefficients of this distribution with the PKPM
    ``variables`` dataset to reconstruct the full distribution
    ``f(x, v_par, v_perp)``.

    See :func:`postgkyl.ops.laguerre_compose`.

    Args:
      variables: GData
        The PKPM variables dataset used to compose the Laguerre coefficients.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The composed distribution function (a new GData unless inplace is
        True).
    """
    from postgkyl import ops
    return ops.laguerre_compose(self, variables, inplace=inplace, tag=tag, label=label)

  def fit(self, fit_type: str, *, guess=None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Fit a model to this dataset and return the fitted curve.

    Fits ``fit_type`` to each component of this dataset and returns a new
    ``GData`` holding the fitted values on the data's grid. The per-component
    fit parameters and R^2 are stored in ``ctx['fit_params']`` and
    ``ctx['fit_R2']``.

    See :func:`postgkyl.ops.fit`.

    Args:
      fit_type: str
        Model name (e.g. 'linear', 'gaussian') or an RPN expression
        describing the model to fit.
      guess: str or sequence or None
        Initial parameter guess, as a comma-separated string or a sequence of
        floats; None lets the fitter pick defaults.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The fitted curve as a dataset (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.fit(self, fit_type, guess=guess, inplace=inplace, tag=tag, label=label)

  def growth(self, *, guess=None, minn: int | None = None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Fit an exponential growth rate to time-series data.

    Fits ``e^(2 b t)`` to this (DynVector) dataset and returns the fitted
    exponential curve. The fitted growth rate ``b`` is stored in
    ``ctx['growth_rate']``.

    See :func:`postgkyl.ops.growth`.

    Args:
      guess: str or sequence or None
        Initial guess for the two fit parameters, as a 'a,b' comma-separated
        string or a sequence; None lets the fitter pick defaults.
      minn: int or None
        Minimum number of points to include in the fit window; None uses the
        default.
      inplace: bool = False
        Mutate this dataset instead of returning a new one.
      tag: str or None
        Tag to assign to the resulting dataset.
      label: str or None
        Label to assign to the resulting dataset.

    Returns:
      GData
        The fitted exponential curve (a new GData unless inplace is True).
    """
    from postgkyl import ops
    return ops.growth(self, guess=guess, minn=minn, inplace=inplace, tag=tag, label=label)

  def plot(self,
      arg: str = "",
      figure=0, squeeze: bool = False, subplots: bool = False,
      num_subplot_row: "int | None" = None, num_subplot_col: "int | None" = None,
      multiblock: bool = False,
      streamline: bool = False, sdensity: int = 1,
      quiver: bool = False,
      contour: bool = False, clevels=None, cnlevels: "int | None" = None,
      cont_label: bool = False,
      diverging: bool = False,
      lineouts: "int | None" = None,
      scatter: bool = False,
      xmin: "float | None" = None, xmax: "float | None" = None,
      xscale: float = 1.0, xshift: float = 0.0,
      ymin: "float | None" = None, ymax: "float | None" = None,
      yscale: float = 1.0, yshift: float = 0.0,
      zmin: "float | None" = None, zmax: "float | None" = None,
      zscale: float = 1.0, zshift: float = 0.0,
      xlim: "str | None" = None, ylim: "str | None" = None, zlim: "str | None" = None,
      globalrange: bool = False, cutoffglobalrange: "float | None" = None,
      relax: bool = False, style: "str | None" = None, rcParams=None,
      legend=True, no_legend: bool = False, forcelegend: bool = False,
      legend_axis: "int | None" = None, colorbar: bool = True,
      xlabel: "str | None" = None, ylabel: "str | None" = None,
      clabel: "str | None" = None, title: "str | None" = None,
      subplot_titles: "str | None" = None, subplot_xlabels: "str | None" = None,
      subplot_ylabels: "str | None" = None,
      logx: bool = False, logy: bool = False, logz: bool = False,
      fixaspect: bool = False, aspect: "float | None" = None,
      edgecolors: "str | None" = None, showgrid: bool = True,
      hashtag: bool = False, xkcd: bool = False,
      color: "str | None" = None, markersize: "float | None" = None,
      linewidth: "float | None" = None, linestyle: "str | None" = None,
      figsize=None, jet: bool = False, cmap: "str | None" = None,
      show: bool = True,
      save: bool = False, saveas: "str | None" = None, dpi: int = 200,
      saveframes: "str | None" = None,
      **kwargs):
    """Plot this dataset on a Matplotlib figure.

    Single-dataset entry point mirroring the top-level :func:`postgkyl.plot`
    and the CLI ``plot`` command. The keyword arguments mirror the underlying
    :func:`postgkyl.output.plot` renderer.

    See :func:`postgkyl.output.plot_datasets`.

    Args:
      arg: str
        Matplotlib format string forwarded to the underlying plot call
        (e.g. '.' for markers, '--' for dashed).
      figure: int | Figure | 'dataset'
        Target figure; defaults to 0 so repeated calls overlay. Pass
        'dataset' to give each dataset its own figure.
      squeeze: bool
        Collapse all components into a single panel.
      subplots: bool
        Place each component into its own subplot instead of overlaying.
      num_subplot_row / num_subplot_col: int | None
        Force the subplot grid shape.
      multiblock: bool
        Overlay multi-block data onto a shared figure with a common range.
      streamline / quiver / contour: bool
        Select the 2D rendering style (line/colormap by default).
      sdensity: int
        Streamline density.
      clevels / cnlevels / cont_label:
        Contour levels ('min:max:n' string), level count, and inline-label
        toggle.
      diverging: bool
        Use a diverging colormap centered on zero.
      lineouts: int | None
        Axis index along which to take 1D lineouts of 2D data.
      scatter: bool
        Render markers without connecting lines.
      xmin/xmax, ymin/ymax, zmin/zmax: float | None
        Axis / colour-scale limits.
      xscale/xshift, yscale/yshift, zscale/zshift: float
        Per-axis affine rescaling of grid and values.
      xlim/ylim/zlim: str | None
        Convenience 'min,max' strings (CLI parity) setting the limits above.
      globalrange: bool
        Scan all datasets for a common value/colour range.
      cutoffglobalrange: float | None
        Like globalrange but clips to the given central percentile (0-1).
      relax: bool
        Relax the 1D autoscale (helps with contours).
      style: str | None
        Matplotlib style file (default: Postgkyl).
      rcParams: dict | None
        Extra Matplotlib rcParams overrides.
      legend: bool | list | str
        True/False toggles the legend; a list (e.g. ['1X', '2X']) or
        comma-separated string sets one label per dataset.
      no_legend: bool
        Force-hide the legend (equivalent to legend=False).
      forcelegend: bool
        Show the legend even for a single dataset.
      legend_axis: int | None
        When plotting into multiple subplots, restrict the legend to the
        subplot with this flat index (0-based); None draws it on every
        subplot. When set, per-component _cN suffixes are dropped.
      colorbar: bool
        Colorbar toggle.
      xlabel/ylabel/clabel/title: str | None
        Axis, colorbar, and figure labels.
      subplot_titles / subplot_xlabels / subplot_ylabels: str | None
        Comma-separated per-subplot titles / x-labels / y-labels.
      logx/logy/logz: bool
        Logarithmic scaling per axis.
      fixaspect/aspect, figsize, cmap, color, markersize, linewidth, linestyle:
        Matplotlib appearance controls.
      edgecolors: str | None
        Cell edge colour for 2D pcolormesh plots.
      showgrid: bool
        Draw the background grid (default True).
      hashtag: bool
        Add a #pgkyl watermark.
      xkcd: bool
        Render in Matplotlib's xkcd sketch style.
      jet: bool
        Use the (non-recommended) jet colormap.
      show: bool
        Call plt.show() when done (default True).
      save / saveas / dpi:
        Save the figure to disk (saveas overrides the auto filename; dpi sets
        the resolution).
      saveframes: str | None
        Save each dataset to <saveframes>_<i>.png instead of showing.
      **kwargs:
        Any remaining options are forwarded verbatim to
        :func:`postgkyl.output.plot_datasets` / :func:`postgkyl.output.plot`.

    Returns:
      The figure / axes object produced by the renderer.
    """
    from postgkyl import output
    # A boolean legend=False is the intuitive way to hide the legend; translate
    # it to the no_legend flag that plot_datasets actually honours.
    if legend is False:
      no_legend = True
    # end
    opts = {key: value for key, value in locals().items()
        if key not in ("self", "output", "kwargs")}
    opts.update(kwargs)
    return output.plot_datasets([self], **opts)

  def plotly(self,
      squeeze: bool = False, num_axes: int = None,
      num_subplot_row: "int | None" = None, num_subplot_col: "int | None" = None,
      scatter: bool = False, marker_radius: float = 4.0, markerstyle: str = "circle",
      diverging: bool = False,
      xscale: float = 1.0, xshift: float = 0.0,
      yscale: float = 1.0, yshift: float = 0.0,
      zscale: float = 1.0, zshift: float = 0.0,
      cmin: "float | None" = None, cmax: "float | None" = None,
      cscale: float = 1.0, cshift: float = 0.0,
      clim: "tuple[float, float] | None" = None,
      style: "str | None" = None, rcParams: "dict | None" = None,
      background: str = "dark", invert_cmap: bool = False,
      legend: bool = True, label_prefix: str = "", colorbar: bool = True,
      xlabel: "str | None" = None, ylabel: "str | None" = None,
      zlabel: "str | None" = None, clabel: "str | None" = None,
      title: "str | None" = None,
      logx: bool = False, logy: bool = False, logz: bool = False, logc: bool = False,
      aspect: "str | float | None" = None,
      showgrid: bool = True, hashtag: bool = False, xkcd: bool = False,
      color: "str | None" = None,
      opacity: "float | None" = 1.0,
      scatter_opacity_range: "tuple[float, float] | None" = None,
      scatter_opacity_log: bool = False,
      maximum_points_per_axis: int = 0,
      surface_count: int = 32,
      xrange: "tuple[float, float] | None" = None,
      yrange: "tuple[float, float] | None" = None,
      zrange: "tuple[float, float] | None" = None,
      figsize: "tuple | None" = None,
      cylindrical_to_cartesian: bool = False,
      cmap: "str | None" = None):
    """Interactive Plotly figure of this dataset (2D surface or 3D volume).

    Renders 3D Gkeyll data as a volume/scatter plot, or 2D data as a surface,
    using Plotly.

    See :func:`postgkyl.output.plotly`.

    Args:
      squeeze: bool = False
        Collapse all components into a single scene.
      num_axes: int = None
        Override the number of spatial axes detected in the data.
      num_subplot_row / num_subplot_col: int | None
        Force the subplot (scene) grid shape.
      scatter: bool = False
        Render a 3D scatter plot instead of a volume (3D data only).
      marker_radius: float = 4.0
        Marker radius for scatter mode.
      markerstyle: str = "circle"
        Plotly marker symbol used in scatter mode.
      diverging: bool = False
        Use a diverging colormap centered on zero.
      xscale/xshift, yscale/yshift, zscale/zshift: float
        Per-axis affine rescaling of the coordinates / values.
      cmin: float | None
        Lower limit of the color scale.
      cmax: float | None
        Upper limit of the color scale.
      cscale: float = 1.0
        Multiplicative scaling applied to the color values.
      cshift: float = 0.0
        Additive shift applied to the color values.
      clim: tuple[float, float] | None
        Explicit (min, max) color limits (overrides cmin/cmax).
      style: str | None
        Matplotlib style file used to derive the colormap.
      rcParams: dict | None
        Extra Matplotlib rcParams overrides.
      background: str = "dark"
        Figure background theme: 'dark' or 'light'.
      invert_cmap: bool = False
        Reverse the colormap.
      legend: bool = True
        Show the trace legend.
      label_prefix: str = ""
        Prefix used to build per-component trace labels.
      colorbar: bool = True
        Show the colorbar.
      xlabel/ylabel/zlabel/clabel/title: str | None
        Axis, colorbar, and figure labels.
      logx/logy/logz/logc: bool
        Logarithmic scaling for each axis and the color scale.
      aspect: str | float | None
        Plotly aspect setting: 'auto', 'data', 'cube', or a numeric ratio.
      showgrid: bool = True
        Draw the scene grid.
      hashtag: bool = False
        Add a #pgkyl watermark.
      xkcd: bool = False
        Render in Matplotlib's xkcd sketch style (affects derived styling).
      color: str | None
        Force a single solid color (disables the colorbar).
      opacity: float | None = 1.0
        Trace opacity.
      scatter_opacity_range: tuple[float, float] | None
        Map scatter marker opacity over this (min, max) alpha range.
      scatter_opacity_log: bool = False
        Apply the scatter opacity mapping in log space.
      maximum_points_per_axis: int = 0
        Downsample to at most this many points per axis (0 disables).
      surface_count: int = 32
        Number of isosurfaces for the volume rendering.
      xrange/yrange/zrange: tuple[float, float] | None
        Explicit per-axis display ranges.
      figsize: tuple | None
        Figure size hint (width, height).
      cylindrical_to_cartesian: bool = False
        Convert (R, Z, phi) cylindrical coordinates to Cartesian.
      cmap: str | None
        Matplotlib colormap name to convert into a Plotly colorscale.

    Returns:
      plotly.graph_objects.Figure
        The constructed Plotly figure.
    """
    from postgkyl import output
    opts = {key: value for key, value in locals().items()
        if key not in ("self", "output")}
    return output.plotly(self, **opts)

  def pyvista(self, args: list = (),
      show: bool = True, spin: bool = True, max_points_per_axis: int = -1,
      contour_levels: int = 10,
      is_log: bool = False, is_contour: bool = True, is_shaded: bool = False,
      hide_axes: bool = False,
      mesh_clip_plane: bool = False, mesh_slice_plane: bool = False,
      volume_clip_plane: bool = False,
      cmin: "float | None" = None, cmax: "float | None" = None,
      aspect_ratio=(1, 1, 1),
      camera_azimuth: float = 0.0, camera_elevation: float = -30.0,
      opacity="sigmoid_4", cmap: str = "inferno",
      xlabel: "str | None" = None, ylabel: "str | None" = None,
      zlabel: "str | None" = None,
      clabel: str = "", title: "str | None" = "", diverging: bool = False,
      cylindrical_to_cartesian: bool = False, theme: str = "default",
      saveas: str = "",
      xscale: float = 1.0, yscale: float = 1.0, zscale: float = 1.0,
      xshift: float = 0.0, yshift: float = 0.0, zshift: float = 0.0,
      hide_zeros: bool = False,
      **kwargs):
    """PyVista 3D visualization of this dataset.

    Creates a 3D rendering of the first component of this dataset as a volume,
    set of contours, or clipped/sliced mesh, with various customization
    options.

    See :func:`postgkyl.output.pyvista`.

    Args:
      args: list = ()
        Extra positional arguments forwarded to the renderer.
      show: bool = True
        Open an interactive window when done.
      spin: bool = True
        Auto-rotate the camera until the user interacts.
      max_points_per_axis: int = -1
        Downsample to at most this many points per axis (-1 disables).
      contour_levels: int = 10
        Number of isosurfaces when rendering contours.
      is_log: bool = False
        Use a log10 color scale.
      is_contour: bool = True
        Render isosurfaces instead of a volume.
      is_shaded: bool = False
        Apply shading to the volume rendering.
      hide_axes: bool = False
        Hide the axes and bounding box.
      mesh_clip_plane: bool = False
        Add an interactive clipping plane to the mesh/contours.
      mesh_slice_plane: bool = False
        Add an interactive slicing plane to the mesh/contours.
      volume_clip_plane: bool = False
        Add an interactive clipping plane to the volume.
      cmin: float | None
        Lower color limit.
      cmax: float | None
        Upper color limit.
      aspect_ratio: tuple[float, float, float] = (1, 1, 1)
        Per-axis aspect ratio; (1, 1, 1) is a cube.
      camera_azimuth: float = 0.0
        Initial camera azimuth in degrees.
      camera_elevation: float = -30.0
        Initial camera elevation in degrees.
      opacity: str | float = "sigmoid_4"
        Opacity transfer function name or scalar opacity.
      cmap: str = "inferno"
        Colormap name.
      xlabel/ylabel/zlabel: str | None
        Axis labels.
      clabel: str = ""
        Colorbar label.
      title: str | None = ""
        Figure title.
      diverging: bool = False
        Use the RdBu_r diverging colormap.
      cylindrical_to_cartesian: bool = False
        Convert (R, Z, phi) cylindrical coordinates to Cartesian.
      theme: str = "default"
        PyVista plot theme.
      saveas: str = ""
        Output file path; extension selects the format (.html, .png, .jpg,
        .jpeg, .pdf, .svg, .gltf, .vtksz).
      xscale/yscale/zscale: float
        Per-axis scaling applied to the displayed axis ranges.
      xshift/yshift/zshift: float
        Per-axis shift applied to the displayed axis ranges.
      hide_zeros: bool = False
        Hide grid points where the scalar is exactly zero.
      **kwargs:
        Any remaining options are forwarded to
        :func:`postgkyl.output.pyvista`.

    Returns:
      None
    """
    from postgkyl import output
    opts = {key: value for key, value in locals().items()
        if key not in ("self", "output", "kwargs")}
    opts.update(kwargs)
    return output.pyvista(self, **opts)

  def animate(self, *, interval: int = 100, fixed_range: bool = True,
      notitle: bool = False, show: bool = False, save: bool = False,
      saveas: "str | None" = None, fps: "int | None" = None,
      dpi: "int | None" = None, arg: str = "", **plot_kwargs):
    """Matplotlib animation with this dataset as a single frame.

    Single-dataset entry point mirroring the top-level :func:`postgkyl.animate`
    and the CLI ``animate`` command. For a multi-frame animation group the
    frames first (``a.with_(b).animate()``, ``pg.load.many(...).animate()``, or
    ``DatasetGroup.animate``).

    See :func:`postgkyl.output.animate`.

    Args:
      interval: int
        Delay between frames in milliseconds.
      fixed_range: bool
        Hold the value/colour scale constant across all frames.
      notitle: bool
        Suppress the per-frame title (otherwise the frame number and time from
        the dataset's context are shown).
      show: bool
        Call ``plt.show()`` when done.
      save: bool
        Save the animation to disk (uses ``anim.mp4`` if ``saveas`` is unset).
      saveas: str | None
        Explicit output filename for the saved animation.
      fps: int | None
        Frames per second for the saved animation.
      dpi: int | None
        Resolution in dots per inch for the saved animation.
      arg: str
        Matplotlib format string forwarded to each frame's plot call.
      **plot_kwargs:
        Additional keyword arguments forwarded to :func:`postgkyl.output.plot`
        for each frame.

    Returns:
      matplotlib.animation.FuncAnimation: The constructed animation object (keep
      a reference so it is not garbage-collected).
    """
    from postgkyl import output
    return output.animate([self], interval=interval, fixed_range=fixed_range,
        notitle=notitle, show=show, save=save, saveas=saveas, fps=fps, dpi=dpi,
        arg=arg, **plot_kwargs)

  def plotly_animate(self, **kwargs):
    """Plotly animation with this dataset as a single frame.

    For a multi-frame animation use ``DatasetGroup.plotly_animate``.

    See :func:`postgkyl.output.plotly_animate`.

    Args:
      frame_labels: list[str] | None
        One label per frame; defaults to the frame indices.
      frame_duration: int = 50
        Per-frame display duration in milliseconds.
      transition_duration: int = 0
        Inter-frame transition duration in milliseconds.
      fromcurrent: bool = True
        Start playback from the currently displayed frame.
      redraw: bool = True
        Force a full redraw on each frame (needed for 3D scenes).
      **kwargs:
        Remaining options are forwarded to the per-frame
        :func:`postgkyl.output.plotly` renderer.

    Returns:
      plotly.graph_objects.Figure
        The animated Plotly figure.
    """
    from postgkyl import output
    return output.plotly_animate([self], **kwargs)

  def with_(self, *others) -> "object":
    """Group this dataset with others for joint plotting/processing.

    Returns a :class:`postgkyl.group.DatasetGroup`. Example::

        pg.plot(a.with_(b))   # or simply pg.plot(a, b)
    """
    from postgkyl.group import DatasetGroup
    return DatasetGroup([self, *others])

  # ---- Guardrails for the numeric surface ----
  def _require_operable(self) -> None:
    if self._values is None:
      raise ValueError("GData has no values to operate on.")
    # end
    if not self.is_interpolated:
      raise ValueError(
          "Cannot perform array math on raw DG (modal) data; call .interp() first.")
    # end

  def _check_compatible(self, other: "GData") -> None:
    if self._values is None or other._values is None:
      raise ValueError("Cannot operate on a GData with no values.")
    # end
    if self._values.shape != other._values.shape:
      raise ValueError(
          f"Incompatible shapes for array operation: "
          f"{self._values.shape} vs {other._values.shape}.")
    # end

  # ---- NumPy interoperability ----
  _HANDLED_TYPES = (numbers.Number, np.ndarray, np.generic)

  def __array__(self, dtype=None):
    """Expose the values so ``np.asarray(data)`` and matplotlib accept it."""
    return np.asarray(self._values, dtype=dtype)

  def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
    """Make NumPy ufuncs (``np.sqrt``, ``np.add``, ...) return a GData.

    ``np.sqrt(a**2 + b**2)`` therefore yields a GData carrying ``a``'s grid
    and metadata. Guardrails block raw modal data and shape mismatches.
    """
    if method != "__call__" or "out" in kwargs:
      return NotImplemented
    # end
    self._require_operable()
    raw_inputs = []
    for x in inputs:
      if isinstance(x, GData):
        x._require_operable()
        self._check_compatible(x)
        raw_inputs.append(x._values)
      elif isinstance(x, self._HANDLED_TYPES):
        raw_inputs.append(x)
      else:
        return NotImplemented
      # end
    # end
    result_values = ufunc(*raw_inputs, **kwargs)
    return self._result(self._grid, result_values)

  # ---- Arithmetic dunders (routed through __array_ufunc__) ----
  def __add__(self, other):  return np.add(self, other)
  def __sub__(self, other):  return np.subtract(self, other)
  def __mul__(self, other):  return np.multiply(self, other)
  def __truediv__(self, other):  return np.true_divide(self, other)
  def __pow__(self, other):  return np.power(self, other)

  def __radd__(self, other):  return np.add(other, self)
  def __rsub__(self, other):  return np.subtract(other, self)
  def __rmul__(self, other):  return np.multiply(other, self)
  def __rtruediv__(self, other):  return np.true_divide(other, self)
  def __rpow__(self, other):  return np.power(other, self)

  def __neg__(self):  return np.negative(self)
  def __pos__(self):  return self.copy()
  def __abs__(self):  return np.absolute(self)

  # ---- Representation ----
  def _summary(self) -> str:
    if self._values is None:
      return f"<GData empty | tag '{self.get_tag():s}'>"
    # end
    cells = tuple(int(c) for c in self.get_num_cells())
    parts = [f"<GData {cells}", f"{self.get_num_comps():d} comp"]
    num_dims = self.get_num_dims()
    lo, up = self.get_bounds()
    if lo is not None:
      parts.append(" ".join(f"[{lo[d]:g},{up[d]:g}]" for d in range(num_dims)))
    # end
    if self.ctx.get("basis_type"):
      dg = str(self.ctx["basis_type"])
      if self.ctx.get("poly_order") is not None:
        dg += f" p{self.ctx['poly_order']}"
      # end
      if self.ctx.get("interpolated"):
        dg += " interp"
      elif self.ctx.get("is_modal"):
        dg += " modal"
      # end
      parts.append(dg)
    # end
    parts.append(f"tag '{self.get_tag():s}'")
    return " | ".join(parts) + ">"

  def __repr__(self) -> str:
    return self._summary()

  def __str__(self) -> str:
    header = self._summary()
    if self._values is None:
      return header
    # end
    return f"{header}\n{np.asarray(self._values)}"