"""``GDataState`` — the verb-less data container (the CONTAINER layer).

Holds a Gkeyll dataset: a nodal ``grid`` (list of 1-D edge arrays) plus values
in one of **two backends** — the two-domain lifecycle of REFACTOR_GKEYLL_FFI.md:

- ``backend == "gkyl"``: modal DG coefficients held as a native
  :class:`~postgkyl.gpython.array.GkylArray`. Gkeyll owns the memory and all math
  on it (weak ops, coefficient lin-combs, integrate). ``values`` exposes a
  read-only NumPy *view* for inspection; ``__array__`` refuses (interpolate first).
- ``backend == "numpy"``: post-``interpolate`` (or never-modal) values as a plain
  ``np.ndarray`` — the field domain, where all NumPy math applies.

It constructs itself by delegating to the :mod:`postgkyl.io` leaf and exposes
only *state*. Crucially it imports **nothing upward** (no ``operations``/``render``/
``api``). The fluent verb methods and the computing operators live on the
:class:`postgkyl.gdata.gdata.GData` subclass, one layer up. That is what keeps
the dependency graph a strict, cycle-free DAG — see HIERARCHY_2.md / HIERARCHY_3.md.
"""

from __future__ import annotations

import numbers
from typing import Tuple

import numpy as np

from postgkyl import io   # leaf layer (below); top-level import — never a cycle
from postgkyl import gpython  # foreign floor (below): GkylArray backend type


