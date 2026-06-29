from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def relchange(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    index: Annotated[Optional[int], typer.Option("--index", "-i", help="Dataset index for computing change relative to.")] = 0,
    comp: Annotated[Optional[str], typer.Option("--comp", "-c", help="Dataset component to be compared to if user only wants to compare to a single component.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the result.")] = "rel_change",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result/")] = "delta",
):
  """Computes the relative change between two datasets"""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting relative change")

  data = ctx.obj["data"]
  for tag in data.tag_iterator(kwargs["use"]):
    reference = data.get_dataset(kwargs["index"], tag)
    for dat in data.iterator(tag):
      if kwargs["tag"]:
        out = ops.relchange(dat, reference, comp=kwargs["comp"], tag=kwargs["tag"])
        dat.deactivate()
        data.add(out)
      else:
        ops.relchange(dat, reference, comp=kwargs["comp"], inplace=True)
      # end
    # end
  # end
  verb_print(ctx, "Finishing relative change")
