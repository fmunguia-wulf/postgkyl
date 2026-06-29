import builtins
import os
import shutil
import tempfile
from matplotlib.animation import FuncAnimation, FFMpegWriter
from multiprocessing import Pool
from PIL import Image
import enum
from typing import List, Optional
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import typer
from typing_extensions import Annotated

from postgkyl.utils import verb_print, set_frame
import postgkyl.output.plot


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

# Formats written through ffmpeg (PIL cannot produce these video containers).
VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv")


def _save_frame_worker(args):
  """Worker for parallel frame saving; each process creates its own figure."""
  matplotlib.use("Agg")
  frame_idx, frame_data, kwargs, prefix, dpi, figsize = args
  fig = plt.figure(figsize=figsize)
  _update(0, [frame_data], fig, kwargs)
  plt.savefig(f"{prefix:s}_{frame_idx:d}.png", dpi=dpi)
  plt.close(fig)
# end


def _save_frames(data_list, num_frames, prefix, kwargs, figsize, fig=None):
  """Save frames as PNGs, using parallel workers when nproc > 1."""
  if kwargs["nproc"] > 1:
    args_list = [(i, data_list[i], kwargs, prefix, kwargs["dpi"], figsize)
        for i in range(num_frames)]
    with Pool(kwargs["nproc"]) as pool:
      pool.map(_save_frame_worker, args_list)
    # end
  else:
    for i in range(num_frames):
      _update(i, data_list, fig, kwargs)
      plt.savefig(f"{prefix:s}_{i:d}.png", dpi=kwargs["dpi"])
    # end
  # end
# end


