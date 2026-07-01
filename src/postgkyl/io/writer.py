"""Write a dataset back to disk.

A leaf module: it consumes the read-only *surface* of a dataset (the same
properties the readers fill) and never imports ``core``/``ops``. Supports the
Gkeyll binary ``.gkyl`` format (round-trips with :class:`GkylReader`), plain
ASCII ``.txt``, and NumPy ``.npy``.
"""

from __future__ import annotations

from typing import Literal

import numpy as np


def write(data, out_name: str = "",
    extension: Literal["gkyl", "txt", "npy"] = "gkyl",
    var_name: str = "CartGridField") -> str:
  """Write ``data`` to ``out_name`` in the requested ``extension``.

  Args:
    data: a dataset exposing ``num_dims``/``num_comps``/``num_cells``/
      ``bounds``/``values``/``grid`` (a ``GDataState`` or subclass).
    out_name: output path; when empty a name is derived from the source file.
    extension: one of ``"gkyl"`` (default), ``"txt"``, ``"npy"``.
    var_name: unused placeholder kept for interface symmetry.

  Returns:
    The path actually written.
  """
  if not out_name:
    src = getattr(data, "_file_name", "") or ""
    stem = src.split(".", maxsplit=1)[0].strip("_") if src else "gdata"
    out_name = f"{stem}_mod.{extension}"
  elif out_name.split(".")[-1] != extension:
    out_name += "." + extension
  # end

  num_dims = data.num_dims
  num_comps = data.num_comps
  num_cells = data.num_cells
  lo, up = data.bounds
  values = data.values

  if extension == "gkyl":
    _write_gkyl(out_name, num_dims, num_comps, num_cells, lo, up, values)
  elif extension == "npy":
    np.save(out_name, np.asarray(values).squeeze())
  elif extension == "txt":
    _write_txt(out_name, data, num_dims, num_comps, num_cells, values)
  else:
    raise ValueError(f"Unsupported write extension '{extension}'")
  # end
  return out_name


def _write_gkyl(out_name, num_dims, num_comps, num_cells, lo, up, values) -> None:
  dti = np.dtype("i8")
  dtf = np.dtype("f8")
  with open(out_name, "w", encoding="utf-8") as fh:
    np.array([103, 107, 121, 108, 48], dtype=np.dtype("b")).tofile(fh, sep="")  # 'gkyl0'
    np.array([1], dtype=dti).tofile(fh, sep="")              # version 1
    np.array([1], dtype=dti).tofile(fh, sep="")              # file type 1 (field)
    np.array([0], dtype=dti).tofile(fh, sep="")              # meta size
    np.array([2], dtype=dti).tofile(fh, sep="")              # real type (f8)
    np.array([num_dims], dtype=dti).tofile(fh, sep="")
    np.array(num_cells, dtype=dti).tofile(fh, sep="")
    np.array(lo, dtype=dtf).tofile(fh, sep="")
    np.array(up, dtype=dtf).tofile(fh, sep="")
    np.array([num_comps * 8], dtype=dti).tofile(fh, sep="")  # elem_sz
    np.array([np.size(values)], dtype=dti).tofile(fh, sep="")  # asize
    np.array(values, dtype=dtf).tofile(fh, sep="")


def _write_txt(out_name, data, num_dims, num_comps, num_cells, values) -> None:
  grid = [0.5 * (g[1:] + g[:-1]) for g in data.grid]  # cell centers
  num_rows = int(np.prod(num_cells))
  basis = np.full(num_dims, 1.0)
  for d in range(num_dims - 1):
    basis[d] = np.prod(num_cells[(d + 1):])
  # end
  with open(out_name, "w", encoding="utf-8") as fh:
    for i in range(num_rows):
      idx = i
      idxs = np.zeros(num_dims, np.int32)
      for d in range(num_dims):
        idxs[d] = int(idx // basis[d])
        idx = idx % basis[d]
      # end
      cells = [f"{grid[d][idxs[d]]:.15e}" for d in range(num_dims)]
      comps = [f"{values[tuple(idxs)][c]:.15e}" for c in range(num_comps)]
      fh.write(", ".join(cells + comps) + "\n")
    # end
