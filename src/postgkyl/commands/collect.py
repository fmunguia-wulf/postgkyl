from typing import Optional

import typer
from typing_extensions import Annotated
import numpy as np

from postgkyl.data import GData
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
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting collect")
  data = ctx.obj["data"]

  if kwargs["tag"]:
    out_tags = kwargs["tag"].split(",")
  # end

  tag_cnt = 0
  for tag in data.tag_iterator(kwargs["use"]):
    time = [[]]
    values = [[]]
    grid = [[]]
    cnt = 0
    label = None

    for i, dat in data.iterator(tag, enum=True):
      cnt += 1
      if kwargs["chunk"] and cnt > kwargs["chunk"]:
        cnt = 1
        time.append([])
        values.append([])
        grid.append([])
      # end
      if dat.ctx["time"]:
        time[-1].append(dat.ctx["time"])
      elif dat.ctx["frame"]:
        time[-1].append(dat.ctx["frame"])
      else:
        time[-1].append(i)
      # end
      val = dat.get_values()
      if kwargs["sumdata"]:
        num_dims = dat.get_num_dims()
        axis = tuple(range(num_dims))
        values[-1].append(np.nansum(val, axis=axis))
      else:
        values[-1].append(val)
      # end
      if not grid[-1]:
        grid[-1] = dat.get_grid().copy()
      # end
      label = dat.get_custom_label()
    # end

    data.deactivate_all(tag)

    out_tag = tag
    if kwargs["tag"]:
      if len(out_tags) > 1:
        out_tag = out_tags[tag_cnt]
      else:
        out_tag = out_tags[0]
      # end
    # end
    tag_cnt += 1

    if label is None:
      label = "collect"
    # end
    if kwargs["label"]:
      label = kwargs["label"]
    # end

    for i in range(len(time)):
      time[i] = np.array(time[i])
      values[i] = np.array(values[i])

      if kwargs.get("period"):
        time[i] = (time[i] - kwargs["offset"]) % kwargs["period"]
      # end

      sort_idx = np.argsort(time[i])
      time[i] = time[i][sort_idx]
      values[i] = values[i][sort_idx]

      if kwargs["sumdata"]:
        grid[i] = [time[i]]
      else:
        grid[i].insert(0, np.array(time[i]))
      # end

      out = GData(tag=out_tag, label=label, comp_grid=ctx.obj["compgrid"])
      out.push(grid[i], values[i])
      data.add(out)
    # end
  # end

  verb_print(ctx, "Finishing collect")
