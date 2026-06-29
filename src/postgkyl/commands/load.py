import glob

import typer
from typing import List, Optional
from typing_extensions import Annotated

from postgkyl.data import GData
from postgkyl.data import GInterpModal
from postgkyl.commands._load_opts import resolve_load_options
from postgkyl.utils import verb_print


def _crush(s : str) -> tuple:  # Temp function used as a sorting key
  splitted = s.split("_")
  tmp = splitted[-1].split(".")
  splitted[-1] = int(tmp[0])
  splitted.append(tmp[1])
  return tuple(splitted)


def load(
    ctx: typer.Context,
    z0: Annotated[Optional[str], typer.Option("--z0", help="Partial file load: 0th coord (either int or slice).")] = None,
    z1: Annotated[Optional[str], typer.Option("--z1", help="Partial file load: 1st coord (either int or slice).")] = None,
    z2: Annotated[Optional[str], typer.Option("--z2", help="Partial file load: 2nd coord (either int or slice).")] = None,
    z3: Annotated[Optional[str], typer.Option("--z3", help="Partial file load: 3rd coord (either int or slice).")] = None,
    z4: Annotated[Optional[str], typer.Option("--z4", help="Partial file load: 4th coord (either int or slice).")] = None,
    z5: Annotated[Optional[str], typer.Option("--z5", help="Partial file load: 5th coord (either int or slice).")] = None,
    component: Annotated[Optional[str], typer.Option("--component", "-c", help="Partial file load: comps (either int or slice).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Specily tag for data.")] = "default",
    compgrid: Annotated[bool, typer.Option("--compgrid", help="Disregard the mapped grid information")] = False,
    varname: Annotated[Optional[List[str]], typer.Option("--varname", "-d", help="Allows to specify the Adios variable name. [default: 'CartGridField']")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Allows to specify the custom label")] = None,
    c2p: Annotated[Optional[str], typer.Option("--c2p", help="Specify the file name containing c2p mapped coordinates")] = None,
    c2p_vel: Annotated[Optional[str], typer.Option("--c2p-vel", help="Specify the file name containing c2p mapped coordinates")] = None,
    fv: Annotated[bool, typer.Option("--fv", help="Tag finite volume data when using c2p mapped coordinates")] = False,
    reader: Annotated[Optional[str], typer.Option("--reader", "-r", help="Allows to specify the Adios variable name (default is 'CartGridField')")] = None,
    load: Annotated[bool, typer.Option("--load/--no-load", help="Specify if data should be loaded.")] = True,
):
  verb_print(ctx, "Starting load")
  data = ctx.obj["data"]

  idx = ctx.obj["in_data_strings_loaded"]
  in_data_string = ctx.obj["in_data_strings"][idx]

  # Handling the wildcard characters
  if "*" in in_data_string or "?" in in_data_string or "!" in in_data_string:
    files = glob.glob(str(in_data_string))
    files = [f for f in files if f.find("restart") < 0]
    try:
      files = sorted(files, key=_crush)
    except Exception:
      typer.echo(
          typer.style("WARNING: The loaded files appear to be of different types. Sorting is turned off.",
              fg="yellow")
      )
    # end
  else:
    files = [in_data_string]
  # end

  # Resolve global pre-options vs. local options (local wins, with a warning).
  opts = resolve_load_options(ctx, z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5,
      component=component, varname=varname, c2p=c2p, c2p_vel=c2p_vel)
  z0, z1, z2, z3, z4, z5 = opts.cuts

  for var in opts.var_names:
    for fn in files:
      try:
        dat = GData(file_name=fn, tag=tag, comp_grid=ctx.obj["compgrid"],
            z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5, comp=opts.comp, var_name=var,
            label=label, mapc2p_name=opts.mapc2p_name,
            mapc2p_vel_name=opts.mapc2p_vel_name,
            reader_name=reader, load=load, click_mode=True)
        if fv:
          dg = GInterpModal(dat, 0, "ms")
          dg.interpolateGrid(overwrite=True)
        # end
        data.add(dat)
      except NameError as e:
        ctx.fail(typer.style(rf"{repr(e):s}", fg="red"))
      # end
    # end
  # end

  data.set_unique_labels()

  ctx.obj["in_data_strings_loaded"] += 1
  verb_print(ctx, "Finishing load")
