"""``listoutputs`` -- list Gkeyll filename stems found in a directory."""

from __future__ import annotations

import click

import postgkyl as pg


@click.command("listoutputs")
@click.option("--extensions", "-e", default="bp,gkyl",
    help="Comma-separated output file extension(s).")
@click.option("--path", "-p", default=".", help="Directory to search for outputs.")
@click.pass_context
def command(ctx, extensions, path) -> None:
  """List the Gkeyll filename stems (per extension) found in a directory."""
  stems_by_ext = pg.diagnostics.discovery.find_output_stems(extensions, path)
  for ext, stems in stems_by_ext.items():
    if stems:
      click.echo(f"{ext}:")
    # end
    for stem in stems:
      click.echo(f"- {stem}")
# end
    # end
  # end
