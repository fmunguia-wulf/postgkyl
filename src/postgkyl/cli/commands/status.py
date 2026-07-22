"""``status`` -- activate/deactivate datasets in the working set, by index."""

from __future__ import annotations

import click

from .._apply import is_active, parse_indices, set_active


@click.command("status")
@click.option("--activate", "-a", "activate_spec", default=None,
    help="Index spec to activate: '1', '0,2,5', '1:6:2', or ':' for all.")
@click.option("--deactivate", "-d", "deactivate_spec", default=None,
    help="Index spec to deactivate; same forms as --activate.")
@click.pass_context
def command(ctx, activate_spec, deactivate_spec) -> None:
  """Activate/deactivate datasets in the working set (by index).

  Deactivated datasets are skipped by transform commands (fft, magsq, ...)
  and by the terminal commands (info, plot, save). With neither option,
  prints the current active/inactive status of every dataset.
  """
  datasets = ctx.obj.datasets
  if activate_spec is not None:
    for i in parse_indices(activate_spec, len(datasets)):
      set_active(datasets[i], True)
    # end
  # end
  if deactivate_spec is not None:
    for i in parse_indices(deactivate_spec, len(datasets)):
      set_active(datasets[i], False)
    # end
  # end
  if activate_spec is None and deactivate_spec is None:
    for i, d in enumerate(datasets):
      state = "active" if is_active(d) else "inactive"
      click.echo(f"[{i}] {state}  tag={d.tag!r}")
# end
    # end
  # end
