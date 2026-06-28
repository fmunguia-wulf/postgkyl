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
import postgkyl.utils.gkeyll_enums as gkenums


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

  def __dict_has_key_from_group__(self, dict_in, group_members_in):
    # Check if a dictionary with key-value pairs, where the key is the name of a group and
    # the value a list of group members (as strings), has a member from a given
    # group.
    #  dict_in: input dictionary.
    #  group_members_in: group members to check for in dict_in.
    dict_keys = dict_in.keys()
    for key in group_members_in:
      if key in dict_keys:
        return True
      #end
    #end
    return False
      

  # ---- Info -----
  def info(self) -> str:
    """Prints GData object information.

    Prints time (only when available), number of components, dimension
    spans, extremes for a GData object.

    Args:
      none

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
    }

    output = ""
    
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
    if self.__dict_has_key_from_group__(self.ctx, info_groups["grid_info"]):
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
      output += f"\n├─ Maximum: {maximum:e} at {str(max_idx[:num_dims]):s}"
      if num_comps > 1:
        output += f" component {max_idx[-1]:d}\n"
      else:
        output += "\n"
      # end
      output += f"├─ Minimum: {minimum:e} at {str(min_idx[:num_dims]):s}"
      if num_comps > 1:
        output += f" component {min_idx[-1]:d}"
      # end
    # end

    if self.__dict_has_key_from_group__(self.ctx, info_groups["basis_info"]):
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

    if self.__dict_has_key_from_group__(self.ctx, info_groups["build_info"]):
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

    if self.__dict_has_key_from_group__(self.ctx, info_groups["geometry_info"]):
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
    """Subselect coordinates/components. See :func:`postgkyl.ops.select`."""
    from postgkyl import ops
    return ops.select(self, comp=comp, z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5,
        inplace=inplace, tag=tag, label=label)

  sel = select

  def interpolate(self, basis: str | None = None, p: int | None = None,
      interp: int | None = None, read: bool | None = None,
      inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
    """Interpolate DG data onto a uniform mesh. See :func:`postgkyl.ops.interpolate`."""
    from postgkyl import ops
    return ops.interpolate(self, basis=basis, p=p, interp=interp, read=read,
        inplace=inplace, tag=tag, label=label)

  interp = interpolate

  def differentiate(self, basis: str | None = None, p: int | None = None,
      interp: int | None = None, read: bool | None = None, direction: int | None = None,
      inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
    """Interpolate a derivative of DG data. See :func:`postgkyl.ops.differentiate`."""
    from postgkyl import ops
    return ops.differentiate(self, basis=basis, p=p, interp=interp, read=read,
        direction=direction, inplace=inplace, tag=tag, label=label)

  diff = differentiate

  def integrate(self, axis=None, *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Integrate over one or more axes. See :func:`postgkyl.ops.integrate`."""
    from postgkyl import ops
    return ops.integrate(self, axis=axis, inplace=inplace, tag=tag, label=label)

  def fft(self, *, psd: bool = False, iso: bool = False, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Fourier transform / PSD. See :func:`postgkyl.ops.fft`."""
    from postgkyl import ops
    return ops.fft(self, psd=psd, iso=iso, inplace=inplace, tag=tag, label=label)

  def magsq(self, *, coords: str = "0:3", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Magnitude squared of selected components. See :func:`postgkyl.ops.magsq`."""
    from postgkyl import ops
    return ops.magsq(self, coords=coords, inplace=inplace, tag=tag, label=label)

  def mask(self, *, filename: str | None = None, lower: float | None = None,
      upper: float | None = None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Mask out values by file or thresholds. See :func:`postgkyl.ops.mask`."""
    from postgkyl import ops
    return ops.mask(self, filename=filename, lower=lower, upper=upper,
        inplace=inplace, tag=tag, label=label)

  def relchange(self, reference: "GData", *, comp=None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Relative change vs. ``reference``. See :func:`postgkyl.ops.relchange`."""
    from postgkyl import ops
    return ops.relchange(self, reference, comp=comp, inplace=inplace, tag=tag, label=label)

  def current(self, *, qbym: bool = False, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Accumulate current from species moments. See :func:`postgkyl.ops.current`."""
    from postgkyl import ops
    return ops.current(self, qbym=qbym, inplace=inplace, tag=tag, label=label)

  def agyro(self, bfield: "GData", *, measure: str = "frobenius", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Agyrotropy from this pressure tensor and ``bfield``. See :func:`postgkyl.ops.agyro`."""
    from postgkyl import ops
    return ops.agyro(self, bfield, measure=measure, inplace=inplace, tag=tag, label=label)

  def energetics(self, ion: "GData", field: "GData", *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Energy decomposition (self=electrons). See :func:`postgkyl.ops.energetics`."""
    from postgkyl import ops
    return ops.energetics(self, ion, field, inplace=inplace, tag=tag, label=label)

  def parrotate(self, rotator: "GData", *, coords: str = "0:3", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Component parallel to ``rotator``. See :func:`postgkyl.ops.parrotate`."""
    from postgkyl import ops
    return ops.parrotate(self, rotator, coords=coords, inplace=inplace, tag=tag, label=label)

  def perprotate(self, rotator: "GData", *, coords: str = "0:3", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Component perpendicular to ``rotator``. See :func:`postgkyl.ops.perprotate`."""
    from postgkyl import ops
    return ops.perprotate(self, rotator, coords=coords, inplace=inplace, tag=tag, label=label)

  def transform_frame(self, bulk: "GData", *, cdim: int, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Shift this distribution to the ``bulk`` frame. See :func:`postgkyl.ops.transform_frame`."""
    from postgkyl import ops
    return ops.transform_frame(self, bulk, cdim=cdim, inplace=inplace, tag=tag, label=label)

  def euler(self, variable: str, *, gas_gamma: float = 5.0 / 3, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Five-moment primitive/derived variable. See :func:`postgkyl.ops.euler`."""
    from postgkyl import ops
    return ops.euler(self, variable, gas_gamma=gas_gamma, inplace=inplace, tag=tag, label=label)

  def tenmoment(self, variable: str, *, gas_gamma: float = 5.0 / 3, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Ten-moment primitive/derived variable. See :func:`postgkyl.ops.tenmoment`."""
    from postgkyl import ops
    return ops.tenmoment(self, variable, gas_gamma=gas_gamma, inplace=inplace, tag=tag, label=label)

  def mhd(self, variable: str, *, gas_gamma: float = 5.0 / 3, mu_0: float = 1.0,
      inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
    """Ideal-MHD primitive/derived variable. See :func:`postgkyl.ops.mhd`."""
    from postgkyl import ops
    return ops.mhd(self, variable, gas_gamma=gas_gamma, mu_0=mu_0, inplace=inplace,
        tag=tag, label=label)

  def velocity(self, momentum: "GData", *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Velocity from this density and ``momentum``. See :func:`postgkyl.ops.velocity`."""
    from postgkyl import ops
    return ops.velocity(self, momentum, inplace=inplace, tag=tag, label=label)

  # Note: no fluent ``grid`` method — ``GData.grid`` is the grid-array property.
  # Use ``pg.ops.grid(data)`` for the grid-as-dataset verb.

  def val2coord(self, *, x: str, y: str, periodic: bool = False,
      tag: str | None = None, label: str | None = None):
    """Build (x, y) datasets from columns. See :func:`postgkyl.ops.val2coord`."""
    from postgkyl import ops
    return ops.val2coord(self, x=x, y=y, periodic=periodic, tag=tag, label=label)

  def extract_input(self) -> str:
    """Decoded embedded input file. See :func:`postgkyl.ops.extract_input`."""
    from postgkyl import ops
    return ops.extract_input(self)

  def laguerre_compose(self, variables, *, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Compose PKPM Laguerre coefficients. See :func:`postgkyl.ops.laguerre_compose`."""
    from postgkyl import ops
    return ops.laguerre_compose(self, variables, inplace=inplace, tag=tag, label=label)

  def fit(self, fit_type: str, *, guess=None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Fit a model and return the fitted curve. See :func:`postgkyl.ops.fit`."""
    from postgkyl import ops
    return ops.fit(self, fit_type, guess=guess, inplace=inplace, tag=tag, label=label)

  def growth(self, *, guess=None, minn: int | None = None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Fit an exponential growth rate. See :func:`postgkyl.ops.growth`."""
    from postgkyl import ops
    return ops.growth(self, guess=guess, minn=minn, inplace=inplace, tag=tag, label=label)

  def plot(self, **kwargs):
    """Plot this dataset. See :func:`postgkyl.output.plot_datasets`."""
    from postgkyl import output
    kwargs.setdefault("show", True)
    return output.plot_datasets([self], **kwargs)

  def plotly(self, *args, **kwargs):
    """Interactive Plotly figure of this dataset. See :func:`postgkyl.output.plotly`."""
    from postgkyl import output
    return output.plotly(self, *args, **kwargs)

  def pyvista(self, *args, **kwargs):
    """PyVista 3D visualization of this dataset. See :func:`postgkyl.output.pyvista`."""
    from postgkyl import output
    return output.pyvista(self, *args, **kwargs)

  def plotly_animate(self, **kwargs):
    """Plotly animation with this dataset as a single frame.

    For a multi-frame animation use ``DatasetGroup.plotly_animate``.
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
    with np.printoptions(threshold=12, edgeitems=2):
      return f"{header}\n{np.asarray(self._values)}"
    # end