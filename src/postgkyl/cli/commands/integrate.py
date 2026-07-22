"""``integrate`` -- grid integral, two modes: whole-grid modal, or per-axis."""

from __future__ import annotations

import click

from .._apply import active_datasets, apply
from .._options import label_option, tag_option, use_option


@click.command("integrate")
@click.argument("axis", required=False, default=None)
@click.option("--op", type=click.Choice(["none", "abs", "sq"]), default="none",
    help="Integrand transform for the whole-grid modal integral (axis not given).")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, axis, op, use, tag, label) -> None:
  """Integrate data over the whole grid (modal) or over chosen axes (point-value).

  AXIS (or axes) to integrate over: an index ('1'), a comma list ('0,2'), or
  a colon slice ('0:2'); omit to run every axis. With AXIS given, integrates
  point-value data (already-interpolated, or a native nodal/quad
  value_form materialized to its true point locations) over the given
  axis/axes via NumPy trapezoidal quadrature, producing a new dataset with
  those axes collapsed -- like ``select``. Raw modal DG coefficients raise;
  run ``interpolate`` first (value_form changes to native
  ``nodal``/``quad`` -- ``.to_nodal()``/``.to_quad()`` -- are fluent-API
  only, not exposed as CLI commands).

  A curvilinear (``map --space conf``) axis has no per-axis width of its
  own; requesting only part of such a block raises -- include every axis of
  the block together, and it is reduced via its physical cell volume
  instead of a per-axis trapezoidal width.

  Without AXIS (the default), this is a terminal verb (like ``info``):
  it integrates the *whole* grid natively inside Gkeyll on modal
  (pre-``interpolate()``) data via ``gkyl_array_integrate``, and prints one value
  per field component instead of producing a new dataset. ``--op`` only
  applies to this mode.
  """
  if axis is not None:
    apply(ctx, lambda d: d.integrate_axis(axis, tag=tag, label=label), use=use)
    return
  # end

  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  for i, d in enumerate(pool):
    try:
      result = d.integrate(op=op)
    # end
    except ValueError as err:
      raise click.UsageError(str(err))
    # end
    lbl = d.label or d.tag
    click.echo(f"[{i}] {lbl}: {result}")
# end
  # end
