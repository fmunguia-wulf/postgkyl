import enum
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import typer
from typing_extensions import Annotated

from postgkyl.utils import verb_print
import postgkyl.output.plot


class _Lineouts(str, enum.Enum):
  v0 = "0"
  v1 = "1"
# end


class _LineStyle(str, enum.Enum):
  solid = "solid"
  dashed = "dashed"
  dotted = "dotted"
  dashdot = "dashdot"
# end


def plot(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify the tag to plot.")] = None,
    figure: Annotated[Optional[str], typer.Option("--figure", "-f", help="Specify figure to plot in; either number or 'dataset'.")] = None,
    squeeze: Annotated[bool, typer.Option("--squeeze", help="Squeeze the components into one panel.")] = False,
    subplots: Annotated[bool, typer.Option("--subplots", "-b", help="Make subplots from multiple datasets.")] = False,
    num_subplot_row: Annotated[Optional[int], typer.Option("--nsubplotrow", help="Manually set the number of rows for subplots.")] = None,
    num_subplot_col: Annotated[Optional[int], typer.Option("--nsubplotcol", help="Manually set the number of columns for subplots.")] = None,
    transpose: Annotated[bool, typer.Option("--transpose", help="Transpose axes.")] = False,
    contour: Annotated[bool, typer.Option("-c", "--contour", help="Make contour plot.")] = False,
    clevels: Annotated[Optional[str], typer.Option("--clevels", help="Specify levels for contours: comma-separated level values or start:end:nlevels.")] = None,
    cnlevels: Annotated[Optional[int], typer.Option("--cnlevels", help="Specify the number of levels for contours.")] = None,
    cont_label: Annotated[bool, typer.Option("--contlabel", help="Add labels to contours")] = False,
    quiver: Annotated[bool, typer.Option("-q", "--quiver", help="Make quiver plot.")] = False,
    streamline: Annotated[bool, typer.Option("-l", "--streamline", help="Make streamline plot.")] = False,
    sdensity: Annotated[int, typer.Option("--sdensity", help="Control density of the streamlines.")] = 1,
    arrowstyle: Annotated[Optional[str], typer.Option("--arrowstyle", help="Set the style for streamline arrows.")] = None,
    lineouts: Annotated[Optional[_Lineouts], typer.Option("--lineouts", help="Switch to lineouts mode.")] = None,
    scatter: Annotated[bool, typer.Option("-s", "--scatter", help="Make scatter plot.")] = False,
    markersize: Annotated[Optional[float], typer.Option("--markersize", help="Set marker size for scatter plots.")] = None,
    linewidth: Annotated[Optional[float], typer.Option("--linewidth", help="Set the linewidth.")] = None,
    linestyle: Annotated[Optional[_LineStyle], typer.Option("--linestyle", help="Set the linestyle.")] = None,
    style: Annotated[Optional[str], typer.Option("--style", help="Specify Matplotlib style file (default: Postgkyl).")] = None,
    diverging: Annotated[bool, typer.Option("-d", "--diverging", help="Switch to diverging color map.")] = False,
    arg: Annotated[Optional[str], typer.Option("--arg", help="Additional plotting arguments, e.g., '*--'.")] = "",
    fixaspect: Annotated[bool, typer.Option("--fix-aspect", "-a", help="Enforce the same scaling on both axes.")] = False,
    aspect: Annotated[Optional[str], typer.Option("--aspect", help="Specify the scaling ratio.")] = None,
    logx: Annotated[bool, typer.Option("--logx", help="Set x-axis to log scale.")] = False,
    logy: Annotated[bool, typer.Option("--logy", help="Set y-axis to log scale.")] = False,
    logz: Annotated[bool, typer.Option("--logz", help="Set values of 2D plot to log scale.")] = False,
    xshift: Annotated[float, typer.Option("--xshift", help="Value to shift the x-axis.")] = 0.0,
    yshift: Annotated[float, typer.Option("--yshift", help="Value to shift the y-axis.")] = 0.0,
    zshift: Annotated[float, typer.Option("--zshift", help="Value to shift the z-axis.")] = 0.0,
    xscale: Annotated[float, typer.Option("--xscale", help="Value to scale the x-axis.")] = 1.0,
    yscale: Annotated[float, typer.Option("--yscale", help="Value to scale the y-axis.")] = 1.0,
    zscale: Annotated[float, typer.Option("--zscale", help="Value to scale the z-axis (default: 1.0).")] = 1.0,
    xmax: Annotated[Optional[float], typer.Option("--xmax", help="Set maximal x-value.")] = None,
    xmin: Annotated[Optional[float], typer.Option("--xmin", help="Set minimal x-values.")] = None,
    ymax: Annotated[Optional[float], typer.Option("--ymax", help="Set maximal y-value.")] = None,
    ymin: Annotated[Optional[float], typer.Option("--ymin", help="Set minimal y-values.")] = None,
    zmax: Annotated[Optional[float], typer.Option("--zmax", help="Set maximal z-value.")] = None,
    zmin: Annotated[Optional[float], typer.Option("--zmin", help="Set minimal z-values.")] = None,
    xlim: Annotated[Optional[str], typer.Option("--xlim", help="Set limits for the x-coordinate (lower,upper)")] = None,
    ylim: Annotated[Optional[str], typer.Option("--ylim", help="Set limits for the y-coordinate (lower,upper).")] = None,
    zlim: Annotated[Optional[str], typer.Option("--zlim", help="Set limits for the z-coordinate (lower,upper).")] = None,
    relax: Annotated[bool, typer.Option("--relax", help="Relax the stringent x axis limits for 1D plots.")] = False,
    globalrange: Annotated[bool, typer.Option("--globalrange", "-r", help="Make uniform extends across datasets.")] = False,
    cutoffglobalrange: Annotated[Optional[float], typer.Option("--cutoffglobalrange", "-cogr", help="Set custom limit for uniform across datasets")] = None,
    legend: Annotated[Optional[str], typer.Option("--legend", help="If specified, comma-separated legend labels (e.g., 'a,b,c').")] = None,
    no_legend: Annotated[bool, typer.Option("--no-legend", help="Hide legend.")] = False,
    legend_axis: Annotated[Optional[int], typer.Option("--legend-axis", help="Restrict the legend to the subplot with this flat index (0-based).")] = None,
    forcelegend: Annotated[bool, typer.Option("--force-legend", help="Force legend even when plotting a single dataset.")] = False,
    color: Annotated[Optional[str], typer.Option("--color", help="Set color when available.")] = None,
    xlabel: Annotated[Optional[str], typer.Option("-x", "--xlabel", help="Specify a x-axis label.")] = None,
    ylabel: Annotated[Optional[str], typer.Option("-y", "--ylabel", help="Specify a y-axis label.")] = None,
    clabel: Annotated[Optional[str], typer.Option("--clabel", help="Specify a label for colorbar.")] = None,
    title: Annotated[Optional[str], typer.Option("--title", help="Specify a title.")] = None,
    subplot_titles: Annotated[Optional[str], typer.Option("--subplot-titles", help="Comma-separated titles for each subplot. e.g. --subplot-titles 'Title1,Title2,Title3'")] = None,
    subplot_xlabels: Annotated[Optional[str], typer.Option("--subplot-xlabels", help="Comma-separated x-axis labels for each subplot. e.g. --subplot-xlabels 'X1,X2,X3'")] = None,
    subplot_ylabels: Annotated[Optional[str], typer.Option("--subplot-ylabels", help="Comma-separated y-axis labels for each subplot. e.g. --subplot-ylabels 'Y1,Y2,Y3'")] = None,
    save: Annotated[bool, typer.Option("--save", help="Save figure as PNG file.")] = False,
    saveas: Annotated[Optional[str], typer.Option("--saveas", help="Name of figure file.")] = None,
    dpi: Annotated[Optional[int], typer.Option("--dpi", help="DPI (resolution) for output.")] = 200,
    edgecolors: Annotated[Optional[str], typer.Option("-e", "--edgecolors", help="Set color for cell edges to show grid outline.")] = None,
    showgrid: Annotated[bool, typer.Option("--showgrid/--no-showgrid", help="Show grid-lines.")] = True,
    xkcd: Annotated[bool, typer.Option("--xkcd", help="Turns on the xkcd style!")] = False,
    hashtag: Annotated[bool, typer.Option("--hashtag", help="Turns on the pgkyl hashtag!")] = False,
    show: Annotated[bool, typer.Option("--show/--no-show", help="Turn showing of the plot ON and OFF.")] = True,
    figsize: Annotated[Optional[str], typer.Option("--figsize", help="Comma-separated values for x and y size.")] = None,
    saveframes: Annotated[Optional[str], typer.Option("--saveframes", help="Save individual frames as PNGS instead of an opening them")] = None,
    jet: Annotated[bool, typer.Option("--jet", help="Turn colormap to jet for comparison with literature.")] = False,
    cmap: Annotated[Optional[str], typer.Option("--cmap", help="Override default colormap with a valid matplotlib cmap.")] = None,
    multiblock: Annotated[bool, typer.Option("-m", "--multiblock")] = False,
):
  """Plot active datasets, optionally displaying the plot and/or saving it to PNG files.

  Plot labels can use a sub-set of LaTeX math commands placed between dollar ($) signs.
  """
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting plot")

  # CLI-supplied context that the shared plot_datasets layer needs.
  kwargs["rcParams"] = ctx.obj["rcParams"]
  kwargs["batch_mode"] = ctx.obj.get("batch_mode", False)
  kwargs["saveframes_prefix"] = ctx.obj.get("saveframes_prefix")

  datasets = list(ctx.obj["data"].iterator(kwargs.get("use")))
  postgkyl.output.plot_datasets(datasets, **kwargs)

  verb_print(ctx, "Finishing plot")
