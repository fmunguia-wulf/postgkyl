"""DatasetGroup — an ordered collection of GData with broadcasting verbs.

A ``DatasetGroup`` lets you treat several datasets as one fluent subject.
Non-terminal verbs (``interp``, ``sel``, ...) broadcast over the members and
return a new group; terminal verbs (``plot``, ``info``) act on all members
together::

    a.with_(b).interp().sel(z0=0.0).plot()
    pg.load.many('elc_M0_*.gkyl').interp().integrate().plot()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def _flatten(items) -> list:
  """Flatten GData / DatasetGroup / nested iterables into a flat list of GData."""
  from postgkyl.data.gdata import GData
  out = []
  for item in items:
    if isinstance(item, GData):
      out.append(item)
    elif isinstance(item, DatasetGroup):
      out.extend(item._datasets)
    elif hasattr(item, "__iter__"):
      out.extend(_flatten(item))
    else:
      raise TypeError(f"Expected a GData (or iterable of them), got {type(item)!r}.")
    # end
  # end
  return out


class DatasetGroup:
  """An ordered collection of ``GData`` exposing the same verb vocabulary."""

  def __init__(self, datasets=()):
    self._datasets = _flatten(datasets) if datasets else []

  # ---- Sequence protocol ----
  def __iter__(self):
    return iter(self._datasets)

  def __len__(self):
    return len(self._datasets)

  def __getitem__(self, index):
    result = self._datasets[index]
    return DatasetGroup(result) if isinstance(index, slice) else result

  def __repr__(self):
    return f"<DatasetGroup [{len(self._datasets):d} datasets]>"

  @property
  def datasets(self) -> list:
    return list(self._datasets)

  # ---- Combining ----
  def with_(self, *others) -> "DatasetGroup":
    """Return a new group with ``others`` appended."""
    return DatasetGroup(self._datasets + _flatten(others))

  __and__ = with_

  # ---- Broadcasting of non-terminal verbs ----
  def __getattr__(self, name):
    # Only broadcast public verbs; never intercept dunders/private probes.
    if name.startswith("_"):
      raise AttributeError(name)
    # end

    def broadcast(*args, **kwargs):
      from postgkyl.data.gdata import GData
      results = [getattr(dat, name)(*args, **kwargs) for dat in self._datasets]
      if results and all(isinstance(r, GData) for r in results):
        return DatasetGroup(results)
      # end
      return results
    # end
    return broadcast

  # ---- Terminal verbs ----
  def plot(self, **kwargs):
    """Plot all members onto a shared figure. See ``output.plot_datasets``."""
    from postgkyl import output
    kwargs.setdefault("show", True)
    kwargs.setdefault("figure", 0)
    return output.plot_datasets(self._datasets, **kwargs)

  def info(self) -> str:
    return "\n\n".join(dat.info() for dat in self._datasets)

  def animate(self, **kwargs):
    """Animate the members (one frame each) with matplotlib. See ``output.animate``."""
    from postgkyl import output
    return output.animate(self._datasets, **kwargs)

  def plotly_animate(self, **kwargs):
    """Animate the members as Plotly frames. See ``output.plotly_animate``."""
    from postgkyl import output
    return output.plotly_animate(self._datasets, **kwargs)

  def collect(self, *, sumdata: bool = False, period: float | None = None,
      offset: float = 0.0, tag: str | None = None, label: str | None = None):
    """Combine the members into one dataset along a time axis (-> GData).

    See :func:`postgkyl.ops.collect`.
    """
    from postgkyl import ops
    return ops.collect(self._datasets, sumdata=sumdata, period=period, offset=offset,
        tag=tag, label=label)
