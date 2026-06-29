import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl.utils import verb_print


def activate(
    ctx: typer.Context,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag(s) to apply to (comma-separated).")] = None,
    index: Annotated[Optional[str], typer.Option("--index", "-i", help="Dataset indices (e.g., '1', '0,2,5', or '1:6:2').")] = None,
    focused: Annotated[bool, typer.Option("--focused", "-f", help="Leave unspecified datasets untouched.")] = False,
):
  """Select datasets(s) to pass further down the command chain.

  Datasets are indexed starting 0. Multiple datasets can be selected using a comma
  separated list or a range specifier. Unless '--focused' is selected, all unselected
  datasets will be deactivated.

  '--tag' and '--index' allow to specify tags and indices. The not specified, 'activate'
  applies to all. Both parameters support comma-separated values. '--index' also
  supports slices following the Python conventions, e.g., '3:7' or ':-5:2'.

  'info' command (especially with the '-ac' flags) can be helpful when
  activating/deactivating multiple datasets.
  """
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting activate")
  data = ctx.obj["data"]

  if not kwargs["focused"]:
    data.deactivate_all()
  # end

  for dat in data.iterator(tag=kwargs["tag"], only_active=False, select=kwargs["index"]):
    dat.activate()
  # end

  verb_print(ctx, "Finishing activate")


def deactivate(
    ctx: typer.Context,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag(s) to apply to (comma-separated).")] = None,
    index: Annotated[Optional[str], typer.Option("--index", "-i", help="Dataset indices (e.g., '1', '0,2,5', or '1:6:2').")] = None,
    focused: Annotated[bool, typer.Option("--focused", "-f", help="Leave unspecified datasets untouched.")] = False,
):
  """Select datasets(s) to pass further down the command chain.

  Datasets are indexed starting 0. Multiple datasets can be selected using a comma
  separated list or a range specifier. Unless '--focused' is selected, all unselected
  datasets will be activated.

  '--tag' and '--index' allow to specify tags and indices. The not specified,
  'deactivate' applies to all. Both parameters support comma-separated values. '--index'
  also supports slices following the Python conventions, e.g., '3:7' or ':-5:2'.

  'info' command (especially with the '-ac' flags) can be helpful when
  activating/deactivating multiple datasets.
  """
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting deactivate")
  data = ctx.obj["data"]

  if kwargs["focused"]:
    data.activate_all()
  # end

  for dat in data.iterator(tag=kwargs["tag"], only_active=False, select=kwargs["index"]):
    dat.deactivate()
  # end

  verb_print(ctx, "Finishing deactivate")
