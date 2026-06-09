import click
import numpy as np
import matplotlib.pyplot as plt

from postgkyl.data import GData, GInterpModal
from postgkyl.utils import verb_print
import postgkyl.utils.gk_utils as gku

def get_interp_data_from_gdata(gdata_in, comp_in):
  # Get interpolated data given the GData object.
  poly_order = gdata_in.ctx["poly_order"]
  basis_type = gdata_in.ctx["basis_type"]
  if basis_type == "serendipity":
    basis_type = "ms"
  # end
  pg_interp = GInterpModal(gdata_in, poly_order, basis_type)
  x_out, data_out = pg_interp.interpolate(comp_in)
  for i in range(len(x_out)):
    x_out[i] = np.squeeze(x_out[i])
  # end
  data_out = np.squeeze(data_out)
  return x_out, data_out

@click.command()
@click.option("--quantity", "-q", required=True, type=click.STRING, default=None,
  help="Quantity to plot (a file or one of the default names).")
@click.option("--name", "-n", type=click.STRING, default=None,
  help="Simulation name (also the file prefix, e.g. gk_sheath_1x2v_p1).")
@click.option("--comp", "-c", default=0,
  help="Component in quantity.")
@click.option("--species", "-s", type=click.STRING, default=None,
  help="Species name.")
@click.option("--frame", "-f", type=click.STRING,
  help="Frame number, comma separated values, or range. Use ':' for all frames and 'start:stop[:step]' for ranges.")
@click.option("--path", "-p", type=click.STRING, default='./.',
  help="Path to simulation data.")
@click.option("--multib", "-m", type=click.STRING, is_flag=False, flag_value="-1", default="-10",
  help="Multiblock. Optional: pass block indices as comma-separated list or slice (start:stop:step). If no indices are given, all blocks are used.")
@click.option("--wall_file", type=click.STRING, default=None,
  help="Vacuum vessel wall (.csv format).")
@click.option("--xlim", default=None, type=click.STRING,
  help="Set limits for the x-coordinate (lower,upper)")
@click.option("--ylim", default=None, type=click.STRING,
  help="Set limits for the y-coordinate (lower,upper).")
@click.option("--xlabel", type=click.STRING, default="R (m)",
  help="Label for the x axis.")
@click.option("--ylabel", type=click.STRING, default="Z (m)",
  help="Label for the y axis.")
@click.option("--zlabel", type=click.STRING, default=None,
  help="Label for the color bar.")
@click.option("--title", type=click.STRING, default=None,
  help="Title for the figure.")
@click.option("--saveas", type=click.STRING, default=None,
  help="Name of figure file.")
@click.option("--no_show", is_flag=True, default=False,
  help="Suppreses showing the figure.")
@click.pass_context
def gk_rz(ctx, **kwargs):
  """
  \b
  Gyrokinetics: Plot a quantity from a 2x or 3x simulation on the R-Z plane.
  The quantity (-q) can be specified as a file name, e.g.
    - <simulation_name>-<species_name>_M0_?.gkyl
    - <simulation_name>_b?-<species_name>_M0_?.gkyl
  where ? is either a number or *, or one of the default names:
    den, upar, tpar, tperp, temp, qpar, qperp,
    m0, m1, m2par, m2perp, m2, m3par, m3perp, m3,
    phi, bmag, jacobgeo
  in combination with the simulation name (-n) and frame (-f) and, if needed,
  species (-s).

  \b
  The default assumes these are in the current directory.
  Alternatively, the path to the files can be specified.

  \b
  If simulation is multiblock, you can:
    1) Pass * for the block index in the file name, OR
    2) Use --multib/-m to specify desired blocks (-m w/o a number plots all blocks).

  NOTE: this command cannot be combined with other postgkyl commands.
  """

  data = ctx.obj["data"]  # Data stack.
  ctx.obj["plot_handles"] = {}  # Handles to objects in plot.
  handles = ctx.obj["plot_handles"]

  kwargs["path"] = kwargs["path"] + '/' # For safety.

  if (kwargs["quantity"][-len(gku.file_fmt):] == gku.file_fmt):
    # Quantity is a file (i.e. ends in .gkyl).
    # Extract the simulation name if it hasn't been provided. If it has, make
    # sure it matches.
    quantity_sim_name = kwargs["quantity"].split('-', 1)[0]
    if kwargs["name"] != None:
      if quantity_sim_name != kwargs["name"]:
        print("gk_rz: Error. Input 'quantity' is a file but the simulation name doesn't match the 'name' input.")
        os.exit(1)
    else:
      kwargs["name"] = quantity_sim_name

    sim_name_len = len(kwargs["name"])

    if kwargs["quantity"][0] == "/":
      # Absolute path included. Don't append path.
      file_path_prefix = kwargs["quantity"]
    else:
      file_path_prefix = kwargs["path"] + kwargs["quantity"] # File name root including path.
    #end
