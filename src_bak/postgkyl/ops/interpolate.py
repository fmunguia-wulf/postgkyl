"""The ``interpolate`` verb — interpolate DG data onto a uniform mesh."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.ops._dg import make_interpolator

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def interpolate(data: "GData", *, basis: str | None = None, p: int | None = None,
    interp: int | None = None, read: bool | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Interpolate DG (modal or nodal) data onto a uniform mesh.

  Converts Discontinuous Galerkin basis coefficients into nodal values on a
  uniform evaluation mesh. The basis/order are taken from ``data.ctx`` when not
  given explicitly. The result is flagged ``interpolated=True`` so it becomes
  safe for element-wise numeric operations.

  Args:
    data: GData
      The DG dataset to interpolate.
    basis: str | None
      Short DG basis code: 'ms' (modal serendipity), 'ns' (nodal
      serendipity), 'mo' (modal maximal-order), 'mt' (modal tensor),
      'gkhyb' (gyrokinetic hybrid), or 'pkpmhyb' (PKPM hybrid). When None the
      'basis_type' stored in ``data.ctx`` is used (and must be present).
    p: int | None
      Polynomial order of the basis. When None the order stored in
      ``data.ctx`` is used.
    interp: int | None
      Number of interpolation points per dimension. When None a default
      derived from the basis/order is used.
    read: bool | None
      When True, read pre-computed interpolation matrices from file instead of
      computing them on the fly. None defers to the interpolator's default.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData on a uniform mesh flagged ``interpolated=True`` (or the mutated
    input when inplace=True).

  Raises:
    ValueError: If no ``basis`` is given and ``data.ctx`` has no stored
      ``basis_type``, or if ``basis`` is not a recognized code.
  """
  dg = make_interpolator(data, basis=basis, p=p, interp=interp, read=read)
  num_comps = int(data.get_num_comps() / dg.num_nodes)
  grid, values = dg.interpolate(tuple(range(num_comps)))
  return data._result(grid, values, inplace=inplace, tag=tag, label=label,
      interpolated=True)
