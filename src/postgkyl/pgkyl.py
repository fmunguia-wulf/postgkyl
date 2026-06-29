#!/usr/bin/env python3
"""Command line entry point for postgkyl.

Uses Typer (https://typer.tiangolo.com) to wrap pgkyl functions. Postgkyl keeps
Click's *chained* command behaviour (``pgkyl file.gkyl interp sel --z0 0 plot``),
which modern Typer no longer provides out of the box; the :class:`PgkylGroup`
below re-implements that chained dispatch on top of Typer's command group while
also supporting command-name abbreviations, explicit aliases and treating bare
file names as implicit ``load`` calls.
"""

from __future__ import annotations

from glob import glob
from typing import Annotated
import functools
import os.path
import sys
import time

import typer
from typer.core import TyperGroup

from postgkyl import __version__
from postgkyl.commands import _options as opt
from postgkyl.commands.state import AppState
from postgkyl.utils import load_style, verb_print
import postgkyl.commands as cmd


# Explicit aliases that should not appear in --help output.
_ALIASES = {
    "pl": "plot",
    "ply": "plotly",
    "ply-anim": "plotly_animate",
    "pv": "pyvista",
}


def _print_version(value: bool) -> None:
  if not value:
    return
  # end
  typer.echo(f"Postgkyl {__version__} ({sys.platform})")
  typer.echo(f"Python version: {sys.version}")
  typer.echo("Copyright 2016-2024 Gkeyll Team")
  typer.echo("Postgkyl can be used freely for research at universities,")
  typer.echo("national laboratories, and other non-profit institutions.")
  typer.echo("There is NO warranty.\n")
  typer.echo("Spam, egg, sausage, and spam.")
  raise typer.Exit()


class PgkylGroup(TyperGroup):
  """Custom pgkyl Typer command group class.

  It allows to:
    - chain multiple commands (``cmd1 ... cmd2 ...``) like Click's ``chain=True``
    - use shortened versions of command names
    - use explicit aliases
    - use a file name as a command
  """

  # Stop option parsing at the first bare token so the chained dispatch loop can
  # hand it off to the next command, mirroring Click's chained-group behaviour.
  allow_extra_args = True
  allow_interspersed_args = False
  chain = True

  def get_command(self, ctx: typer.Context, cmd_name: str):
    # cmd_name is a full name of a pgkyl command
    rv = self.commands.get(cmd_name)
    if rv is not None:
      return rv
    # end

    # cmd_name is an explicit (hidden) alias
    target = _ALIASES.get(cmd_name)
    if target is not None:
      rv = self.commands.get(target)
      if rv is not None:
        return rv
      # end
    # end

    # cmd_name is an abbreviation of a pgkyl command
    matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
    if matches and len(matches) == 1:
      return self.commands.get(matches[0])
    elif matches:
      ctx.fail(f"Too many matches for '{cmd_name}': {', '.join(sorted(matches))}")
    # end

    # cmd_name is a data set
    if glob(cmd_name):
      ctx.obj.in_data_strings.append(cmd_name)
      return self.commands.get("load")
    # end

    ctx.fail(f"'{cmd_name}' does not match either command name nor a data file")

  def resolve_command(self, ctx: typer.Context, args: list[str]):
    cmd_name = args[0]
    command = self.get_command(ctx, cmd_name)
    if command is None and not ctx.resilient_parsing:
      ctx.fail(f"No such command {cmd_name!r}.")
    # end
    return (command.name if command else None), command, args[1:]

  def invoke(self, ctx: typer.Context):
    # No subcommand: just run the group callback (sets up ctx.obj).
    if not ctx._protected_args:
      with ctx:
        super(TyperGroup, self).invoke(ctx)
      # end
      return []
    # end

    args = [*ctx._protected_args, *ctx.args]
    ctx.args = []
    ctx._protected_args = []

    with ctx:
      # Run the group callback before any subcommand, like Click groups do.
      super(TyperGroup, self).invoke(ctx)
      ctx.invoked_subcommand = "*"
      while args:
        cmd_name, command, args = self.resolve_command(ctx, args)
        if command is None:
          break
        # end
        sub_ctx = command.make_context(
            cmd_name, args, parent=ctx,
            allow_extra_args=True, allow_interspersed_args=False,
        )
        with sub_ctx:
          sub_ctx.command.invoke(sub_ctx)
          args = sub_ctx.args
        # end
      # end
    # end
    return []


