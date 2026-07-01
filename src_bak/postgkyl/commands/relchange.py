from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops


def relchange(
    ctx: typer.Context,
    use: opt.Use = None,
    index: Annotated[Optional[int], typer.Option("--index", "-i", help="Dataset index for computing change relative to.")] = 0,
    comp: Annotated[Optional[str], typer.Option("--comp", "-c", help="Dataset component to be compared to if user only wants to compare to a single component.")] = None,
    tag: opt.Tag = "rel_change",
    label: opt.Label = "delta",
):
  """Computes the relative change between two datasets"""

  data = ctx.obj.data
  for src_tag in data.tag_iterator(use):
    reference = data.get_dataset(index, src_tag)
    for dat in data.iterator(src_tag):
      if tag:
        out = ops.relchange(dat, reference, comp=comp, tag=tag)
        dat.deactivate()
        data.add(out)
      else:
        ops.relchange(dat, reference, comp=comp, inplace=True)
      # end
    # end
  # end
