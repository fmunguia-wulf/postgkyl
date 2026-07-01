import builtins
import enum
import shutil
from typing import Annotated, Optional

import matplotlib.pyplot as plt
import typer

from postgkeyll import output
from postgkyl.utils import set_frame


class _Group(str, enum.Enum):
  v0 = "0"
  v1 = "1"
# end


class _LineStyle(str, enum.Enum):
  solid = "solid"
  dashed = "dashed"
  dotted = "dotted"
  dashdot = "dashdot"
# end


def animate(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a tag to plot.")] = None,
    grouptags: Annotated[bool, typer.Option("--grouptags", help="Group coresponding tagged frames.")] = False,
    squeeze: Annotated[bool, typer.Option("--squeeze", "-p", help="Squeeze the components into one panel.")] = False,
    subplots: Annotated[bool, typer.Option("--subplots", "-b", help="Make subplots from multiple datasets.")] = False,
    nSubplotRow: Annotated[Optional[int], typer.Option("--nsubplotrow", help="Manually set the number of rows for subplots.")] = None,
    nSubplotCol: Annotated[Optional[int], typer.Option("--nsubplotcol", help="Manually set the number of columns for subplots.")] = None,
    transpose: Annotated[bool, typer.Option("--transpose", help="Transpose axes.")] = False,
    contour: Annotated[bool, typer.Option("--contour", "-c", help="Make contour plot.")] = False,
    clevels: Annotated[Optional[str], typer.Option("--clevels", help="Specify levels for contours: either integer or start:end:nlevels")] = None,
    quiver: Annotated[bool, typer.Option("--quiver", "-q", help="Make quiver plot.")] = False,
    streamline: Annotated[bool, typer.Option("--streamline", "-l", help="Make streamline plot.")] = False,
    sdensity: Annotated[Optional[float], typer.Option("--sdensity", help="Control density of the streamlines.")] = None,
    arrowstyle: Annotated[Optional[str], typer.Option("--arrowstyle", help="Set the style for streamline arrows.")] = None,
    group: Annotated[Optional[_Group], typer.Option("--group", "-g", help="Switch to group mode.")] = None,
    scatter: Annotated[bool, typer.Option("--scatter", "-s", help="Make scatter plot.")] = False,
    markersize: Annotated[Optional[float], typer.Option("--markersize", help="Set marker size for scatter plots.")] = None,
    linewidth: Annotated[Optional[float], typer.Option("--linewidth", help="Set the linewidth.")] = None,
    linestyle: Annotated[Optional[_LineStyle], typer.Option("--linestyle", help="Set the linestyle.")] = None,
    color: Annotated[Optional[str], typer.Option("--color", help="Set color when available.")] = None,
    style: Annotated[Optional[str], typer.Option("--style", help="Specify Matplotlib style file (default: Postgkyl).")] = None,
    diverging: Annotated[bool, typer.Option("--diverging", "-d", help="Switch to diverging colormesh mode.")] = False,
    arg: Annotated[Optional[str], typer.Option("--arg", help="Additional plotting arguments, e.g., '*--'.")] = None,
    fixaspect: Annotated[bool, typer.Option("--fix-aspect", "-a", help="Enforce the same scaling on both axes.")] = False,
    logx: Annotated[bool, typer.Option("--logx", help="Set x-axis to log scale.")] = False,
    logy: Annotated[bool, typer.Option("--logy", help="Set y-axis to log scale.")] = False,
    logz: Annotated[bool, typer.Option("--logz", help="Set values of 2D plot to log scale.")] = False,
    xshift: Annotated[float, typer.Option("--xshift", help="Value to shift the x-axis.")] = 0.0,
    yshift: Annotated[float, typer.Option("--yshift", help="Value to shift the y-axis.")] = 0.0,
    zshift: Annotated[float, typer.Option("--zshift", help="Value to shift the z-axis.")] = 0.0,
    xscale: Annotated[float, typer.Option("--xscale", help="Value to scale the x-axis.")] = 1.0,
    yscale: Annotated[float, typer.Option("--yscale", help="Value to scale the y-axis.")] = 1.0,
    zscale: Annotated[float, typer.Option("--zscale", help="Value to scale the z-axis.")] = 1.0,
    float: Annotated[bool, typer.Option("--float", help="Choose min/max levels based on current frame (i.e., each frame uses a different color range).")] = False,
    xmax: Annotated[Optional[float], typer.Option("--xmax", help="Set maximal x-value.")] = None,
    xmin: Annotated[Optional[float], typer.Option("--xmin", help="Set minimal x-values.")] = None,
    ymax: Annotated[Optional[float], typer.Option("--ymax", help="Set maximal y-value.")] = None,
    ymin: Annotated[Optional[float], typer.Option("--ymin", help="Set minimal y-values.")] = None,
    zmax: Annotated[Optional[float], typer.Option("--zmax", help="Set maximal z-value.")] = None,
    zmin: Annotated[Optional[float], typer.Option("--zmin", help="Set minimal z-values.")] = None,
    xlim: Annotated[Optional[str], typer.Option("--xlim", help="Set limits for the x-coordinate (lower,upper).")] = None,
    ylim: Annotated[Optional[str], typer.Option("--ylim", help="Set limits for the y-coordinate (lower,upper).")] = None,
    zlim: Annotated[Optional[str], typer.Option("--zlim", help="Set limits for the z-coordinate (lower,upper).")] = None,
    cutoffglobalrange: Annotated[Optional[float], typer.Option("--cutoffglobalrange", "-cogr", help="Specify middle percentile of data extrema to set y/z limits to")] = None,
    legend: Annotated[bool, typer.Option("--legend/--no-legend", help="Show legend.")] = True,
    colorbar: Annotated[bool, typer.Option("--colorbar/--no-colorbar", help="Show colorbar (2D animations), no colorbar improves animation performance")] = True,
    forcelegend: Annotated[bool, typer.Option("--force-legend", help="Force legend even when plotting a single dataset.")] = False,
    xlabel: Annotated[Optional[str], typer.Option("-x", "--xlabel", help="Specify a x-axis label.")] = None,
    ylabel: Annotated[Optional[str], typer.Option("-y", "--ylabel", help="Specify a y-axis label.")] = None,
    clabel: Annotated[Optional[str], typer.Option("--clabel", help="Specify a label for colorbar.")] = None,
    title: Annotated[Optional[str], typer.Option("--title", help="Specify a title.")] = None,
    notitle: Annotated[bool, typer.Option("--notitle", help="Do not show title.")] = False,
    interval: Annotated[Optional[int], typer.Option("-i", "--interval", help="Specify the animation interval.")] = 100,
    save: Annotated[bool, typer.Option("--save", help="Save figure as PNG.")] = False,
    saveas: Annotated[Optional[str], typer.Option("--saveas", help="Name to save the plot as.")] = None,
    fps: Annotated[Optional[int], typer.Option("--fps", help="Specify frames per second for saving.")] = None,
    dpi: Annotated[Optional[int], typer.Option("--dpi", help="DPI (resolution) for output.")] = None,
    edgecolors: Annotated[Optional[str], typer.Option("--edgecolors", "-e", help="Set color for cell edges.")] = None,
    showgrid: Annotated[bool, typer.Option("--showgrid/--no-showgrid", help="Show grid-lines.")] = True,
    collected: Annotated[bool, typer.Option("--collected", help="Animate a dataset that has been collected, i.e. a single dataset with time taken to be the first index.")] = False,
    hashtag: Annotated[bool, typer.Option("--hashtag", help="Turns on the pgkyl hashtag!")] = False,
    show: Annotated[bool, typer.Option("--show/--no-show", help="Turn showing of the plot ON and OFF.")] = True,
    saveframes: Annotated[Optional[str], typer.Option("--saveframes", help="Save individual frames as PNGs.")] = None,
    nproc: Annotated[Optional[int], typer.Option("--nproc", help="Number of parallel processes for frame generation.")] = 1,
    tmpdir: Annotated[Optional[str], typer.Option("--tmpdir", help="Directory to place the temporary directory for parallel frame generation.")] = None,
    figsize: Annotated[Optional[str], typer.Option("--figsize", help="Comma-separated values for x and y size.")] = None,
    multiblock: Annotated[bool, typer.Option("-m", "--multiblock", help="Plots blocks from each frame together")] = False,
):
  """Animate the actively loaded dataset and show resulting plots in a loop.

  Typically, the datasets are loaded using wildcard/regex feature of the -f option to
  the main pgkyl executable.
  """
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  data = ctx.obj.data

  # Accept str or path-like input for --saveas (e.g. a pathlib.Path).
  if kwargs["saveas"]:
    kwargs["saveas"] = str(kwargs["saveas"])
  # end
  supported_exts = (".gif", ".webp", ".apng") + output.VIDEO_EXTS
  if kwargs["saveas"] and not kwargs["saveas"].lower().endswith(supported_exts):
    raise typer.BadParameter(
        "Unsupported output format for --saveas; please use one of: "
        + ", ".join(supported_exts) + ".")
  # end
  # Video containers are written through ffmpeg, which must be on the PATH.
  if kwargs["saveas"] and kwargs["saveas"].lower().endswith(output.VIDEO_EXTS) \
      and shutil.which("ffmpeg") is None:
    raise typer.BadParameter(
        "ffmpeg is required to write " + ", ".join(output.VIDEO_EXTS) + " files but was "
        "not found. Please install ffmpeg or choose a .gif output instead.")
  # end

  # CLI ``--xlim a,b`` convenience overrides the explicit min/max options.
  for lim, lo, hi in (("xlim", "xmin", "xmax"), ("ylim", "ymin", "ymax"),
      ("zlim", "zmin", "zmax")):
    if kwargs[lim]:
      kwargs[lo] = builtins.float(kwargs[lim].split(",")[0])
      kwargs[hi] = builtins.float(kwargs[lim].split(",")[1])
    # end
  # end

  figsize = None
  if kwargs["figsize"]:
    figsize = (int(kwargs["figsize"].split(",")[0]), int(kwargs["figsize"].split(",")[1]))
  # end

  # Everything that is not orchestration state is forwarded to output.animate
  # (its explicit params bind by name; the rest reach the per-frame plot call).
  show_flag = kwargs["show"]
  saving = bool(kwargs["save"] or kwargs["saveas"])
  opts = {k: v for k, v in kwargs.items()
      if k not in ("use", "grouptags", "show", "saveas", "xlim", "ylim", "zlim", "figsize")}
  opts["figsize"] = figsize
  opts["fixed_range"] = not kwargs["float"]
  opts["show"] = False
  opts["legend"] = False  # animate suppresses the legend (re-enabled per tag below)

  if kwargs["grouptags"]:
    # One animation per tag; truncate all to the shortest tag's frame count.
    opts["legend"] = True
    opts["fixed_range"] = True
    tag_list = list(data.tag_iterator(kwargs["use"]))
    min_size = min((int(data.get_num_datasets(tag=t)) for t in tag_list), default=0)
    for t in tag_list:
      frames = [[dat] for dat in data.iterator(t)][:min_size]
      file_name = kwargs["saveas"] or (f"anim_{t:s}.gif" if t is not None else "anim.gif")
      output.animate(frames, saveas=(file_name if saving else None), **opts)
    # end
  elif kwargs["multiblock"]:
    # Group the blocks of each frame together.
    sorted_frame_list = set_frame(ctx)
    frames = [[dat for dat in data.iterator(kwargs["use"]) if dat.ctx["frame"] == frame]
        for frame in sorted_frame_list]
    # Keep all blocks the same colour in 1D so they read as one curve.
    if not opts.get("color") and frames and frames[0][0].get_num_dims() == 1:
      opts["color"] = "tab:blue"
    # end
    file_name = kwargs["saveas"] or "anim.gif"
    output.animate(frames, saveas=(file_name if saving else None), **opts)
  else:
    frames = [[dat] for dat in data.iterator(kwargs["use"])]
    file_name = kwargs["saveas"] or "anim.gif"
    output.animate(frames, saveas=(file_name if saving else None), **opts)
  # end

  # The frame-dump paths render off-screen; only the live FuncAnimation shows.
  if show_flag and not kwargs["saveframes"] and not (kwargs["nproc"] and kwargs["nproc"] > 1):
    plt.show()
  # end