app = typer.Typer(
    cls=PgkylGroup,
    add_completion=False,
    no_args_is_help=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
    help="Postprocessing and plotting tool for Gkeyll data.\n\n"
         "Datasets can be loaded, processed and plotted using a command chaining "
         "mechanism. For full documentation see the Gkeyll documentation webpages "
         "(https://gkeyll.readthedocs.io). Help for individual commands can be "
         "obtained using the --help option for that command.",
)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Turn on verbosity.")] = False,
    batch_mode: Annotated[bool, typer.Option("--batch-mode", help="Run in batch mode (no plots will be shown).")] = False,
    saveframes_prefix: Annotated[str, typer.Option("--saveframes-prefix", help="Output prefix to use for plot output in batch mode.")] = os.path.expanduser("~") + "/pg",
    version: Annotated[bool | None, typer.Option("--version", callback=_print_version, is_eager=True, help="Print the version information.")] = None,
    z0: opt.Z0 = None,
    z1: opt.Z1 = None,
    z2: opt.Z2 = None,
    z3: opt.Z3 = None,
    z4: opt.Z4 = None,
    z5: opt.Z5 = None,
    component: opt.Component = None,
    compgrid: opt.CompGrid = False,
    varname: opt.VarName = None,
    style: Annotated[str | None, typer.Option("--style", help="Sets Maplotlib rcParams style file.")] = None,
):
  """Postprocessing and plotting tool for Gkeyll data."""
  # The main context object: a typed AppState (see commands/state.py).
  ctx.obj = AppState(
      verbose=bool(verbose),
      batch_mode=bool(batch_mode),
      saveframes_prefix=saveframes_prefix,
      compgrid=compgrid,
      global_var_names=varname,
      global_cuts=(z0, z1, z2, z3, z4, z5, component),
      start_time=time.time(),  # Timings are written in the verbose mode
  )

  if verbose:
    # Monty Python references should be a part of any Python code
    verb_print(ctx, "This is Postgkyl running in verbose mode!")
    verb_print(ctx, "Spam! Spam! Spam! Spam! Lovely Spam! Lovely Spam!")
    verb_print(ctx, "And now for something completelly different...")
  # end

  fn = style if style else f"{os.path.dirname(os.path.realpath(__file__))}/output/postgkyl.mplstyle"
  load_style(ctx, fn)


# Hook the individual commands into pgkyl. The (name, callback, hidden) triples
# mirror the command names produced by the previous Click registration.
_COMMANDS = [
    ("config", cmd.config, False),
    ("activate", cmd.activate, False),
    ("agyro", cmd.agyro, False),
    ("mom-agyro", cmd.mom_agyro, False),
    ("animate", cmd.animate, False),
    ("plotly-animate", cmd.plotly_animate, False),
    ("collect", cmd.collect, False),
    ("current", cmd.current, False),
    ("deactivate", cmd.deactivate, False),
    ("differentiate", cmd.differentiate, False),
    ("energetics", cmd.energetics, False),
    ("euler", cmd.euler, False),
    ("mhd", cmd.mhd, False),
    ("ev", cmd.ev, False),
    ("extractinput", cmd.extractinput, False),
    ("fft", cmd.fft, False),
    ("fit", cmd.fit, False),
    ("gk-nodes", cmd.gk_nodes, False),
    ("dg-local-poly", cmd.dg_local_poly, False),
    ("gk-distf", cmd.gk_distf, False),
    ("gk-load-quantity", cmd.gk_load_quantity, False),
    ("grid", cmd.grid, False),
    ("growth", cmd.growth, False),
    ("info", cmd.info, False),
    ("integrate", cmd.integrate, False),
    ("interpolate", cmd.interpolate, False),
    ("laguerrecompose", cmd.laguerrecompose, False),
    ("listoutputs", cmd.listoutputs, False),
    ("load", cmd.load, True),
    ("magsq", cmd.magsq, False),
    ("map", cmd.map, False),
    ("mask", cmd.mask, False),
    ("gk-energy-balance", cmd.gk_energy_balance, False),
    ("gk-particle-balance", cmd.gk_particle_balance, False),
    ("plot", cmd.plot, False),
    ("plotly", cmd.plotly, False),
    ("pyvista", cmd.pyvista, False),
    ("pr", cmd.pr, False),
    ("relchange", cmd.relchange, False),
    ("select", cmd.select, False),
    ("style", cmd.style, False),
    ("tenmoment", cmd.tenmoment, False),
    ("trajectory", cmd.trajectory, False),
    ("val2coord", cmd.val2coord, False),
    ("velocity", cmd.velocity, False),
    ("write", cmd.write, False),
    ("transformframe", cmd.transformframe, False),
    ("pkpm", cmd.pkpm, False),
]

def _traced(name: str, func):
  """Wrap a command callback to emit verbose Starting/Finishing markers.

  Centralizes the bracketing that used to be hand-written at the top and bottom
  of every command body. ``functools.wraps`` keeps the signature and docstring
  intact so Typer's introspection (and ``--help``) is unaffected.
  """
  @functools.wraps(func)
  def wrapper(ctx: typer.Context, *args, **kwargs):
    verb_print(ctx, f"Starting {name}")
    try:
      return func(ctx, *args, **kwargs)
    finally:
      verb_print(ctx, f"Finishing {name}")
    # end
  return wrapper


for _name, _func, _hidden in _COMMANDS:
  app.command(name=_name, hidden=_hidden)(_traced(_name, _func))
# end

# The Click command object exposed via the ``pgkyl`` console-script entry point.
cli = typer.main.get_command(app)


if __name__ == "__main__":
  cli()
# end
