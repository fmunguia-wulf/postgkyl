from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def laguerrecompose(
    ctx: typer.Context,
    distribution: Annotated[Optional[str], typer.Option("--distribution", "-f", prompt=True, help="Specify the PKPM distribution function dataset.")] = None,
    tm: Annotated[Optional[str], typer.Option("--tm", prompt=True, help="Specify the PKPM vars dataset.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
):
  """Compose PKPM Laguerre coefficients together."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting laguerrecompose")
  data = ctx.obj["data"]

  for f, tm in zip(data.iterator(kwargs["distribution"]), data.iterator(kwargs["tm"])):
    if kwargs["tag"]:
      data.add(ops.laguerre_compose(f, tm, tag=kwargs["tag"], label=kwargs["label"]))
    else:
      ops.laguerre_compose(f, tm, inplace=True)
    # end
  # end
  verb_print(ctx, "Finishing laguerrecompose")
