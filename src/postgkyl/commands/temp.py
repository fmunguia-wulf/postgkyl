import numpy as np
import typer
from typing_extensions import Annotated

from postgkyl.utils import verb_print



# ---- Math ----
def mult(
    ctx: typer.Context,
    factor: Annotated[float, typer.Argument()],
):
  """Multiply data by a factor"""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, f"Multiplying by {kwargs['factor']:f}")
  for s in ctx.obj["sets"]:
    values = ctx.obj["dataSets"][s].get_values()
    values = values * kwargs["factor"]
    ctx.obj["dataSets"][s].push(values)
  # end


def pow(
    ctx: typer.Context,
    power: Annotated[float, typer.Argument()],
):
  """Calculate power of data"""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, f"Calculating the power of {kwargs['power']:f}")
  for s in ctx.obj["sets"]:
    values = ctx.obj["dataSets"][s].get_values()
    values = values ** kwargs["power"]
    ctx.obj["dataSets"][s].push(values)
  # end


def log(ctx: typer.Context):
  """Calculate natural log of data"""
  verb_print(ctx, "Calculating the natural log")
  for s in ctx.obj["sets"]:
    values = ctx.obj["dataSets"][s].get_values()
    values = np.log(values)
    ctx.obj["dataSets"][s].push(values)
  # end


def abs(ctx: typer.Context):
  """Calculate absolute values of data"""
  verb_print(ctx, "Calculating the absolute value")
  for s in ctx.obj["sets"]:
    values = ctx.obj["dataSets"][s].get_values()
    values = np.abs(values)
    ctx.obj["dataSets"][s].push(values)
  # end


def norm(
    ctx: typer.Context,
    shift: Annotated[bool, typer.Option("--shift/--no-shift", help="Shift minimal value to zero.")] = False,
    usefirst: Annotated[bool, typer.Option("--usefirst", help="Normalize to first value in field.")] = False,
):
  """Normalize data"""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Normalizing data")
  for s in ctx.obj["sets"]:
    values = ctx.obj["dataSets"][s].get_values()
    num_comps = ctx.obj["dataSets"][s].get_num_comps()
    values_out = values.copy()
    for comp in range(num_comps):
      if kwargs["shift"]:
        values_out[..., comp] -= values_out[..., comp].min()
      if kwargs["usefirst"]:
        values_out[..., comp] /= values_out[..., comp].item(0)
      else:
        values_out[..., comp] /= np.abs(values_out[..., comp]).max()
      # end
    # end
    ctx.obj["dataSets"][s].push(values_out)
  # end
