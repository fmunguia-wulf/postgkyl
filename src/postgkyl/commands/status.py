import typer
from typing import Annotated, Optional



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
  data = ctx.obj.data

  if not focused:
    data.deactivate_all()
  # end

  for dat in data.iterator(tag=tag, only_active=False, select=index):
    dat.activate()
  # end



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
  data = ctx.obj.data

  if focused:
    data.activate_all()
  # end

  for dat in data.iterator(tag=tag, only_active=False, select=index):
    dat.deactivate()
  # end

