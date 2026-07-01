from matplotlib.animation import FuncAnimation
import math
import matplotlib.pyplot as plt
import numpy as np
import typer
from typing import Annotated, Optional




def _update(i, ax, ctx, leap, vel, xmin, xmax, ymin, ymax, zmin, zmax, tag):
  colors = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]

  s = 0
  plt.cla()
  # for s, dat in ctx.obj.data.iterator(tag, emum=True):
  for dat in ctx.obj.data.iterator(tag):
    time = dat.get_grid()[0]
    coords = dat.get_values()
    t_idx = int(i * leap)

    if xmin is not None:
      x = np.where(coords[:, 0] > xmin, coords[:, 0], np.nan)
    else:
      x = coords[:, 0]
    # end
    if xmax is not None:
      x = np.where(x < xmax, x, np.nan)
    # end
    if ymin is not None:
      y = np.where(coords[:, 1] > ymin, coords[:, 1], np.nan)
    else:
      y = coords[:, 1]
    # end
    if ymax is not None:
      y = np.where(y < ymax, y, np.nan)
    # end
    if zmin is not None:
      z = np.where(coords[:, 2] > zmin, coords[:, 2], np.nan)
    else:
      z = coords[:, 2]
    # end
    if zmax is not None:
      z = np.where(z < zmax, z, np.nan)
    # end

    ax.plot(x, y, z, color=colors[s % 10])
    ax.scatter(x[t_idx], y[t_idx], z[t_idx], color=colors[s % 10])
    if vel and dat.get_num_comps() == 6:
      if t_idx + leap >= len(time):
        dt = time[-1] - time[t_idx]
      else:
        dt = time[int(t_idx + leap)] - time[t_idx]
      # end
      dx = coords[i, 3] * dt
      dy = coords[i, 4] * dt
      dz = coords[i, 5] * dt
      ax.plot([x[t_idx], x[t_idx] + dx], [y[t_idx], y[t_idx] + dy], [z[t_idx], z[t_idx] + dz],
          color=colors[s % 10])
    # end
    s += 1
  # end
  plt.title(f"T: {time[t_idx]:.4e}")
  ax.set_xlabel("$z_0$")
  ax.set_ylabel("$z_1$")
  ax.set_zlabel("$z_2$")
  ax.set_xlim3d(xmin, xmax)
  ax.set_ylim3d(ymin, ymax)
  ax.set_zlim3d(zmin, zmax)


def trajectory(
    ctx: typer.Context,
    fixaspect: Annotated[bool, typer.Option("--fix-aspect", help="Enforce the same scaling on both axes.")] = False,
    show: Annotated[bool, typer.Option("--show/--no-show", help="Turn showing of the plot ON and OFF (default: ON).")] = True,
    interval: Annotated[Optional[int], typer.Option("-i", "--interval", help="Specify the animation interval.")] = 100,
    save: Annotated[bool, typer.Option("--save", help="Save figure as PNG.")] = False,
    velocity: Annotated[bool, typer.Option("--velocity/--no-velocity", help="Plot velocity vectors.")] = True,
    saveas: Annotated[Optional[str], typer.Option("--saveas", help="Name to save the plot as.")] = None,
    elevation: Annotated[Optional[float], typer.Option("-e", "--elevation", help="Set elevation.")] = None,
    azimuth: Annotated[Optional[float], typer.Option("-a", "--azimuth", help="Set azimuth.")] = None,
    numframes: Annotated[Optional[int], typer.Option("-n", "--numframes", help="Set number of frames for the animation.")] = None,
    xmin: Annotated[Optional[float], typer.Option("--xmin", help="Minimum value of the x-coordinate")] = None,
    xmax: Annotated[Optional[float], typer.Option("--xmax", help="Maximum value of the x-coordinate")] = None,
    ymin: Annotated[Optional[float], typer.Option("--ymin", help="Minimum value of the y-coordinate")] = None,
    ymax: Annotated[Optional[float], typer.Option("--ymax", help="Maximum value of the y-coordinate")] = None,
    zmin: Annotated[Optional[float], typer.Option("--zmin", help="Minimum value of the z-coordinate")] = None,
    zmax: Annotated[Optional[float], typer.Option("--zmax", help="Maximum value of the z-coordinate")] = None,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
):
  """Animate a particle trajectory."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  data = ctx.obj.data

  tags = list(data.tag_iterator(kwargs["use"]))
  tag = tags[0]
  if len(tags) > 1:
    ctx.fail(typer.echo(f"'trajectory' supports only one 'tag', was provided {len(tags):d}",
        color="red"))
  # end

  fig = plt.figure()
  ax = fig.add_subplot(111, projection="3d")
  kwargs["figure"] = fig
  kwargs["legend"] = False

  dat = ctx.obj.data.get_dataset(0, tag)
  num_pos = dat.get_num_cells()[0]

  jump = 1
  if kwargs.get("numframes"):
    jump = int(math.floor(num_pos / kwargs["numframes"]))
    num_pos = int(kwargs["numframes"])
  # end

  anim = FuncAnimation(fig, _update, num_pos,
      fargs=(ax, ctx, jump, kwargs["velocity"], kwargs["xmin"], kwargs["xmax"], kwargs["ymin"],
          kwargs["ymax"], kwargs["zmin"], kwargs["zmax"], tag),
      interval=kwargs["interval"])

  ax.view_init(elev=kwargs["elevation"], azim=kwargs["azimuth"])

  if kwargs["fixaspect"]:
    plt.setp(ax, aspect=1.0)
  # end

  f_name = "anim.mp4"
  if kwargs["saveas"]:
    f_name = str(kwargs["saveas"])
  # end
  if kwargs["save"] or kwargs["saveas"]:
    anim.save(f_name, writer="ffmpeg")
  # end

  if kwargs["show"]:
    plt.show()
  # end
