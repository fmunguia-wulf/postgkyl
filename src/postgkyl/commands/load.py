import glob
from typing import Annotated

import typer

from postgkyl.data import GData
from postgkyl.commands import _options as opt
from postgkyl.commands._load_opts import resolve_load_options
from postgkyl.commands.state import AppState


def _crush(s: str) -> tuple:
  """Sort key: split a frame name so its trailing ``_<int>`` sorts numerically."""
  parts = s.split("_")
  stem, ext = parts[-1].split(".")
  parts[-1] = int(stem)
  parts.append(ext)
  return tuple(parts)


def _resolve_files(pattern: str) -> list[str]:
  """Expand a load pattern into a sorted, restart-free list of file names."""
  if not any(c in pattern for c in "*?!"):
    return [pattern]
  # end
  files = [f for f in glob.glob(pattern) if "restart" not in f]
  try:
    return sorted(files, key=_crush)
  except Exception:
    typer.secho("WARNING: The loaded files appear to be of different types. "
        "Sorting is turned off.", fg=typer.colors.YELLOW)
    return files
  # end


def load(
    ctx: typer.Context,
    z0: opt.Z0 = None,
    z1: opt.Z1 = None,
    z2: opt.Z2 = None,
    z3: opt.Z3 = None,
    z4: opt.Z4 = None,
    z5: opt.Z5 = None,
    component: opt.Component = None,
    tag: Annotated[str, typer.Option("--tag", "-t", help="Specily tag for data.")] = "default",
    compgrid: opt.CompGrid = False,
    varname: opt.VarName = None,
    label: Annotated[str | None, typer.Option("--label", "-l", help="Allows to specify the custom label")] = None,
    reader: Annotated[str | None, typer.Option("--reader", "-r", help="Allows to specify the Adios variable name (default is 'CartGridField')")] = None,
    do_load: Annotated[bool, typer.Option("--load/--no-load", help="Specify if data should be loaded.")] = True,
):
  state: AppState = ctx.obj

  in_data_string = state.in_data_strings[state.in_data_strings_loaded]
  files = _resolve_files(in_data_string)

  # Resolve global pre-options vs. local options (local wins, with a warning).
  opts = resolve_load_options(ctx, z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5,
      component=component, varname=varname)
  z0, z1, z2, z3, z4, z5 = opts.cuts

  for var in opts.var_names:
    for fn in files:
      try:
        state.data.add(GData(
            file_name=fn, tag=tag, comp_grid=state.compgrid,
            z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5, comp=opts.comp,
            var_name=var, label=label, reader_name=reader,
            load=do_load, cli_mode=True))
      except NameError as e:
        typer.secho(repr(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
      # end
    # end
  # end

  state.data.set_unique_labels()

  state.in_data_strings_loaded += 1
