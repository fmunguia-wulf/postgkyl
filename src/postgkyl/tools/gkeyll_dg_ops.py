"""Python bindings for gkeyll DG binary operations via ctypes.

Calls gkyl_dg_mul_op and gkyl_dg_inv_op from libg0core.so using opaque
c_void_p handles for gkyl_array and gkyl_basis — no Python struct layout
needed because the gkeyll API takes gkyl_basis by pointer.

Usage:
  ops = GkeyllDGops("/path/to/gkylsoft/gkeyll")
  ops.invert(0, out_gdata, 0, inp_gdata)
  ops.multiply(0, out_gdata, 0, lop_gdata, 0, rop_gdata)
"""

import ctypes
import os

import numpy as np

from postgkyl._gkylsoft_path import resolve_gkylsoft_path

# gkyl_elem_type enum ordinal for double (INT=0, FLOAT=1, DOUBLE=2)
_GKYL_DOUBLE = ctypes.c_int(2)


class GkeyllDGops:
  """Wraps gkyl_dg_mul_op and gkyl_dg_inv_op from libg0core.so.

  Parameters
  ----------
  gkylsoft_path : str or None
    Path to the gkylsoft directory (the one containing lib/libg0core.so).
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
    lib_file = os.path.join(path, "lib", "libg0core.so")
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

    # gkyl_array_new_from_buff(type, ncomp, size, buff) -> gkyl_array*
    lib.gkyl_array_new_from_buff.argtypes = [c_i, c_sz, c_sz, c_vp]
    lib.gkyl_array_new_from_buff.restype  = c_vp

    # gkyl_array_release(arr)
    lib.gkyl_array_release.argtypes = [c_vp]
    lib.gkyl_array_release.restype  = None

    # gkyl_cart_modal_serendip_new(ndim, poly_order) -> gkyl_basis*
    lib.gkyl_cart_modal_serendip_new.argtypes = [c_i, c_i]
    lib.gkyl_cart_modal_serendip_new.restype  = c_vp

    # gkyl_cart_modal_basis_release(basis)
    lib.gkyl_cart_modal_basis_release.argtypes = [c_vp]
    lib.gkyl_cart_modal_basis_release.restype  = None

    # gkyl_dg_mul_op(basis*, c_oop, out*, c_lop, lop*, c_rop, rop*)
    lib.gkyl_dg_mul_op.argtypes = [c_vp, c_i, c_vp, c_i, c_vp, c_i, c_vp]
    lib.gkyl_dg_mul_op.restype  = None

    # gkyl_dg_inv_op(basis*, c_oop, out*, c_iop, iop*)
    lib.gkyl_dg_inv_op.argtypes = [c_vp, c_i, c_vp, c_i, c_vp]
    lib.gkyl_dg_inv_op.restype  = None

  # ---------------------------------------------------------------------------
  # Private helpers
  # ---------------------------------------------------------------------------

  def _gdata_to_array(self, gdata):
    """Wrap a GData's value buffer in a gkyl_array without copying.

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

  def _make_basis(self, gdata):
    """Create a serendipity basis from a GData's metadata. Caller must release."""
    ndim       = ctypes.c_int(gdata.get_num_dims())
    poly_order = ctypes.c_int(int(gdata.ctx["poly_order"]))
    return self._lib.gkyl_cart_modal_serendip_new(ndim, poly_order)

  # ---------------------------------------------------------------------------
  # Public API
  # ---------------------------------------------------------------------------

  def multiply(self,
      c_oop: int, oop,
      c_lop: int, lop,
      c_rop: int, rop) -> None:
    """Weak DG multiply: oop[c_oop] = lop[c_lop] * rop[c_rop].

    Writes the result in-place into oop's underlying value buffer.

    Parameters
    ----------
    c_oop, c_lop, c_rop : int
        Physical component indices (0-based) within each multi-component field.
        Use 0 for single-component (scalar) fields.
    oop, lop, rop : GData
        Output and input operand datasets. oop must already have values
        allocated (e.g. via GData.push with a zero array).
    """
    basis = self._make_basis(lop)
    arr_oop, vals_oop = self._gdata_to_array(oop)
    arr_lop, vals_lop = self._gdata_to_array(lop)
    arr_rop, vals_rop = self._gdata_to_array(rop)
    try:
      self._lib.gkyl_dg_mul_op(
          basis,
          ctypes.c_int(c_oop), arr_oop,
          ctypes.c_int(c_lop), arr_lop,
          ctypes.c_int(c_rop), arr_rop,
      )
    finally:
      self._lib.gkyl_cart_modal_basis_release(basis)
      self._lib.gkyl_array_release(arr_oop)
      self._lib.gkyl_array_release(arr_lop)
      self._lib.gkyl_array_release(arr_rop)

  def invert(self,
      c_oop: int, oop,
      c_iop: int, iop) -> None:
    """Weak DG invert: oop[c_oop] = 1 / iop[c_iop].

    Writes the result in-place into oop's underlying value buffer.
    Only supported for serendipity basis at p=1 (gkeyll limitation).

    Parameters
    ----------
    c_oop, c_iop : int
        Physical component indices (0-based).
    oop, iop : GData
        Output and input datasets. oop must already have values allocated.
    """
    basis  = self._make_basis(iop)
    arr_oop, vals_oop = self._gdata_to_array(oop)
    arr_iop, vals_iop = self._gdata_to_array(iop)
    try:
      self._lib.gkyl_dg_inv_op(
          basis,
          ctypes.c_int(c_oop), arr_oop,
          ctypes.c_int(c_iop), arr_iop,
      )
    finally:
      self._lib.gkyl_cart_modal_basis_release(basis)
      self._lib.gkyl_array_release(arr_oop)
      self._lib.gkyl_array_release(arr_iop)
