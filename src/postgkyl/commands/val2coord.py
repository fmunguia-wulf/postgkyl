from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def val2coord(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the result.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
    x: Annotated[Optional[str], typer.Option("-x", help="Select components that will became the grid of the new dataset.")] = None,
    y: Annotated[Optional[str], typer.Option("-y", help="Select components that will became the values of the new dataset.")] = None,
    periodic: Annotated[bool, typer.Option("--periodic", "-p", help="Set the last component to match the first one.")] = False,
):
  """Given a dataset (typically a DynVector) selects columns from it to create new datasets.

  For example, you can choose say column 1 to be the X-axis of the new dataset and
  column 2 to be the Y-axis. Multiple columns can be choosen using range specifiers and
  as many datasets are then created.
  """
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting val2coord")
  data = ctx.obj["data"]

  out_tag = kwargs["tag"]
  if out_tag is None:
    tags = list(data.tag_iterator())
    out_tag = tags[0] if len(tags) == 1 else "val2coord"
  # end

  for dat in data.iterator(kwargs["use"]):
    group = ops.val2coord(dat, x=kwargs["x"], y=kwargs["y"],
        periodic=kwargs["periodic"], tag=out_tag, label=kwargs["label"])
    for out in group:
      data.add(out)
    # end
    dat.deactivate()
  # end
  verb_print(ctx, "Finishing val2coord")
