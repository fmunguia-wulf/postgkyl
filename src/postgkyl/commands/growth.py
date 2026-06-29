from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt
import matplotlib.pyplot as plt
import numpy as np
import os

from postgkyl.data import GData
import postgkyl.tools
from postgkyl.utils import verb_print


def growth(
    ctx: typer.Context,
    use: opt.Use = None,
    guess: Annotated[Optional[str], typer.Option("-g", "--guess", help="Specify comma-separated initial guess.")] = None,
    minn: Annotated[Optional[int], typer.Option("--minn", help="Set minimal number of points to fit.")] = None,
    dataset: Annotated[bool, typer.Option("-d", "--dataset", help="Create a new dataset with fitted exponential.")] = False,
    instantaneous: Annotated[bool, typer.Option("-i", "--instantaneous", help="Plot instantaneous growth rate vs time.")] = False,
    dir: Annotated[Optional[int], typer.Option("--dir", help="Choose direction for multi-D data.")] = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Attempts to compute growth rate (i.e. fit e^(2x)) from DynVector data.

  the DynVector is typically an integrated quantity like electric or magnetic field
  energy.
  """
  data = ctx.obj.data

  for dat in data.iterator(use):
    time = dat.get_grid()
    values = dat.get_values()
    num_dims = len(np.array(values.shape).squeeze())

    growth_rates = np.zeros(1)
    ks = np.zeros(1)
    if num_dims == 2:
      if dir == 0:
        growth_rates = np.zeros(values.shape[1])
        ks = np.zeros(values.shape[1])
      elif dir == 1:
        growth_rates = np.zeros(values.shape[0])
        ks = np.zeros(values.shape[0])
      # end
    # end

    for idx in range(len(growth_rates)):
      p0 = guess
      if guess:
        parts = guess.split(",")
        p0 = (float(parts[0]), float(parts[1]))
      # end

      x = time[0]
      if dir == 1:
        x = time[1]

      y = values[..., 0].squeeze()
      if dir == 0:
        y = values[:, idx, 0].squeeze()
      elif dir == 1:
        y = values[idx, :, 0].squeeze()
      # end

      best_params, _, _ = postgkyl.tools.fit_growth(x, y, min_N=minn, p0=p0)

      if dataset:
        out = GData(tag="growth", label="Fit",
            comp_grid=ctx.obj.compgrid, ctx=dat.ctx)
        t = 0.5 * (time[0][:-1] + time[0][1:])
        out_val = postgkyl.tools.exp2(t, *best_params)
        out.push([time[0]], out_val[..., np.newaxis])
        data.add(out)
      # end

      if instantaneous:
        verb_print(ctx, "growth: Plotting instantaneous growth rate")
        gammas = []
        for i in range(1, len(time[0]) - 1):
          gamma = (values[i + 1, 0] - values[i - 1, 0]) / (2*values[i, 0]*(time[0][i + 1] - time[0][i - 1]))
          gammas.append(gamma)

          plt.style.use(f"{os.path.dirname(os.path.realpath(__file__)):s}/../output/postgkyl.mplstyle")
          _, ax = plt.subplots()
          ax.plot(time[0][1:-1], gammas)
          # ax.set_autoscale_on(False)
          ax.grid(True)
          plt.show()
        # end
      # end

      growth_rates[idx] = best_params[1]
      ks[idx] = idx
    # end

    if tag:
      out = GData(tag=tag, label=label,
          comp_grid=ctx.obj.compgrid, ctx=dat.ctx)
      out.push([ks], growth_rates[..., np.newaxis])
      data.add(out)
    # end
  # end
