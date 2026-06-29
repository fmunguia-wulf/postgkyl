import typer
from typing import Annotated, List, Optional

from postgkyl.utils import load_style


def style(
    ctx: typer.Context,
    file: Annotated[Optional[str], typer.Option("--file", "-f", help="Sets Maplotlib rcParams style file.")] = None,
    set: Annotated[Optional[List[str]], typer.Option("--set", "-s", help="Sets individual rcParam(s) as 'key:value'.")] = [],
    print: Annotated[bool, typer.Option("--print", "-p", help="Prints the current rcParams.")] = False,
):
  """Probe and control the Matplotlib plotting style.

  The list of rcParams is available
  here:\nhttps://matplotlib.org/stable/api/matplotlib_configuration_api.html"""

  if file:
    load_style(ctx, file)
  # end

  for param in set:
    param_split = param.split(":")
    key = param_split[0].strip()
    value = param[len(param_split[0]) + 1 :].strip()
    ctx.obj.rcParams[key] = value
  # end

  if print:
    for key in ctx.obj.rcParams:
      typer.echo(f"{key:s} : {ctx.obj.rcParams[key]}")
    # end
  # end