class GDataState:
  """Storage + metadata for one dataset. No verbs; no upward imports."""

  def __init__(self, file_name: str = "", *, ctx: dict | None = None,
      tag: str = "default", label: str = "", representation: str | None = None,
      **read_kwargs):
    self._grid: list | None = None
    self._values: np.ndarray | gpython.GkylArray | None = None
    self.ctx: dict = {}
    if ctx:
      self.ctx.update(ctx)
    # end
    self._tag = tag
    self._label = ""
    self._custom_label = label
    self._file_name = str(file_name)
    self.color = None

    if self._file_name:
      self._grid, self._values = io.read(self._file_name, self.ctx,
          representation=representation, **read_kwargs)
  # end
    # end

  # ------------------------------------------------------------------ tags
  def get_tag(self) -> str:
    return self._tag
  # end

  def set_tag(self, tag: str = "") -> None:
    if tag:
      self._tag = tag
  # end
    # end

  tag = property(get_tag, set_tag)

  def get_label(self) -> str:
    return self._custom_label or self._label
  # end

  def set_label(self, label: str) -> None:
    self._label = label
  # end

  label = property(get_label, set_label)

  # ------------------------------------------------------------- shape info
  def get_num_cells(self) -> np.ndarray:
    if self.ctx.get("cells") is not None:
      return np.asarray(self.ctx["cells"])
    # end
    if isinstance(self._values, np.ndarray):
      return np.array(self._values.shape[:-1], dtype=np.int64)
    # end
    return np.array([], dtype=np.int64)
  # end

  num_cells = property(get_num_cells)

  def get_num_comps(self) -> int:
    if self.ctx.get("num_comps"):
      return int(self.ctx["num_comps"])
    # end
    if isinstance(self._values, gpython.GkylArray):
      return self._values.ncomp
    # end
    if self._values is not None:
      return int(self._values.shape[-1])
    # end
    return 0
  # end

  num_comps = property(get_num_comps)

  def get_num_dims(self) -> int:
    if self.ctx.get("cells") is not None:
      return len(self.ctx["cells"])
    # end
    if isinstance(self._values, np.ndarray):
      return int(self._values.ndim - 1)
    # end
    return 0
  # end

  num_dims = property(get_num_dims)

  def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
    if "lower" in self.ctx and "upper" in self.ctx:
      return np.asarray(self.ctx["lower"]), np.asarray(self.ctx["upper"])
    # end
    if self._grid is not None:
      num_dims = self.get_num_dims()
      lo = np.array([self._grid[d].min() for d in range(num_dims)])
      up = np.array([self._grid[d].max() for d in range(num_dims)])
      return lo, up
    # end
    return None, None
  # end

  bounds = property(get_bounds)

  def get_grid_type(self) -> str:
    return self.ctx.get("grid_type", "uniform")
  # end

  # --------------------------------------------------------- grid / values
  def get_grid(self) -> list:
    return self._grid
  # end

  def set_grid(self, grid: list) -> None:
    self._grid = grid
    # ``len(grid)`` (not ``get_num_dims()``) on purpose: for a gkyl-backed
    # dataset, num_dims reads ctx["cells"], which a dimension-reducing verb
    # (e.g. ``average``) updates via ``_result``'s ctx_updates -- AFTER
    # ``push`` calls this method. Deriving straight from the just-given grid
    # avoids depending on that update having landed yet.
    num_dims = len(grid)
    self.ctx["lower"] = np.array([grid[d].min() for d in range(num_dims)])
    self.ctx["upper"] = np.array([grid[d].max() for d in range(num_dims)])
  # end

  grid = property(get_grid, set_grid)

  @property
  def backend(self) -> str:
    """``"gkyl"`` (native modal storage) or ``"numpy"`` (field domain)."""
    return "gkyl" if isinstance(self._values, gpython.GkylArray) else "numpy"
  # end

  @property
  def native(self) -> gpython.GkylArray | None:
    """The native ``GkylArray`` when gkyl-backed; None otherwise. This is the
    handle the modal verbs pass to the Gkeyll kernels."""
    return self._values if isinstance(self._values, gpython.GkylArray) else None
  # end

  def get_values(self) -> np.ndarray:
    """Values for *reading*: gkyl-backed data yields a read-only NumPy view of
    the C buffer (valid while this dataset is alive); numpy-backed data yields
    the array itself. Mutation of modal data must go through the kernels."""
    if isinstance(self._values, gpython.GkylArray):
      return self._values.view(self.ctx.get("cells"))
    # end
    return self._values
  # end

  def set_values(self, values) -> None:
    self._values = values
    if isinstance(values, gpython.GkylArray):
      # Cell layout is not derivable from the flat native array; it comes from
      # ctx (set by the reader, and carried through copy(data=False)).
      self.ctx["num_comps"] = values.ncomp
    # end
    else:
      self.ctx["cells"] = np.array(values.shape[:-1], dtype=np.int64)
      self.ctx["num_comps"] = int(values.shape[-1])
    # end
  # end

  values = property(get_values, set_values)

  def __getitem__(self, comp):
    if self._values is None:
      raise ValueError("GData values are not loaded; cannot subscript.")
    # end
    return self.get_values()[..., comp]
  # end

  def push(self, grid, values):
    """Set values (updating cell/comp ctx) then the grid (updating bounds)."""
    self.set_values(values)
    self.set_grid(grid)
    return self
  # end

  # ------------------------------------------------------------- duplication
  def clone(self, data: bool = True) -> "GDataState":
    """Deep-copy without re-reading. Builds ``type(self)`` so subclasses
    (e.g. the fluent ``GData``) propagate through every verb result."""
    new = type(self)(tag=self._tag, label=self._custom_label, ctx=self.ctx)
    new.set_label(self._label)
    new._file_name = self._file_name
    new.color = self.color
    if data and self._values is not None:
      dup = (self._values.clone() if isinstance(self._values, gpython.GkylArray)
             else np.array(self._values, copy=True))
      new.push([np.array(g, copy=True) for g in self._grid], dup)
    # end
    return new
  # end

  def _result(self, grid, values, *, inplace: bool = False,
      tag: str | None = None, label: str | None = None, **ctx_updates):
    """The single 'mutate self vs. emit a new dataset' decision point.

    Every verb funnels its computed ``(grid, values)`` through here. Because
    ``copy`` uses ``type(self)``, the result is the *same* (sub)class as the
    input — so ``operations`` can be typed on ``GDataState`` yet return a fluent
    ``GData`` at runtime.
    """
    target = self if inplace else self.clone(data=False)
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
  # end

  # ---------------------------------------------------------- operability
  @property
  def is_interpolated(self) -> bool:
    """True when values are safe for element-wise math: never-modal data, or
    modal data already run through ``interpolate`` (``ctx['interpolated']``)."""
    return (not self.ctx.get("is_modal", False)) or self.ctx.get("interpolated", False)
  # end

  def _require_operable(self) -> None:
    """Pointwise math is allowed exactly where the data are point values:
    the NumPy field domain, or the nodal/quad representations. Modal
    coefficients refuse — a pointwise operation has no basis-space meaning."""
    if self._values is None:
      raise ValueError("GData has no values to operate on.")
    # end
    if self.backend == "gkyl" and self.ctx.get("representation",
        "modal") != "modal":
      return  # nodal/quad: the values ARE the field at points
    # end
    if not self.is_interpolated:
      raise ValueError(
          "Cannot do NumPy math on modal DG coefficients. Convert explicitly: "
          ".to_nodal()/.to_quad() (pointwise, stays native), .apply(fn) "
          "(pointwise via quadrature, projects back to modal), or .interpolate() "
          "(leave for the NumPy field domain).")
    # end
  # end

  # ----------------------------------------------------- numpy interop (read)
  _HANDLED_TYPES = (numbers.Number, np.ndarray, np.generic)

  def __array__(self, dtype=None):
    """Expose values so ``np.asarray(data)`` / matplotlib accept the dataset.

    This is a pure *reader* (no ``operations``), so it lives on the container; the
    computing operators (``__add__``, ``__array_ufunc__``) live on the fluent
    subclass — see HIERARCHY_3.md. Nodal/quad data expose their point values;
    native *modal* data refuses: silently handing out DG coefficients as if
    they were point values is a correctness trap."""
    if isinstance(self._values, gpython.GkylArray):
      if self.ctx.get("representation", "modal") != "modal":
        return np.asarray(self.get_values(), dtype=dtype)
      # end
      raise ValueError(
          "This dataset holds modal DG coefficients in native Gkeyll storage; "
          ".to_nodal()/.to_quad() for point values, or .interpolate() for NumPy.")
    # end
    return np.asarray(self._values, dtype=dtype)
  # end

  # -------------------------------------------------------------- reporting
  def info(self, index: int = 0, header: bool = True) -> str:
    """Build (and print) a human-readable summary of the dataset."""
    values, num_comps = self.get_values(), self.num_comps
    num_dims, num_cells = self.num_dims, self.num_cells
    lo, up = self.bounds
    out = ""
    if header:
      lbl = self.get_label()
      out += f"{lbl}{' ' if lbl else ''}({self.get_tag()}#{index})\n"
    # end
    if "time" in self.ctx:
      out += f"├─ Time: {self.ctx['time']:e}\n"
    # end
    if "frame" in self.ctx:
      out += f"├─ Frame: {self.ctx['frame']:d}\n"
    # end
    out += f"├─ Number of components: {num_comps:d}\n"
    out += f"├─ Number of dimensions: {num_dims:d}\n"
    if lo is not None:
      out += f"├─ Grid: ({self.get_grid_type()})\n"
      for d in range(num_dims):
        branch = "└" if d == num_dims - 1 else "├"
        out += (f"│  {branch}─ Dim {d}: Num. cells: {int(num_cells[d]):d}; "
                f"Lower: {lo[d]:e}; Upper: {up[d]:e}\n")
    # end
      # end
    if values is not None:
      vmax = np.nanmax(values)
      vmin = np.nanmin(values)
      max_pos = tuple(int(i) for i in np.unravel_index(np.nanargmax(values), values.shape)[:num_dims])
      min_pos = tuple(int(i) for i in np.unravel_index(np.nanargmin(values), values.shape)[:num_dims])
      out += f"├─ Maximum: {vmax:e} at {max_pos}\n"
      out += f"├─ Minimum: {vmin:e} at {min_pos}\n"
    # end
    if self.ctx.get("basis_type"):
      modal = "modal" if self.ctx.get("is_modal") else "nodal"
      if self.ctx.get("interpolated"):
        modal = "interpolated"
      # end
      elif self.backend == "gkyl":
        rep = self.ctx.get("representation", "modal")
        if rep != "modal":
          modal = f"{rep} representation"
          if rep == "quad" and self.ctx.get("num_quad"):
            modal += f", num_quad={self.ctx['num_quad']}"
          # end
        # end
      # end
      out += f"├─ DG: {self.ctx['basis_type']} p{self.ctx.get('poly_order', '?')} ({modal})\n"
    # end
    print(out)
    return out
  # end

  # --------------------------------------------------------------- summary
  def _summary(self) -> str:
    if self._values is None:
      return f"<{type(self).__name__} empty | tag '{self._tag}'>"
    # end
    cells = tuple(int(c) for c in self.get_num_cells())
    parts = [f"<{type(self).__name__} {cells}", f"{self.num_comps:d} comp"]
    lo, up = self.bounds
    if lo is not None:
      parts.append(" ".join(f"[{lo[d]:g},{up[d]:g}]" for d in range(self.num_dims)))
    # end
    if self.ctx.get("basis_type"):
      dg = str(self.ctx["basis_type"])
      if self.ctx.get("poly_order") is not None:
        dg += f" p{self.ctx['poly_order']}"
      # end
      if self.ctx.get("interpolated"):
        dg += " interpolate"
      # end
      elif self.ctx.get("is_modal"):
        dg += " modal"
      # end
      parts.append(dg)
    # end
    if self.backend == "gkyl":
      rep = self.ctx.get("representation", "modal")
      parts.append("gkyl-native" if rep == "modal" else f"gkyl-native ({rep})")
    # end
    parts.append(f"tag '{self._tag}'")
    return " | ".join(parts) + ">"
  # end

  def __repr__(self) -> str:
    return self._summary()
  # end

  def __str__(self) -> str:
    if self._values is None:
      return self._summary()
    # end
    return (f"{self._summary()}\n"
            f"{np.array2string(self.get_values(), threshold=20, edgeitems=2)}")
  # end
# end
