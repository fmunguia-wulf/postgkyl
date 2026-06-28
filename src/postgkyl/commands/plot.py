import click
import matplotlib.pyplot as plt
import numpy as np

from postgkyl.utils import verb_print
import postgkyl.output.plot


@click.command()
@click.option("--use", "-u", default=None, help="Specify the tag to plot.")
@click.option("--figure", "-f", default=None,
    help="Specify figure to plot in; either number or 'dataset'.")
@click.option("--squeeze", is_flag=True, help="Squeeze the components into one panel.")
@click.option("--subplots", "-b", is_flag=True, help="Make subplots from multiple datasets.")
@click.option("--nsubplotrow", "num_subplot_row", type=click.INT,
    help="Manually set the number of rows for subplots.")
@click.option("--nsubplotcol", "num_subplot_col", type=click.INT,
    help="Manually set the number of columns for subplots.")
@click.option("--transpose", is_flag=True, help="Transpose axes.")
@click.option("-c", "--contour", is_flag=True, help="Make contour plot.")
@click.option("--clevels", type=click.STRING,
    help="Specify levels for contours: comma-separated level values or start:end:nlevels.")
@click.option("--cnlevels", type=click.INT, help="Specify the number of levels for contours.")
@click.option("--contlabel", "cont_label", is_flag=True, help="Add labels to contours")
@click.option("-q", "--quiver", is_flag=True, help="Make quiver plot.")
@click.option("-l", "--streamline", is_flag=True, help="Make streamline plot.")
@click.option("--sdensity", type=click.INT, default=1, help="Control density of the streamlines.")
@click.option("--arrowstyle", type=click.STRING, help="Set the style for streamline arrows.")
@click.option("--lineouts", type=click.Choice(["0", "1"]), help="Switch to lineouts mode.")
@click.option("-s", "--scatter", is_flag=True, help="Make scatter plot.")
@click.option("--markersize", type=click.FLOAT, help="Set marker size for scatter plots.")
@click.option("--linewidth", type=click.FLOAT, help="Set the linewidth.")
@click.option("--linestyle", type=click.Choice(["solid", "dashed", "dotted", "dashdot"]),
    help="Set the linestyle.")
@click.option("--style", help="Specify Matplotlib style file (default: Postgkyl).")
@click.option("-d", "--diverging", is_flag=True, help="Switch to diverging color map.")
@click.option("--arg", type=click.STRING, default="",
    help="Additional plotting arguments, e.g., '*--'.")
@click.option("--fix-aspect", "-a", "fixaspect", is_flag=True,
    help="Enforce the same scaling on both axes.")
@click.option("--aspect", default=None, help="Specify the scaling ratio.")
@click.option("--logx", is_flag=True, help="Set x-axis to log scale.")
@click.option("--logy", is_flag=True, help="Set y-axis to log scale.")
@click.option("--logz", is_flag=True, help="Set values of 2D plot to log scale.")
@click.option("--xshift", default=0.0, type=click.FLOAT, show_default=True,
    help="Value to shift the x-axis.")
@click.option("--yshift", default=0.0, type=click.FLOAT, show_default=True,
    help="Value to shift the y-axis.")
@click.option("--zshift", default=0.0, type=click.FLOAT, show_default=True,
    help="Value to shift the z-axis.")
@click.option("--xscale", default=1.0, type=click.FLOAT, show_default=True,
    help="Value to scale the x-axis.")
@click.option("--yscale", default=1.0, type=click.FLOAT, show_default=True,
    help="Value to scale the y-axis.")
@click.option("--zscale", default=1.0, type=click.FLOAT, show_default=True,
    help="Value to scale the z-axis (default: 1.0).")
@click.option("--xmax", default=None, type=click.FLOAT, help="Set maximal x-value.")
@click.option("--xmin", default=None, type=click.FLOAT, help="Set minimal x-values.")
@click.option("--ymax", default=None, type=click.FLOAT, help="Set maximal y-value.")
@click.option("--ymin", default=None, type=click.FLOAT, help="Set minimal y-values.")
@click.option("--zmax", default=None, type=click.FLOAT, help="Set maximal z-value.")
@click.option("--zmin", default=None, type=click.FLOAT, help="Set minimal z-values.")
@click.option("--xlim", default=None, type=click.STRING,
    help="Set limits for the x-coordinate (lower,upper)")
