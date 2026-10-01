"""The ``average`` verb -- weighted (or plain) average of a native DG field
over a subset of dimensions, via Gkeyll's ``gkyl_array_average``.

A full average is terminal and returns one physical mean per field. Partial
averaging preserves native modal data over the surviving dimensions.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated
from postgkyl.cli_spec import CliType, DatasetRef

import numpy as np

from postgkyl import dg
from postgkyl.gdatastate.layout import require_kernel_basis
from ._compatibility import require_collocated_layout, uniform_cartesian_grid

from postgkyl.gdatastate.gdatastate import GDataState


def _native_basis(data: "GDataState", what: str):
  if data.backend != "gkyl":
    raise ValueError(
        f"average wraps gkyl_array_average and needs native modal data; "
        f"{what} is not available after .interpolate() or without the "
        "Gkeyll library.")
  if data.ctx.get("value_form", "modal") != "modal":
    raise ValueError(f"average expects the modal value_form, not "
                     f"'{data.ctx['value_form']}' ({what}); "
                     "call .represent(to='modal') first.")
  basis_type = data.ctx.get("basis_type")
  poly_order = data.ctx.get("poly_order")
  if basis_type is None or poly_order is None:
    raise ValueError(f"{what} has no basis_type/poly_order metadata")
  layout = require_kernel_basis(data)
  return layout.basis_type, layout.poly_order


def average(data: "GDataState",
            dims: Annotated[Iterable[int], CliType(list[int])],
            *,
            weight: Annotated[GDataState | None,
                              DatasetRef()] = None,
            inplace: bool = False,
            tag: str | None = None,
            label: str | None = None):
  """``int f w dx^dims / int w dx^dims`` over the directions in ``dims``.

  Args:
    data: gkyl-backed (native modal) dataset in the modal value_form.
    dims: iterable of 0-based direction indices to average over (repeat
      ``--dims`` at the CLI, e.g. ``--dims 0 --dims 1``).
    weight: optional gkyl-backed dataset in the modal value_form, same
      ``num_dims``/``basis_type``/``poly_order`` as ``data`` and exactly one
      field (``gkyl_array_average`` takes no field-index argument) -- the
      plain average (dividing by volume) is computed when omitted.
    inplace: Mutate and return ``data`` for partial averaging only.
    tag: Optional tag for a partial-average dataset.
    label: Optional label for a partial-average dataset.

  Returns:
    A float (one field) or NumPy array (multiple fields) containing the
    physical mean when every direction is averaged out. Otherwise a native
    modal dataset over the surviving dimensions. Dataset-only options
    ``inplace``, ``tag``, and ``label`` apply only to partial averaging.

  Raises:
    ValueError: ``data`` (or ``weight``) is NumPy-backed or non-modal, is
      missing basis metadata, or ``weight``'s grid/basis doesn't match
      ``data``'s, or dataset-only options are used for a full average.
  """
  basis_type, poly_order = _native_basis(data, "data")
  ndim = data.num_dims

  weight_native = None
  if weight is not None:
    w_basis_type, w_poly_order = _native_basis(weight, "weight")
    if weight.num_dims != ndim:
      raise ValueError(
          f"weight has {weight.num_dims} dims but the field has {ndim}")
    if w_basis_type != basis_type:
      raise ValueError(
          f"weight basis_type '{w_basis_type}' != field's '{basis_type}'")
    if w_poly_order != poly_order:
      raise ValueError(
          f"weight poly_order {w_poly_order} != field's {poly_order}")
    require_collocated_layout(data, weight)
    weight_native = weight.native

  grid = uniform_cartesian_grid(data)
  keep_dirs, cells_avg, out_native = dg.modal.average(grid,
                                                      basis_type,
                                                      ndim,
                                                      poly_order,
                                                      data.native,
                                                      dims,
                                                      weight=weight_native)

  if not keep_dirs:
    if inplace or tag is not None or label is not None:
      raise ValueError(
          "inplace, tag, and label apply only to partial averaging, which "
          "returns a dataset")
    # The DG layer returns a constant one-cell 1D modal field, including
    # for weighted averages. Reconstruct its physical mean: phi0=1/sqrt(2).
    coefficients = out_native.view().reshape(-1, poly_order + 1)
    means = coefficients[:, 0] / np.sqrt(2.0)
    return float(means[0]) if means.size == 1 else means

  new_grid = [np.asarray(data.grid[d]) for d in keep_dirs]

  return data._result(new_grid,
                      out_native,
                      inplace=inplace,
                      tag=tag,
                      label=label,
                      cells=np.asarray(cells_avg))
