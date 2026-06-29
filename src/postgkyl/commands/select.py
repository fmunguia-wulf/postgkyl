import numpy as np
import typer
from postgkyl.commands import _options as opt
from typing import Annotated

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.commands.state import AppState
from postgkyl.data import GData
from postgkyl.utils import set_frame

import postgkyl.data.select


def select(
    ctx: typer.Context,
    z0: Annotated[str | None, typer.Option("--z0", help="Indices for 0th coord (either int, float, or slice).")] = None,
    z1: Annotated[str | None, typer.Option("--z1", help="Indices for 1st coord (either int, float, or slice).")] = None,
    z2: Annotated[str | None, typer.Option("--z2", help="Indices for 2nd coord (either int, float, or slice).")] = None,
    z3: Annotated[str | None, typer.Option("--z3", help="Indices for 3rd coord (either int, float, or slice).")] = None,
    z4: Annotated[str | None, typer.Option("--z4", help="Indices for 4th coord (either int, float, or slice).")] = None,
    z5: Annotated[str | None, typer.Option("--z5", help="Indices for 5th coord (either int, float, or slice).")] = None,
    comp: Annotated[str | None, typer.Option("--comp", "-c", help="Indices for components (either int, slice, or coma-separated).")] = None,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
    multiblock: Annotated[bool, typer.Option("--multiblock", "-m", help="Necessary parameter for multiblock lineouts in z0 or z1 dims")] = False,
    multiframe: Annotated[bool, typer.Option("--multiframe", "-f", help="Specify if performing select on multiple multiblock frames")] = False,
):
  """Subselect data from the active dataset(s).

  This command allows, for example, to choose a specific component of a multi-component
  dataset, select a index or coordinate range. Index ranges can also be specified using
  python slice notation (start:end:stride).
  """
  state: AppState = ctx.obj
  data = state.data

  #multiblock case
  if multiblock:

    #set ctx frames
    frame_list = set_frame(ctx)
    #creates list of lists with blocks per frame if multiframe parameter
    #if not, then only one frame with all blocks
    if multiframe:
      data_list = []
      for frame in frame_list:
        frame_data_list = [dat for dat in data.iterator(use) if dat.ctx["frame"] == frame]
        data_list.append(frame_data_list)
      # end
    else:
      data_list = [list(data.iterator(use))]
    # end


    for i, frame in enumerate(data_list):
    
      #establish lower bounds for x and y axis
      botlef_point = []
      for dim in [0,1]:
        botlef_point.append(min([dat.get_bounds()[0][dim] for dat in frame]))
      # end
      #find starting block for lineout coordinate
      if z0:
        for dat in frame:
          if dat.get_bounds()[0][0] <= float(z0) <= dat.get_bounds()[1][0] and dat.get_bounds()[0][1] == botlef_point[1]:
            block = dat
          # end
        # end
      # end
      if z1:
        for dat in frame:
          if dat.get_bounds()[0][1] <= float(z1) <= dat.get_bounds()[1][1] and dat.get_bounds()[0][0] == botlef_point[0]:
            block = dat
          # end
        # end
      # end
      #find neighboring blocks of starting block
      block.set_neighbors(frame)

      value_list = []

      #creates new grid and value list containing data from blocks which contain specified z0 coordinate
      if z0:
        grid, values = postgkyl.data.select(block,
                                            z0=z0,
                                            comp=comp)
        grid_list = grid
        for val in values[0]:
          value_list.append(val)
        # end
        while block._neighbors[1][1] is not None:
          block = block._neighbors[1][1]
          block.set_neighbors(data.iterator(use))
          grid, values = postgkyl.data.select(block,
                                              z0=z0,
                                              comp=comp)
          grid_list[1] = np.append(grid_list[1], grid[1])
          for val in values[0]:
            value_list.append(val)
          # end
        # end
        grid_list[1] = np.unique(grid_list[1])
        value_list = np.array([value_list])
      # end


      #same but for z1 coordinate
      if z1:
        grid, values = postgkyl.data.select(block,
                                              z1=z1,
                                              comp=comp)
        grid_list = grid
        for val in values:
          value_list.append(val)
        # end
        while block._neighbors[0][1] is not None:
          block = block._neighbors[0][1]
          block.set_neighbors(data.iterator(use))
          grid, values = postgkyl.data.select(block,
                                              z1=z1,
                                              comp=comp)
          grid_list[0] = np.append(grid_list[0], grid[0])
          for val in values:
            value_list.append(val)
          # end
        grid_list[0] = np.unique(grid_list[0])
        value_list = np.array(value_list)
      # end

      #loop through frame list and deactivate each
      for dat in frame:
        dat.deactivate()
      # end

      #create new gdata instance and push new stitched grid and values
      out = GData(tag=tag,
                  label=label,
                  comp_grid=state.compgrid)
      out.ctx["frame"] = i
      out.push(grid_list, value_list)
      data.add(out)
    # end


  else:
    apply(ctx, ops.select, use=use, tag=tag, label=label,
        z0=z0, z1=z1, z2=z2, z3=z3,
        z4=z4, z5=z5, comp=comp)
  # end
