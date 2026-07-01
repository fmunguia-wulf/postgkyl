from typing import Annotated, Optional

import typer



def info(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("-u", "--use", help="Specify a 'tag' to apply to (default all tags).")] = None,
    compact: Annotated[bool, typer.Option("-c", "--compact", help="Show in compact mode.")] = False,
    allsets: Annotated[bool, typer.Option("-a", "--allsets", help="All data sets.")] = False,
):
  """Print info of active datasets."""
  data = ctx.obj.data
  if allsets:
    only_active = False
  else:
    only_active = True
  # end

  for i, dat in data.iterator(use, enum=True, only_active=only_active):
    if dat.get_status():
      color = "green"
      bold = True
    else:
      color = None
      bold = False
    # end
    typer.echo(
        typer.style(f"{dat.get_label():s}{' ' if dat.get_label() else '':s}({dat.get_tag():s}#{i:d})",
            fg=color, bold=bold)
    )
    if not compact:
      dat.info(header=False)  # the colored header above replaces info's own
      typer.echo("")          # trailing blank line between datasets
    # end
  # end

