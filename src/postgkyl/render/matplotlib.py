"""Matplotlib rendering backend.

Imports only ``core``/``numerics`` (a backend the fluent layer uses); it never
imports ``ops``/``api``. Supports 1-D line plots and 2-D pcolormesh, one
sub-panel per component, with multiple datasets overlaid on 1-D axes.
"""

from __future__ import annotations

import numpy as np

from postgkyl.core import flatten_datasets


def _centers(edges: np.ndarray) -> np.ndarray:
  return 0.5 * (edges[:-1] + edges[1:])


def plot(*datasets, title: str | None = None, labels=None,
    figsize=None, show: bool = True, save: str | None = None):
  """Plot one or more datasets and return the matplotlib figure.

  Accepts ``plot(a, b)`` or ``plot([a, b])``. The first dataset sets the layout
  (dimensionality and component count); the rest are overlaid (1-D only).

  Args:
    datasets: ``GDataState`` (or subclass) instances, or lists thereof.
    title: optional figure title.
    labels: optional per-dataset legend labels (1-D).
    figsize: optional ``(w, h)`` in inches.
    show: call ``plt.show()`` when True.
    save: path to save the figure to (PNG by extension).
  """
  import matplotlib.pyplot as plt

  states = flatten_datasets(datasets)
  if not states:
    raise ValueError("nothing to plot")
  # end
  for st in states:
    if st.values is None:
      raise ValueError("dataset has no values to plot")
  # end

  ref = states[0]
  num_dims = ref.num_dims
  ncomp = ref.num_comps
  fig, axes = plt.subplots(1, ncomp, figsize=figsize or (5 * ncomp, 4),
                           squeeze=False)
  axes = axes[0]

  for c in range(ncomp):
    ax = axes[c]
    if num_dims == 1:
      for i, st in enumerate(states):
        lbl = (labels[i] if labels else st.get_label()) or None
        ax.plot(_centers(st.grid[0]), st.values[..., c], label=lbl)
      # end
      ax.set_xlabel("z0")
      if any((labels or st.get_label()) for st in states):
        ax.legend()
    elif num_dims == 2:
      st = states[0]
      im = ax.pcolormesh(st.grid[0], st.grid[1], st.values[..., c].T,
                         shading="flat")
      fig.colorbar(im, ax=ax)
      ax.set_xlabel("z0")
      ax.set_ylabel("z1")
    else:
      raise ValueError(f"{num_dims}D plotting is not supported in this port")
    # end
    if ncomp > 1:
      ax.set_title(f"comp {c}")
    # end
  # end

  if title:
    fig.suptitle(title)
  # end
  fig.tight_layout()
  if save:
    fig.savefig(save, dpi=120)
  if show:
    plt.show()
  return fig