#  else:
#    # Quantity is not a file, so assemble the file name from other inputs.
#    quant_lc = kwargs["quantity"].lower()
#    if quant_lc in gku.quant_attributes.keys():
#      # Loop through files that may have this quantity.
#      quant_files = gku.quant_attributes[quant_lc]["files"]
#      for fn in files: 
#        # Check if file exists.
#    else:
#      print("--quantity/-q: quantity name not valid.")
#      os.exit(1)
  # end

  verb_print(ctx, "Plotting " + file_path_prefix)

  # Get the c2p file.
  mapc2p_file = kwargs["name"] + "-mapc2p_deflated" + gku.file_fmt
 
  print("file_path_prefix = ",file_path_prefix)
  grid, vals, gdat = gku.read_gfile(file_path_prefix, mapc2p=mapc2p_file) 
  grid_int, vals_int = get_interp_data_from_gdata(gdat, kwargs["comp"]) 

  #[ Prepare figure.
  fig_prop = (6.0, 6.0)
  ax_pos   = [[0.15, 0.1, 0.65, 0.85],]
  cbax_pos =  [0.82, 0.1, 0.02, 0.85]
  fig_h    = plt.figure(figsize=fig_prop)
  ax_h     = [fig_h.add_axes(pos) for pos in ax_pos]
  cbax_h   = fig_h.add_axes(cbax_pos)

  ax_h[0].set_aspect('equal')

  #[ Plot data
  hpla = list()
  hpla.append(ax_h[0].pcolormesh(grid_int[0], grid_int[1], vals_int, cmap='inferno'))

  if kwargs["wall_file"]:
    # Plot the wall.
    if kwargs["wall_file"][0] == "/":
      # Absolute path included in node file. Don't append path.
      wall_file = kwargs["wall_file"]
    else:
      wall_file = kwargs["path"] + kwargs["wall_file"]
    #end

    wall_data = np.loadtxt(open(wall_file),delimiter=',')
    wall_h = ax_h[0].plot(wall_data[:,0],wall_data[:,1],color="grey")
    handles["wall"] = wall_h
  # end

  hcba = plt.colorbar(hpla[0], ax=ax_h[0], cax=cbax_h)
  hcba.ax.tick_params(labelsize=gku.tick_font_size)
  hcba.set_label(kwargs["zlabel"], rotation=90, labelpad=0, fontsize=gku.colorbar_label_font_size)
  hcba.ax.yaxis.get_offset_text().set_fontsize(gku.tick_font_size)

  ax_h[0].set_xlabel(kwargs["xlabel"], fontsize=gku.xy_label_font_size)
  ax_h[0].xaxis.get_offset_text().set_size(gku.tick_font_size)
  ax_h[0].set_ylabel(kwargs["ylabel"], fontsize=gku.xy_label_font_size, labelpad=-3)
  ax_h[0].yaxis.get_offset_text().set_size(gku.tick_font_size)
  gku.set_tick_font_size(ax_h[0],gku.tick_font_size)

  if kwargs["saveas"]:
    plt.savefig(kwargs["saveas"])
  # end

  if not kwargs["no_show"]:
    plt.show()
  # end

  verb_print(ctx, "Finishing GK R-Z plot.")
