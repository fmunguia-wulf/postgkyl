"""The representation verbs — explicit modal · nodal · quad changes + ``apply``.

Conversions are **never implicit** (REFACTOR_GKEYLL_FFI.md §3b): these verbs are
the only way a dataset changes representation, and each one stamps
``ctx["representation"]`` (and ``ctx["num_quad"]`` for quad data) so ``info``
always shows what the numbers mean. All of them keep the data gkyl-native.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import dg

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end

REPRESENTATIONS = ("modal", "nodal", "quad")


def _native_basis(data: "GDataState"):
  """(basis_type, ndim, poly_order) for a gkyl-backed dataset, or raise."""
  if data.backend != "gkyl":
    raise ValueError(
        "representation changes act on native (gkyl-backed) DG data; "
        "this dataset is NumPy-backed (already interpolated, or loaded "
        "without the Gkeyll library).")
  basis_type = data.ctx.get("basis_type")
  poly_order = data.ctx.get("poly_order")
  if basis_type is None or poly_order is None:
    raise ValueError("dataset has no basis_type/poly_order metadata")
  return str(basis_type), data.num_dims, int(poly_order)


def represent(data: "GDataState", *, to: str, num_quad: int | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """Convert a native dataset to the ``to`` representation (explicitly).

  ``modal`` <-> ``nodal`` is exact; ``modal`` -> ``quad`` evaluates at
  ``num_quad`` (default ``p+1``) Gauss–Legendre points per dimension;
  ``quad`` -> ``modal`` projects back with the rule the data was made with.
  ``nodal`` <-> ``quad`` composes through modal.
  """
  if to not in REPRESENTATIONS:
    raise ValueError(f"unknown representation '{to}'; "
                     f"choices: {REPRESENTATIONS}")
  basis_type, ndim, poly_order = _native_basis(data)
  cur = data.ctx.get("representation", "modal")
  arr = data.native

  if cur != to:
    if cur == "nodal":  # leave nodal (exact)
      arr = dg.rep.nodal_to_modal(basis_type, ndim, poly_order, arr)
    elif cur == "quad":  # leave quad (projection, with the data's own rule)
      nq = data.ctx.get("num_quad")
      if nq is None:
        raise ValueError("quad-represented dataset lost its 'num_quad' ctx")
      arr = dg.rep.quad_to_modal(basis_type, ndim, poly_order, arr, int(nq))
    # arr is now modal
    if to == "nodal":
      arr = dg.rep.modal_to_nodal(basis_type, ndim, poly_order, arr)
    elif to == "quad":
      nq = int(num_quad) if num_quad else poly_order + 1
      arr = dg.rep.modal_to_quad(basis_type, ndim, poly_order, arr, nq)
  else:
    arr = arr.clone()
  # end

  return data._result(data.grid, arr, inplace=inplace, tag=tag, label=label,
      representation=to,
      num_quad=(int(num_quad) if num_quad else poly_order + 1)
               if to == "quad" else None)


def apply(data: "GDataState", fn, *, num_quad: int | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """Apply ``fn`` pointwise via quadrature: modal -> quad -> fn -> modal.

  The explicit spelling of nonlinear pointwise operations on DG data (e.g.
  ``d.apply(np.sqrt)``): evaluate at ``num_quad`` (default ``p+1``) Gauss
  points, apply ``fn`` to the values, project back onto the basis. The result
  stays modal and gkyl-native; the projection is exact when ``fn(f)·b_j`` has
  degree ≤ 2·num_quad−1 — raise ``num_quad`` to de-alias.
  """
  basis_type, ndim, poly_order = _native_basis(data)
  if data.ctx.get("representation", "modal") != "modal":
    raise ValueError("apply() expects modal data; call .to_modal() first.")
  nq = int(num_quad) if num_quad else poly_order + 1
  out = dg.rep.apply_pointwise(basis_type, ndim, poly_order, data.native,
      fn, nq)
  return data._result(data.grid, out, inplace=inplace, tag=tag, label=label,
      applied=getattr(fn, "__name__", str(fn)), applied_num_quad=nq)
