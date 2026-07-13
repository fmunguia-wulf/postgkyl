"""``extractinput`` — print any input file embedded in compatible BP files."""

from __future__ import annotations

import click

from .._apply import active_datasets
from .._options import use_option


@click.command("extractinput")
@use_option
@click.pass_context
def command(ctx, use) -> None:
  """Extract and print the embedded input file from compatible BP files."""
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  for d in pool:
    text = d.extract_input()
    click.echo(text if text else "No embedded input file!")
# end
  # end
