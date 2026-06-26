"""
Python bindings for Gkeyll DG binary operations via ctypes.

Usage:
  ops = GkeyllDGops("/path/to/gkylsoft/gkeyll")
  ops.invert(0, out_gdata, 0, inp_gdata)
  ops.multiply(0, out_gdata, 0, lop_gdata, 0, rop_gdata)
"""

import ctypes
import os

import numpy as np

from postgkyl._gkylsoft_path import resolve_gkylsoft_path
from postgkyl.data import GData

# gkyl_elem_type enum ordinal for double (INT=0, FLOAT=1, DOUBLE=2)
_GKYL_DOUBLE = ctypes.c_int(2)

class GkeyllDGops:
  """
  Operations on DG data, returning DG data.
  Some of these are implemented in Gkeyll, and we get them from libg0core.so.

  Inputs:
    gkylsoft_path: Path to the gkylsoft directory (the one containing gkeyll/lib/libg0core.so).
                   If None, falls back to the GKYLSOFT env var, ~/.postgkyl/gkylsoft_path,
                   and the build-time default in postgkyl._gkylsoft_path.
  """

  def __init__(self, gkylsoft_path: str | None = None):
    path = resolve_gkylsoft_path(gkylsoft_path)
    if path is None:
      raise RuntimeError("gkylsoft path not configured. Set the GKYLSOFT environment variable, "
                         "write the path to ~/.postgkyl/gkylsoft_path, or pass gkylsoft_path= "
                         "to GkeyllDGops().")
    # end
    lib_file = os.path.join(path, "gkeyll/lib", "libg0core.so")
    if not os.path.isfile(lib_file):
      raise FileNotFoundError(f"libg0core.so not found at {lib_file}. "
                               "Check that the gkylsoft path is correct.")
    # end
    self._lib = ctypes.CDLL(lib_file)
    self._setup_signatures()

  def _setup_signatures(self) -> None:
    lib = self._lib
    c_vp = ctypes.c_void_p
    c_i  = ctypes.c_int
    c_sz = ctypes.c_size_t
    c_d = ctypes.c_double

    # gkyl_array_new_from_buff(type, ncomp, size, buff) -> gkyl_array*
    lib.gkyl_array_new_from_buff.argtypes = [c_i, c_sz, c_sz, c_vp]
    lib.gkyl_array_new_from_buff.restype  = c_vp

    # gkyl_array_release(arr)
    lib.gkyl_array_release.argtypes = [c_vp]
    lib.gkyl_array_release.restype  = None

    # gkyl_cart_modal_serendip_new(ndim, poly_order) -> gkyl_basis*
    lib.gkyl_cart_modal_serendip_new.argtypes = [c_i, c_i]
    lib.gkyl_cart_modal_serendip_new.restype  = c_vp

    # gkyl_cart_modal_gkhybrid_new(cdim, vdim) -> gkyl_basis*
    lib.gkyl_cart_modal_gkhybrid_new.argtypes = [c_i, c_i]
    lib.gkyl_cart_modal_gkhybrid_new.restype  = c_vp

    # gkyl_cart_modal_basis_get_num_basis(basis*) -> int
    lib.gkyl_cart_modal_basis_get_num_basis.argtypes = [c_vp]
    lib.gkyl_cart_modal_basis_get_num_basis.restype  = c_i

    # gkyl_cart_modal_basis_release(basis)
    lib.gkyl_cart_modal_basis_release.argtypes = [c_vp]
    lib.gkyl_cart_modal_basis_release.restype  = None

    # gkyl_rect_grid_new(ndim, lower*, upper*, cells*) -> gkyl_rect_grid*
    lib.gkyl_rect_grid_new.argtypes = [c_i, ctypes.POINTER(c_d),
                                       ctypes.POINTER(c_d), ctypes.POINTER(c_i)]
    lib.gkyl_rect_grid_new.restype  = c_vp

    # gkyl_rect_grid_release(grid)
    lib.gkyl_rect_grid_release.argtypes = [c_vp]
    lib.gkyl_rect_grid_release.restype  = None

    # gkyl_range_new(ndim, lower*, upper*) -> gkyl_range*
    lib.gkyl_range_new.argtypes = [c_i, ctypes.POINTER(c_i), ctypes.POINTER(c_i)]
    lib.gkyl_range_new.restype  = c_vp

    # gkyl_range_release(rng)
    lib.gkyl_range_release.argtypes = [c_vp]
    lib.gkyl_range_release.restype  = None

    # gkyl_dg_mul_op(basis*, c_oop, out*, c_lop, lop*, c_rop, rop*)
    lib.gkyl_dg_mul_op.argtypes = [c_vp, c_i, c_vp, c_i, c_vp, c_i, c_vp]
    lib.gkyl_dg_mul_op.restype  = None

    # gkyl_dg_mul_conf_phase_op_range(cbasis*, pbasis*, pout*, cop*, pop*, crange*, prange*)
    lib.gkyl_dg_mul_conf_phase_op_range.argtypes = [c_vp, c_vp, c_vp, c_vp, c_vp, c_vp, c_vp]
    lib.gkyl_dg_mul_conf_phase_op_range.restype  = None

    # gkyl_dg_inv_op(basis*, c_oop, out*, c_iop, iop*)
    lib.gkyl_dg_inv_op.argtypes = [c_vp, c_i, c_vp, c_i, c_vp]
    lib.gkyl_dg_inv_op.restype  = None

    # gkyl_dg_differentiate_op_local(basis*, dir, diff_order, dx, c_oop, out*, c_iop, inp*)
    lib.gkyl_dg_differentiate_op_local.argtypes = [c_vp, c_i, c_i, c_d, c_i, c_vp, c_i, c_vp]
    lib.gkyl_dg_differentiate_op_local.restype  = None

    # gkyl_dg_eval_at_coord_proj_new(cdim_do, basis_do*, num_eval_dirs, eval_dirs*, use_gpu)
    lib.gkyl_dg_eval_at_coord_proj_new.argtypes = [c_i, c_vp, c_i, ctypes.POINTER(c_i), ctypes.c_bool]
    lib.gkyl_dg_eval_at_coord_proj_new.restype  = c_vp

    # gkyl_dg_eval_at_coord_proj_advance(up*, eval_coords*, grid*, pick_lower*,
    #                                     known_index*, rng_do*, rng_tar*, fdo*, ftar*)
    lib.gkyl_dg_eval_at_coord_proj_advance.argtypes = [
      c_vp, ctypes.POINTER(c_d), c_vp, ctypes.POINTER(ctypes.c_bool),
      ctypes.POINTER(c_i), c_vp, c_vp, c_vp, c_vp,
    ]
    lib.gkyl_dg_eval_at_coord_proj_advance.restype  = None

    # gkyl_dg_eval_at_coord_proj_release(up*)
    lib.gkyl_dg_eval_at_coord_proj_release.argtypes = [c_vp]
    lib.gkyl_dg_eval_at_coord_proj_release.restype  = None

  def _gkyl_array_new_from_gdata(self, gdata):
    """
    Wrap a GData's value buffer in a gkyl_array without copying.

    Returns (arr_ptr, values) where values is the numpy array kept alive
    to prevent GC while arr_ptr is in use.
    """
    values = gdata.get_values()
    # Ensure C-contiguous float64 layout expected by gkyl kernels
    values = np.ascontiguousarray(values, dtype=np.float64)
    size  = ctypes.c_size_t(int(np.prod(values.shape[:-1])))
    ncomp = ctypes.c_size_t(int(values.shape[-1]))
    data_ptr = values.ctypes.data_as(ctypes.c_void_p)
    arr_ptr = self._lib.gkyl_array_new_from_buff(_GKYL_DOUBLE, ncomp, size, data_ptr)
    return arr_ptr, values

  def _gkyl_basis_new_from_gdata(self, gdata):
    """Create a basis from a GData's metadata. Caller must release."""
    ndim       = ctypes.c_int(gdata.get_num_dims())
    poly_order = ctypes.c_int(int(gdata.ctx["poly_order"]))
    basis_type = ctypes.c_int(int(gdata.ctx["basis_type"]))
    if basis_type == "gkhybrid":
      vdim = 1 if ndim == 2 else 2
      cdim = ndim - vdim
      return self._lib.gkyl_cart_modal_gkhybrid_new(cdim, vdim)
    else:
      return self._lib.gkyl_cart_modal_serendip_new(ndim, poly_order)

  def _gkyl_range_new_from_gdata(self, gdata):
    """Create a 1-indexed gkyl_range covering all cells of gdata. Caller must release."""
    values = gdata.get_values()
    cells  = list(values.shape[:-1])
    ndim   = len(cells)
    c_lo   = (ctypes.c_int * ndim)(*([1] * ndim))
    c_up   = (ctypes.c_int * ndim)(*cells)
    return self._lib.gkyl_range_new(ctypes.c_int(ndim), c_lo, c_up)

  def multiply(self, c_oop: int, oop, c_lop: int, lop, c_rop: int, rop) -> None:
    """
    Weak DG multiply: oop[c_oop] = lop[c_lop] * rop[c_rop].

    Inputs:
      c_oop, c_lop, c_rop: Physical component indices (0-based) within each multi-component field.
                           Use 0 for single-component (scalar) fields.
      oop, lop, rop: Output and input operand datasets. Must be pre-allocated.
    """
    basis = self._gkyl_basis_new_from_gdata(lop)
    arr_oop, _ = self._gkyl_array_new_from_gdata(oop)
    arr_lop, _ = self._gkyl_array_new_from_gdata(lop)
    arr_rop, _ = self._gkyl_array_new_from_gdata(rop)
    try:
      self._lib.gkyl_dg_mul_op(basis,
        ctypes.c_int(c_oop), arr_oop,
        ctypes.c_int(c_lop), arr_lop,
        ctypes.c_int(c_rop), arr_rop,)
    finally:
      self._lib.gkyl_cart_modal_basis_release(basis)
      self._lib.gkyl_array_release(arr_oop)
      self._lib.gkyl_array_release(arr_lop)
      self._lib.gkyl_array_release(arr_rop)

  def multiply_conf_phase(self, pout, cop, pop) -> None:
    """
    Weak DG conf-phase multiply: pout = cop * pop on all cells.

    cop is a conf-space field and pop/pout are phase-space fields.
    Ranges are constructed automatically from the shape of each dataset.

    Inputs:
      pout: Output phase-space dataset. Must be pre-allocated.
      cop:  Conf-space operand dataset.
      pop:  Phase-space operand dataset.
    """
    cbasis = self._gkyl_basis_new_from_gdata(cop)
    pbasis = self._gkyl_basis_new_from_gdata(pop)
    arr_pout, _ = self._gkyl_array_new_from_gdata(pout)
    arr_cop,  _ = self._gkyl_array_new_from_gdata(cop)
    arr_pop,  _ = self._gkyl_array_new_from_gdata(pop)
    crange = self._gkyl_range_new_from_gdata(cop)
    prange = self._gkyl_range_new_from_gdata(pop)
    try:
      self._lib.gkyl_dg_mul_conf_phase_op_range(
        cbasis, pbasis, arr_pout, arr_cop, arr_pop, crange, prange)
    finally:
      self._lib.gkyl_cart_modal_basis_release(cbasis)
      self._lib.gkyl_cart_modal_basis_release(pbasis)
      self._lib.gkyl_array_release(arr_pout)
      self._lib.gkyl_array_release(arr_cop)
      self._lib.gkyl_array_release(arr_pop)
      self._lib.gkyl_range_release(crange)
      self._lib.gkyl_range_release(prange)

  def differentiate(self, dir: int, diff_order: int, dx: float, c_oop: int, oop, c_iop: int, iop) -> None:
    """
    Local DG differentiation: oop[c_oop] = d^diff_order/dx_dir^diff_order iop[c_iop].

    Differentiates the DG expansion in each cell independently (no inter-cell stencil).

    Inputs:
      dir:        Direction of differentiation (0-based).
      diff_order: Order of the derivative (1 or 2).
      dx:         Cell length in the direction of differentiation.
      c_oop, c_iop: Physical component indices (0-based).
      oop, iop:   Output and input datasets. oop must be allocated.
    """
    basis = self._gkyl_basis_new_from_gdata(iop)
    arr_oop, _ = self._gkyl_array_new_from_gdata(oop)
    arr_iop, _ = self._gkyl_array_new_from_gdata(iop)
    try:
      self._lib.gkyl_dg_differentiate_op_local(basis,
        ctypes.c_int(dir), ctypes.c_int(diff_order), ctypes.c_double(dx),
        ctypes.c_int(c_oop), arr_oop,
        ctypes.c_int(c_iop), arr_iop,)
    finally:
      self._lib.gkyl_cart_modal_basis_release(basis)
      self._lib.gkyl_array_release(arr_oop)
      self._lib.gkyl_array_release(arr_iop)

  def eval_at_coord_proj(self, eval_dirs: list, eval_coords: list, gdata,
                         comp_grid: bool = False) -> GData:
    """
    Evaluate a DG field at physical coordinates in eval_dirs and project onto
    the lower-dimensional target basis.

    Inputs:
      eval_dirs:   Sorted list of 0-based direction indices to eliminate.
      eval_coords: Physical coordinates, one per entry in eval_dirs.
      gdata:       Donor DG dataset (must have poly_order in ctx).
      comp_grid:   Passed to the output GData constructor.

    Returns:
      GData with the projected field. The surviving grid dimensions, cells,
      lower, upper, and num_comps in ctx are set correctly for the target.
    """
    ndim       = gdata.get_num_dims()
    poly_order = int(gdata.ctx["poly_order"])

    grid_edges = gdata.get_grid()
    cells = [len(grid_edges[d]) - 1 for d in range(ndim)]
    lower = [float(grid_edges[d][0])   for d in range(ndim)]
    upper = [float(grid_edges[d][-1])  for d in range(ndim)]

    num_eval  = len(eval_dirs)
    keep_dirs = [d for d in range(ndim) if d not in eval_dirs]
    ndim_tar  = len(keep_dirs)
    cells_tar = [cells[d] for d in keep_dirs] if num_eval<ndim else [1 for d in range(ndim)]

    # donor grid (opaque)
    c_lower  = (ctypes.c_double * ndim)(*lower)
    c_upper  = (ctypes.c_double * ndim)(*upper)
    c_cells  = (ctypes.c_int   * ndim)(*cells)
    grid_ptr = self._lib.gkyl_rect_grid_new(ctypes.c_int(ndim), c_lower, c_upper, c_cells)

    # donor range: 1-indexed lower=[1,...], upper=[cells[d],...]
    c_rng_lo_do = (ctypes.c_int * ndim)(*([1] * ndim))
    c_rng_up_do = (ctypes.c_int * ndim)(*cells)
    rng_do_ptr  = self._lib.gkyl_range_new(ctypes.c_int(ndim), c_rng_lo_do, c_rng_up_do)

    # donor basis
    basis_do_ptr = self._lib.gkyl_cart_modal_serendip_new(ctypes.c_int(ndim), ctypes.c_int(poly_order))
    num_basis_do = int(self._lib.gkyl_cart_modal_basis_get_num_basis(basis_do_ptr))

    # target basis and range
    if ndim_tar > 0:
      basis_tar_ptr = self._lib.gkyl_cart_modal_serendip_new(ctypes.c_int(ndim_tar), ctypes.c_int(poly_order))
      num_basis_tar = int(self._lib.gkyl_cart_modal_basis_get_num_basis(basis_tar_ptr))
      c_rng_lo_tar  = (ctypes.c_int * ndim_tar)(*([1] * ndim_tar))
      c_rng_up_tar  = (ctypes.c_int * ndim_tar)(*cells_tar)
      rng_tar_ptr   = self._lib.gkyl_range_new(ctypes.c_int(ndim_tar), c_rng_lo_tar, c_rng_up_tar)
      tar_grid      = [grid_edges[d] for d in keep_dirs]
    else:
      # all dims evaluated: basis_tar = NULL per C API; use a 1D range of shape (1,)
      basis_tar_ptr = ctypes.c_void_p(None)
      num_basis_tar = 1
      c_one       = (ctypes.c_int * 1)(1)
      rng_tar_ptr = self._lib.gkyl_range_new(ctypes.c_int(1), c_one, c_one)
      tar_grid      = [np.array([eval_coords[d]]) for d in range(num_eval)]

    # donor array
    arr_do, values = self._gkyl_array_new_from_gdata(gdata)
    ncomp_raw = int(values.shape[-1])

    # target buffer
    num_phys_comps = ncomp_raw // num_basis_do
    ncomp_tar      = num_phys_comps * num_basis_tar
    size_tar       = int(np.prod(cells_tar)) if cells_tar else 1
    tar_shape      = (*cells_tar, ncomp_tar) if cells_tar else (ncomp_tar,)
    tar_buf        = np.zeros(tar_shape, dtype=np.float64)
    arr_tar        = self._lib.gkyl_array_new_from_buff(
      _GKYL_DOUBLE, ctypes.c_size_t(ncomp_tar), ctypes.c_size_t(size_tar),
      tar_buf.ctypes.data_as(ctypes.c_void_p),
    )

    # updater
    c_eval_dirs   = (ctypes.c_int  * num_eval)(*eval_dirs)
    updater       = self._lib.gkyl_dg_eval_at_coord_proj_new(
      ctypes.c_int(ndim), basis_do_ptr, ctypes.c_int(num_eval), c_eval_dirs, ctypes.c_bool(False),
    )
    c_eval_coords = (ctypes.c_double * num_eval)(*eval_coords)
    c_pick_lower  = (ctypes.c_bool   * num_eval)(*([False] * num_eval))
    c_known_idx   = (ctypes.c_int    * ndim)(*([-1] * ndim))
    try:
      self._lib.gkyl_dg_eval_at_coord_proj_advance(
        updater, c_eval_coords, grid_ptr, c_pick_lower, c_known_idx,
        rng_do_ptr, rng_tar_ptr, arr_do, arr_tar,
      )
    finally:
      self._lib.gkyl_dg_eval_at_coord_proj_release(updater)
      self._lib.gkyl_cart_modal_basis_release(basis_do_ptr)
      if ndim_tar > 0:
        self._lib.gkyl_cart_modal_basis_release(basis_tar_ptr)
      self._lib.gkyl_array_release(arr_do)
      self._lib.gkyl_array_release(arr_tar)
      self._lib.gkyl_rect_grid_release(grid_ptr)
      self._lib.gkyl_range_release(rng_do_ptr)
      self._lib.gkyl_range_release(rng_tar_ptr)

    out = GData(ctx=gdata.ctx, comp_grid=comp_grid)
    out.push(tar_grid, tar_buf)

    return out

  def invert(self, c_oop: int, oop, c_iop: int, iop) -> None:
    """
    Weak DG invert: oop[c_oop] = 1 / iop[c_iop].

    Only supported for serendipity basis at p=1 (gkeyll limitation).

    Inputs:
      c_oop, c_iop: Physical component indices (0-based).
      oop, iop: Output and input datasets. oop be allocated.
    """
    basis  = self._gkyl_basis_new_from_gdata(iop)
    arr_oop, _ = self._gkyl_array_new_from_gdata(oop)
    arr_iop, _ = self._gkyl_array_new_from_gdata(iop)
    try:
      self._lib.gkyl_dg_inv_op(basis,
        ctypes.c_int(c_oop), arr_oop,
        ctypes.c_int(c_iop), arr_iop,)
    finally:
      self._lib.gkyl_cart_modal_basis_release(basis)
      self._lib.gkyl_array_release(arr_oop)
      self._lib.gkyl_array_release(arr_iop)

