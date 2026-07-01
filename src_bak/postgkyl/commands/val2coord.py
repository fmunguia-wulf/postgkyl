from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops


def val2coord(
    ctx: typer.Context,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
    x: Annotated[Optional[str], typer.Option("-x", help="Select components that will became the grid of the new dataset.")] = None,
    y: Annotated[Optional[str], typer.Option("-y", help="Select components that will became the values of the new dataset.")] = None,
    periodic: Annotated[bool, typer.Option("--periodic", "-p", help="Set the last component to match the first one.")] = False,
):
  """Given a dataset (typically a DynVector) selects columns from it to create new datasets.

  For example, you can choose say column 1 to be the X-axis of the new dataset and
  column 2 to be the Y-axis. Multiple columns can be choosen using range specifiers and
  as many datasets are then created.
  """
  data = ctx.obj.data

  out_tag = tag
  if out_tag is None:
    tags = list(data.tag_iterator())
    out_tag = tags[0] if len(tags) == 1 else "val2coord"
  # end

  for dat in data.iterator(use):
    group = ops.val2coord(dat, x=x, y=y,
        periodic=periodic, tag=out_tag, label=label)
    for out in group:
      data.add(out)
    # end
    dat.deactivate()
  # end
