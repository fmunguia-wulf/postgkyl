import numpy as np
import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl.data import GData
from postgkyl.data import select as pselect
from postgkyl.ops.ev import apply_operator
from postgkyl.tools.ev_ops import cmds
from postgkyl.utils import verb_print


help_str = ""
for s in cmds.keys():
  help_str += f" '{s:s}',"
# end


def _data(ctx, grid_stack, value_stack, ctx_stack, str_in, tags, only_active):
  """Resolve a CLI data token against the DataSpace, pushing it onto the stacks.

  Unlike the script-API token parser in ``ops.ev``, the CLI lets a token select
  by *tag* and broadcast over every matching dataset, so this resolver stays in
  the command layer where the DataSpace lives.
  """
  str_in_split = str_in.split("[")
  if str_in[0] == "f" or str_in_split[0] in tags:
    tag_nm = None
    if str_in_split[0] in tags:
      tag_nm = str_in_split[0]
      only_active = False
    # end
    set_idx = None
    if len(str_in_split) >= 2:
      set_idx = str_in_split[1].split("]")[0]
    # end
    comp_idx = None
    if len(str_in_split) == 3:
      comp_idx = str_in_split[2].split("]")[0]
    # end
    ctx_key = None
    if len(str_in.split(".")) == 2:
      ctx_key = str_in.split(".")[1]
    # end

    grid_stack.append([])
    value_stack.append([])
    ctx_stack.append([])

    for dat in ctx.obj["data"].iterator(tag=tag_nm, select=set_idx, only_active=only_active):
      tag_nm = dat.get_tag()
      if ctx_key:
        grid = None
        if ctx_key in dat.ctx:
          values = np.array(dat.ctx[ctx_key])
        else:
          ctx.fail(typer.style(f"Wrong ctx key '{ctx_key:s}' specified", fg="red"))
        # end
      else:
        grid, values = pselect(dat, comp=comp_idx)
      # end
      grid_stack[-1].append(grid)
      value_stack[-1].append(values)
      ctx_stack[-1].append(dat.ctx)
    # end
    return True, (tag_nm, set_idx)
  elif "(" in str_in or "[" in str_in:
    value_stack.append([eval(str_in)])
    grid_stack.append([None])
    ctx_stack.append([{}])
    return True, ()
  elif ":" in str_in or "," in str_in:
    value_stack.append([str(str_in)])
    grid_stack.append([None])
    ctx_stack.append([{}])
    return True, ()
  else:
    try:
      value_stack.append([np.array(float(str_in))])
      grid_stack.append([None])
      ctx_stack.append([{}])
      return True, ()
    except Exception:
      return False, ()
    # end
  # end


def ev(
    ctx: typer.Context,
    chain: Annotated[str, typer.Argument()],
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the result")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
    all: Annotated[bool, typer.Option("--all", "-a", help="Ignore the status of a dataset")] = False,
):
  """Manipulate datasets using math expressions. Expressions are specified using Reverse Polish Notation (RPN)."""
  verb_print(ctx, "Starting evaluate")
  data = ctx.obj["data"]

  grid_stack, value_stack, ctx_stack = [], [], []
  chain_split = list(filter(None, chain.split(" ")))

  only_active = not all

  tags = list(data.tag_iterator(only_active=only_active))
  if label is None:
    label = chain
  # end

  num_datasets_in_chain = 0
  out_data_id = ()
  for s in chain_split:
    is_data, data_id = _data(ctx, grid_stack, value_stack, ctx_stack, s, tags, only_active)
    if is_data and len(data_id) > 0 and data_id != out_data_id:
      num_datasets_in_chain += 1
      out_data_id = data_id
    # end
    if not is_data:
      try:
        is_command = apply_operator(grid_stack, value_stack, ctx_stack, s)
      except ValueError as err:
        ctx.fail(typer.style(f"{err}", fg="red"))
      # end
    # end
    if not is_data and not is_command:
      ctx.fail(typer.style(f"Evaluate input '{s:s}' represents neither data nor commad",
          fg="red"))
    # end
  # end

  if len(value_stack) == 0:
    ctx.fail(typer.style("Evaluate stack is empty, there is nothing to return", fg="red"))
  elif len(value_stack) > 1:
    typer.echo(
        typer.style("WARNING: Length of the evaluate stack is bigger than 1, there is a posibility of unintended behavior",
            fg="yellow" ))
  # end
  if num_datasets_in_chain == 1 and tag is None:
    cnt = 0
    out_tag = out_data_id[0]
    for out in ctx.obj["data"].iterator(tag=out_tag, select=out_data_id[1], only_active=only_active):
      out.push(grid_stack[-1][cnt], value_stack[-1][cnt])
      cnt += 1
    # end
  else:
    out_tag = tag if tag else out_data_id[0]
    if not tag:
      data.deactivate_all()
    # end
    for grid, values, data_ctx in zip(grid_stack[-1], value_stack[-1], ctx_stack[-1]):
      out = GData(tag=out_tag, label=label, ctx=data_ctx)
      out.push(grid, values)
      data.add(out)
    # end
  # end

  verb_print(ctx, "Finishing ev")


# Preserve the original dynamic help that lists every supported RPN operator.
ev.__doc__ = (
    "Manipulate datasets using math expressions. Expressions are specified using "
    f"Reverse Polish Notation (RPN).\n Supported operators are: {help_str[:-1]}"
)