def _compile_movie(frame_files, output_file, fps, duration, ctx):
  """Compile PNG frames into an animation."""
  ext = os.path.splitext(output_file)[1].lower()
  verb_print(ctx,f"Creating {output_file}...")
  if ext in (".gif", ".webp", ".apng"):
    images = [Image.open(f) for f in frame_files]
    images[0].save(
        output_file, save_all=True, append_images=images[1:],
        duration=duration, loop=0, optimize=False,
    )
  elif ext in VIDEO_EXTS:
    # PIL cannot write video containers; use matplotlib's ffmpeg writer.
    # duration is in milliseconds per frame, so fall back to it when fps is unset.
    movie_fps = fps if fps else 1.0e3 / duration
    writer = FFMpegWriter(fps=movie_fps)
    first = Image.open(frame_files[0])
    dpi = 100
    fig = plt.figure(figsize=(first.width / dpi, first.height / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    with writer.saving(fig, output_file, dpi):
      for frame_file in frame_files:
        ax.clear()
        ax.axis("off")
        ax.imshow(Image.open(frame_file))
        writer.grab_frame()
      # end
    # end
    plt.close(fig)
  else:
    raise ValueError(f"Unsupported output format: {ext}")

  verb_print(ctx,f"{output_file} created.")
# end


def _update(frame, data, fig, kwargs):
  fig.clear()
  kwargs["figure"] = fig

  #global range function is called every frame to set scale limits for frame plot
  if kwargs["multiblock"] and kwargs["float"]:
    vmin, vmax, num_dims = globalrange(data[frame], kwargs)
    if num_dims == 1:
      kwargs["ymin"] = vmin
      kwargs["ymax"] = vmax
    else:
      kwargs["zmin"] = vmin
      kwargs["zmax"] = vmax
    # end
  # end

  #main plotting loop
  for i, dat in enumerate(data[frame]):
    kwargs["title"] = ""
    if not kwargs["notitle"]:
      if dat.ctx.get("frame") is not None:
        kwargs["title"] = f"{kwargs['title']:s} frame: {dat.ctx['frame']:d} "
      # end
      if dat.ctx.get("time") is not None:
        kwargs["title"] = f"{kwargs['title']:s} time: {dat.ctx['time']:.4e}"
      # end
    # end

    if i == 0:
      if kwargs.get("arg"):
        im = postgkyl.output.plot(dat, kwargs["arg"], **kwargs)
      else:
        im = postgkyl.output.plot(dat, **kwargs)
      # end
    else:
      kwargs_ncb = kwargs.copy()
      kwargs_ncb["colorbar"] = False
      if kwargs.get("arg"):
        im = postgkyl.output.plot(dat, kwargs["arg"], **kwargs_ncb)
      else:
        im = postgkyl.output.plot(dat, **kwargs_ncb)
      # end
    # end
  # end
  return im
# end

#Finds global minima and maxima for all inputed data objects
#also incorporates cutoffglobalrange
def globalrange(data,kwargs):
  vmin = float("inf")
  vmax = float("-inf")
  v_extrema = np.array([])
  for dat in data:
    num_dims = dat.get_num_dims()
    if num_dims == 1:
      val = dat.get_values()*kwargs["yscale"]
    else:
      val = dat.get_values()*kwargs["zscale"]
    # end
    if vmin > np.nanmin(val):
      vmin = np.nanmin(val)
    if vmax < np.nanmax(val):
      vmax = np.nanmax(val)
    # end
    v_extrema = np.append(v_extrema, np.nanmin(val))
    v_extrema = np.append(v_extrema, np.nanmax(val))
  # end
  v_extrema = np.sort(v_extrema)
  if kwargs["cutoffglobalrange"]:
    boundary = 100 * (1 - kwargs["cutoffglobalrange"]) / 2
    vmax = np.percentile(v_extrema, 100 - boundary)
    vmin = np.percentile(v_extrema, boundary)
    return vmin, vmax, num_dims
  else:
    return vmin, vmax, num_dims
  # end
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
  verb_print(ctx, "Starting animate")
  data = ctx.obj["data"]

  # Accept str or path-like input for --saveas (e.g. a pathlib.Path).
  if kwargs["saveas"]:
    kwargs["saveas"] = str(kwargs["saveas"])
  # end
  supported_exts = (".gif", ".webp", ".apng") + VIDEO_EXTS
  if kwargs["saveas"] and not kwargs["saveas"].lower().endswith(supported_exts):
    raise typer.BadParameter(
        "Unsupported output format for --saveas; please use one of: "
        + ", ".join(supported_exts) + ".")
  # end
  # Video containers are written through ffmpeg, which must be on the PATH.
  if kwargs["saveas"] and kwargs["saveas"].lower().endswith(VIDEO_EXTS) \
      and shutil.which("ffmpeg") is None:
    raise typer.BadParameter(
        "ffmpeg is required to write " + ", ".join(VIDEO_EXTS) + " files but was "
        "not found. Please install ffmpeg or choose a .gif output instead.")
  # end

  if kwargs["xlim"]:
    kwargs["xmin"] = builtins.float(kwargs["xlim"].split(",")[0])
    kwargs["xmax"] = builtins.float(kwargs["xlim"].split(",")[1])
  # end
  if kwargs["ylim"]:
    kwargs["ymin"] = builtins.float(kwargs["ylim"].split(",")[0])
    kwargs["ymax"] = builtins.float(kwargs["ylim"].split(",")[1])
  # end
  if kwargs["zlim"]:
    kwargs["zmin"] = builtins.float(kwargs["zlim"].split(",")[0])
    kwargs["zmax"] = builtins.float(kwargs["zlim"].split(",")[1])
  # end

  if not kwargs["float"] and not kwargs["grouptags"]:
    vmin, vmax, num_dims = globalrange(data.iterator(kwargs["use"]), kwargs)
    if num_dims == 1:
      if kwargs["ymin"] is None:
        kwargs["ymin"] = vmin
      # end
      if kwargs["ymax"] is None:
        kwargs["ymax"] = vmax
      # end
    else:
      if kwargs["zmin"] is None:
        kwargs["zmin"] = vmin
      # end
      if kwargs["zmax"] is None:
        kwargs["zmax"] = vmax
      # end
    # end
  # end

  anims = []
  figs = []
  kwargs["legend"] = False

  figsize = None
  if kwargs["figsize"]:
    figsize = (int(kwargs["figsize"].split(",")[0]), int(kwargs["figsize"].split(",")[1]))
  # end

  # PIL requires duration in miliseconds.
  duration = int(1.0e3 / kwargs["fps"]) if kwargs["fps"] else kwargs["interval"]

  set_figure = False
  min_size = np.nan
  yset = False

  if kwargs["grouptags"]:
    #runs animation for each tag
    for tag in data.tag_iterator(kwargs["use"]):
      num_datasets = int(data.get_num_datasets(tag=tag))
      min_size = int(np.nanmin((min_size, num_datasets)))
    # end

    tag_iterator = list(data.tag_iterator(kwargs["use"]))
    kwargs["legend"] = True
    set_figure = True
    fig_num = int(0)

    for tag in tag_iterator:
      #sets scale for each tag animation
      vmin, vmax, num_dims = globalrange(data.iterator(tag), kwargs)
      if num_dims == 1:
        kwargs["ymin"] = vmin
        kwargs["ymax"] = vmax
        yset = True
      else:
        if yset: #so that ymin,ymax of 1D anim don't affect 2D anim
          kwargs["ymin"] = None
          kwargs["ymax"] = None
        # end
        kwargs["zmin"] = vmin
        kwargs["zmax"] = vmax
      # end

      #creating min list of lists (non-multiblock case)
      data_list = []
      for dat in data.iterator(tag):
        data_list.append([dat])
      # end
      figs.append(plt.figure(fig_num, figsize=figsize))
      fig_num += 1

      num_frames = int(np.nanmin((min_size, len(data_list))))
      file_name = f"anim_{tag:s}.gif" if tag is not None else "anim.gif"
      if kwargs["saveas"]:
        file_name = str(kwargs["saveas"])
      # end

      if kwargs["saveframes"]:
        # Save PNGs, then optionally compile a movie.
        _save_frames(data_list, num_frames, kwargs["saveframes"], kwargs, figsize, figs[-1])
        if kwargs["save"] or kwargs["saveas"]:
          frame_files = [f"{kwargs['saveframes']}_{i}.png" for i in range(num_frames)]
          _compile_movie(frame_files, file_name, kwargs["fps"], duration, ctx)
        # end
        kwargs["show"] = False
      elif kwargs["nproc"] > 1:
        # Parallel: use a temp dir, compile, then clean up.
        with tempfile.TemporaryDirectory(dir=kwargs["tmpdir"]) as tmpdir:
          tmp_prefix = os.path.join(tmpdir, "frame")
          _save_frames(data_list, num_frames, tmp_prefix, kwargs, figsize)
          frame_files = [f"{tmp_prefix}_{i}.png" for i in range(num_frames)]
          _compile_movie(frame_files, file_name, kwargs["fps"], duration, ctx)
        # end
        kwargs["show"] = False
      else:
        anims.append(
            FuncAnimation(figs[-1], _update, num_frames,
                fargs=(data_list, figs[-1], kwargs), interval=kwargs["interval"],
                blit=False)
        )
        if kwargs["save"] or kwargs["saveas"]:
          anims[-1].save(file_name, writer="ffmpeg", fps=kwargs["fps"], dpi=kwargs["dpi"])
        # end
      # end
    # end
  #animation code for multiblock case
  elif kwargs["multiblock"]:

    #set ctx frames for all data objects
    sorted_frame_list = set_frame(ctx)

    #create main list of lists (multiblock case)
    data_list = []
    #organize data objects so each interior list includes blocks from one frame
    for frame in sorted_frame_list:
      frame_data_list = [dat for dat in data.iterator(kwargs["use"]) if dat.ctx["frame"] == frame]
      data_list.append(frame_data_list)
    # end

    figs.append(plt.figure(figsize=figsize))
    #makes default color blue in 1D cases, this prevents blocks from having different colors
    if (not kwargs["color"] and data_list[0][0].get_num_dims() == 1):
      kwargs["color"] = "tab:blue"
    # end

    num_frames = int(np.nanmin((min_size, len(data_list))))
    file_name = kwargs["saveas"] if kwargs["saveas"] else "anim.gif"

    if kwargs["saveframes"]:
      _save_frames(data_list, num_frames, kwargs["saveframes"], kwargs, figsize, figs[-1])
      if kwargs["save"] or kwargs["saveas"]:
        frame_files = [f"{kwargs['saveframes']}_{i}.png" for i in range(num_frames)]
        _compile_movie(frame_files, file_name, kwargs["fps"], duration, ctx)
      # end
      kwargs["show"] = False
    elif kwargs["nproc"] > 1:
      with tempfile.TemporaryDirectory(dir=kwargs["tmpdir"]) as tmpdir:
        tmp_prefix = os.path.join(tmpdir, "frame")
        _save_frames(data_list, num_frames, tmp_prefix, kwargs, figsize)
        frame_files = [f"{tmp_prefix}_{i}.png" for i in range(num_frames)]
        _compile_movie(frame_files, file_name, kwargs["fps"], duration, ctx)
      # end
      kwargs["show"] = False
    else:
      anims.append(
          FuncAnimation(figs[-1], _update, num_frames,
              fargs=(data_list, figs[-1], kwargs), interval=kwargs["interval"],
              blit=False)
      )
      if kwargs["save"] or kwargs["saveas"]:
        anims[-1].save(file_name, writer="ffmpeg", fps=kwargs["fps"], dpi=kwargs["dpi"])
      # end
    # end

  else:

    #create main list of lists (non-multiblock case)
    data_list = []
    for dat in data.iterator(kwargs["use"]):
      data_list.append([dat])
    # end
    if set_figure:
      figs.append(plt.figure(fig_num, figsize=figsize))
    else:
      figs.append(plt.figure(figsize=figsize))
    # end

    num_frames = int(np.nanmin((min_size, len(data_list))))
    file_name = kwargs["saveas"] if kwargs["saveas"] else "anim.gif"

    if kwargs["saveframes"]:
      _save_frames(data_list, num_frames, kwargs["saveframes"], kwargs, figsize, figs[-1])
      if kwargs["save"] or kwargs["saveas"]:
        frame_files = [f"{kwargs['saveframes']}_{i}.png" for i in range(num_frames)]
        _compile_movie(frame_files, file_name, kwargs["fps"], duration, ctx)
      # end
      kwargs["show"] = False
    elif kwargs["nproc"] > 1:
      with tempfile.TemporaryDirectory(dir=kwargs["tmpdir"]) as tmpdir:
        tmp_prefix = os.path.join(tmpdir, "frame")
        _save_frames(data_list, num_frames, tmp_prefix, kwargs, figsize)
        frame_files = [f"{tmp_prefix}_{i}.png" for i in range(num_frames)]
        _compile_movie(frame_files, file_name, kwargs["fps"], duration, ctx)
      # end
      kwargs["show"] = False
    else:
      anims.append(
          FuncAnimation(figs[-1], _update, num_frames,
              fargs=(data_list, figs[-1], kwargs), interval=kwargs["interval"],
              blit=False)
      )
      if kwargs["save"] or kwargs["saveas"]:
        anims[-1].save(file_name, writer="ffmpeg", fps=kwargs["fps"], dpi=kwargs["dpi"])
      # end
    # end
  # end

  if kwargs["show"]:
    plt.show()
  # end
  verb_print(ctx, "Finishing animate")
