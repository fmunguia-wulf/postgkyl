"""The ``differentiate`` verb — numerical gradient of field-domain data.

Per ``.claude/migration/notes/differentiate-decision.md`` (layer 03): an
*exact* modal derivative would need a ``pg0_basis_eval_grad`` addition to the
compiled shim (``gkeyll/core/zero/gkyl_pg0.h``/``pg0.c`` +
``ffi/csrc/_g0pymodule.c``), out of scope for every layer above ``ffi``. This
verb instead differentiates *after* ``.interp()``, with ``np.gradient`` on the
plain NumPy field values (via ``numerics.ev_ops.grad``/``grad2``, the
existing pure ``(grid, values)`` gradient operators shared with the ``ev``
verb) -- a numerical (second-order accurate, cell-centered), not exact,
derivative. Exactness on the modal polynomial is unnecessary here precisely
because the data have already been interpolated to a uniform mesh.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.numerics import ev_ops

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def differentiate(data: "GDataState", *, direction: int | None = None,
    inplace: bool = False, tag: str | None = None, label: str | None = None):
  """Numerical gradient of field-domain data.

  With ``direction=None``, differentiates along every spatial axis and
  stacks the results in the component axis (``num_comps`` becomes
  ``num_comps * num_dims``, grouped ``[d0_comp0..d0_compN, d1_comp0.., ...]``).
  With an explicit ``direction``, differentiates along that one axis only
  (``num_comps`` unchanged). Requires a nodal (edge) grid one entry longer
  than the value count along each differentiated axis (the same convention
  ``numerics.ev_ops`` uses elsewhere); a mismatched axis silently returns a
  wrong result -- a caveat inherited unchanged from the legacy tool.

  Args:
    data: the dataset to differentiate; must be NumPy-backed (call
      ``.interp()`` first on native modal data).
    direction: 0-based axis to differentiate along; None differentiates
      along every axis.
    inplace: mutate and return ``data`` instead of a new dataset.
    tag: optional tag for the returned dataset.
    label: optional label for the returned dataset.

  Returns:
    A dataset of the gradient, on ``data``'s (unchanged) grid.

  Raises:
    ValueError: if ``data`` is native modal (gkyl-backed).
  """
  if data.backend == "gkyl":
    raise ValueError(
        "differentiate operates on interpolated (NumPy) values; call "
        ".interp() first -- np.gradient has no basis-space meaning for raw "
        "DG coefficients.")
  # end
  grid = data.grid
  values = data.values
  if direction is None:
    out_grid, out_values = ev_ops.grad([grid], [values])
  else:
    out_grid, out_values = ev_ops.grad2([None, grid], [int(direction), values])
  # end
  return data._result(out_grid[0], out_values[0], inplace=inplace, tag=tag,
      label=label)
