from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def collect(
    ctx: typer.Context,
    sumdata: Annotated[bool, typer.Option("-s", "--sumdata", help="Sum data in the collected datasets (retain components).")] = False,
    period: Annotated[Optional[float], typer.Option("-p", "--period", help="Specify a period to create epoch data instead of time data.")] = None,
    offset: Annotated[Optional[float], typer.Option("--offset", help="Specify an offset to create epoch data instead of time data.")] = 0.0,
    chunk: Annotated[Optional[int], typer.Option("-c", "--chunk", help="Collect into chunks with specified length rather than into a single dataset.")] = None,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Specify a 'tag' for the result.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Specify the custom label for the result.")] = None,
):
  """Collect data from the active datasets and create a new combined dataset.

  The time-stamp in each of the active datasets is collected and used as the new X-axis.
  Data can be collected in chunks, in which case several datasets are created, each with
  the chunk-sized pieces collected into each new dataset.
  """
  verb_print(ctx, "Starting collect")
  data = ctx.obj["data"]
  comp_grid = ctx.obj["compgrid"]

  out_tags = tag.split(",") if tag else None

  for tag_cnt, in_tag in enumerate(data.tag_iterator(use)):
    datasets = list(data.iterator(in_tag))
    # The result label defaults to the members' custom label (then 'collect',
    # handled by ops.collect); an explicit --label overrides.
    resolved_label = label
    if resolved_label is None and datasets:
      resolved_label = datasets[-1].get_custom_label()
    # end

    out_tag = in_tag
    if out_tags:
      out_tag = out_tags[tag_cnt] if len(out_tags) > 1 else out_tags[0]
    # end

    data.deactivate_all(in_tag)

    # A single dataset by default; --chunk splits the frames into fixed-size
    # groups, each collected into its own dataset.
    step = chunk if chunk else len(datasets)
    for start in range(0, len(datasets), max(step, 1)):
      data.add(ops.collect(datasets[start:start + step], sumdata=sumdata,
          period=period, offset=offset, comp_grid=comp_grid, tag=out_tag,
          label=resolved_label))
    # end
  # end

  verb_print(ctx, "Finishing collect")