@click.option("--ylim", default=None, type=click.STRING,
    help="Set limits for the y-coordinate (lower,upper).")
@click.option("--zlim", default=None, type=click.STRING,
    help="Set limits for the z-coordinate (lower,upper).")
@click.option("--relax", is_flag=True, help="Relax the stringent x axis limits for 1D plots.")
@click.option("--globalrange", "-r", is_flag=True, help="Make uniform extends across datasets.")
@click.option("--cutoffglobalrange", "-cogr", default=None, type=click.FLOAT,
              help="Set custom limit for uniform across datasets")
@click.option("--legend", default=None, type=click.STRING,
    help="If specified, comma-separated legend labels (e.g., 'a,b,c').")
@click.option("--no-legend", is_flag=True, help="Hide legend.")
@click.option("--force-legend", "forcelegend", is_flag=True,
    help="Force legend even when plotting a single dataset.")
@click.option("--color", type=click.STRING, help="Set color when available.")
@click.option("-x", "--xlabel", type=click.STRING, help="Specify a x-axis label.")
@click.option("-y", "--ylabel", type=click.STRING, help="Specify a y-axis label.")
@click.option("--clabel", type=click.STRING, help="Specify a label for colorbar.")
@click.option("--title", type=click.STRING, help="Specify a title.")
@click.option("--subplot-titles", type=click.STRING, help="Comma-separated titles for each subplot. e.g. --subplot-titles 'Title1,Title2,Title3'")
@click.option("--subplot-xlabels", type=click.STRING, help="Comma-separated x-axis labels for each subplot. e.g. --subplot-xlabels 'X1,X2,X3'")
@click.option("--subplot-ylabels", type=click.STRING, help="Comma-separated y-axis labels for each subplot. e.g. --subplot-ylabels 'Y1,Y2,Y3'")
@click.option("--save", is_flag=True, help="Save figure as PNG file.")
@click.option("--saveas", type=click.STRING, default=None, help="Name of figure file.")
@click.option("--dpi", type=click.INT, default=200, help="DPI (resolution) for output.")
@click.option("-e", "--edgecolors", type=click.STRING,
    help="Set color for cell edges to show grid outline.")
@click.option("--showgrid/--no-showgrid", default=True, help="Show grid-lines.")
@click.option("--xkcd", is_flag=True, help="Turns on the xkcd style!")
@click.option("--hashtag", is_flag=True, help="Turns on the pgkyl hashtag!")
@click.option("--show/--no-show", default=True,
    help="Turn showing of the plot ON and OFF.")
@click.option("--figsize", help="Comma-separated values for x and y size.")
@click.option("--saveframes", type=click.STRING,
    help="Save individual frames as PNGS instead of an opening them")
@click.option("--jet", is_flag=True, help="Turn colormap to jet for comparison with literature.")
@click.option("--cmap", type=click.STRING, default=None,
    help="Override default colormap with a valid matplotlib cmap.")
@click.option("-m", "--multiblock", is_flag=True, default=False)
@click.pass_context
def plot(ctx, **kwargs):
  """Plot active datasets, optionally displaying the plot and/or saving it to PNG files.

  Plot labels can use a sub-set of LaTeX math commands placed between dollar ($) signs.
  """
  verb_print(ctx, "Starting plot")

  # CLI-supplied context that the shared plot_datasets layer needs.
  kwargs["rcParams"] = ctx.obj["rcParams"]
  kwargs["batch_mode"] = ctx.obj.get("batch_mode", False)
  kwargs["saveframes_prefix"] = ctx.obj.get("saveframes_prefix")

  datasets = list(ctx.obj["data"].iterator(kwargs.get("use")))
  postgkyl.output.plot_datasets(datasets, **kwargs)

  verb_print(ctx, "Finishing plot")
