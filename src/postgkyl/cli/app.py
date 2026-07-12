"""``pgkyl`` command-line entry point — a chained pipeline on pure Click.

The chained syntax mirrors the fluent script API 1:1::

    pg.load('f.gkyl').interpolate().sel(z0=0).plot()      # script
    pgkyl   f.gkyl    interp   sel --z0 0  plot        # CLI

Chaining and callback-before-dispatch are native to ``click.Group(chain=True)``,
so the only custom code is a small :class:`PgkylGroup.get_command` override for
command-name abbreviation and treating a bare filename as an implicit ``load``.
Every command body lives in :mod:`postgkyl.cli.commands` and only uses the public
API (``pg.load``/``pg.plot`` and ``GData`` methods).
"""

from __future__ import annotations

from glob import glob

import click

from postgkyl import __version__
from postgkyl.cli.state import DataSpace
from postgkyl.cli.commands import COMMANDS, COMMAND_SECTIONS

# Hidden aliases (abbreviation already covers interp->interpolate, sel->select).
_ALIASES = {"pl": "plot"}


class PgkylGroup(click.Group):
  """Click's chained group + two conveniences: abbreviation & bare-filename load."""

  def get_command(self, ctx, name):
    cmd = super().get_command(ctx, name)
    if cmd is not None:
      return cmd
    if name in _ALIASES:
      return super().get_command(ctx, _ALIASES[name])
    matches = [c for c in self.list_commands(ctx) if c.startswith(name)]
    if len(matches) == 1:
      return super().get_command(ctx, matches[0])
    if matches:
      ctx.fail(f"Ambiguous command '{name}': {', '.join(sorted(matches))}")
    if glob(name):
      ctx.obj.in_data_strings.append(name)
      return super().get_command(ctx, "load")
    ctx.fail(f"'{name}' is not a command name nor a data file")

  def format_commands(self, ctx, formatter) -> None:
    """Group ``pgkyl --help``'s command listing under section headers.

    Presentation only (see ``commands/__init__.py``'s ``COMMAND_SECTIONS``
    and "14-cli.md"'s "Help output organization"): every command stays a
    flat, chainable top-level ``click.Command`` resolved exactly as before;
    only how they are *printed* changes, mirroring how ``git``/``docker``
    group their subcommand help.
    """
    for section, names in COMMAND_SECTIONS.items():
      rows = []
      for name in names:
        cmd = self.get_command(ctx, name)
        if cmd is None:
          continue
        # end
        rows.append((name, cmd.get_short_help_str(limit=formatter.width - 6)))
      # end
      if rows:
        with formatter.section(section):
          formatter.write_dl(rows)
        # end
      # end
    # end


@click.group(cls=PgkylGroup, chain=True,
    context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(__version__, "--version", prog_name="pgkyl")
@click.option("--batch-mode", is_flag=True, help="Do not show plots; save them instead.")
@click.option("--saveframes-prefix", default="pgkyl", help="Output prefix used in batch mode.")
@click.pass_context
def cli(ctx, batch_mode, saveframes_prefix) -> None:
  """Postprocessing and plotting tool for Gkeyll data.

  Datasets are loaded, processed and plotted by chaining commands, e.g.::

      pgkyl file.gkyl interp sel --z0 0 plot
  """
  ctx.obj = DataSpace(batch=batch_mode, prefix=saveframes_prefix)


for _command in COMMANDS:
  cli.add_command(_command)
# end


if __name__ == "__main__":
  cli()
