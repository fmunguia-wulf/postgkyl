"""
# Postgkyl

Postgkyl is both Python library and command-line tool designed to provide unified access
to Gkeyll data together with a broad variety of analytical and visualization tools.
"""

__version__ = "1.7.5"

# import submodules
from postgkyl import data
from postgkyl import utils
from postgkyl import tools
from postgkyl import output
from postgkyl import ops

# import selected classes to the root
from postgkyl.data.gdata import GData
from postgkyl.data.dg import GInterpNodal
from postgkyl.data.dg import GInterpModal
from postgkyl.group import DatasetGroup
from postgkyl.loader import load


def _flatten_datasets(items):
  """Flatten GData / DatasetGroup / nested iterables into a flat list of GData."""
  out = []
  for item in items:
    if isinstance(item, GData):
      out.append(item)
    elif hasattr(item, "__iter__"):
      out.extend(_flatten_datasets(item))
    else:
      raise TypeError(f"Expected a GData (or iterable of them), got {type(item)!r}.")
    # end
  # end
  return out


def plot(*datasets, **kwargs):
  """Plot one or more datasets together on a shared figure.

  Examples:
    pg.plot(data)
    pg.plot(data_a, data_b)         # overlaid, auto legend
    pg.load('f.gkyl').interp().plot()
  """
  kwargs.setdefault("show", True)
  kwargs.setdefault("figure", 0)  # overlay onto a shared figure by default
  return output.plot_datasets(_flatten_datasets(datasets), **kwargs)


def info(*datasets) -> None:
  """Print the metadata summary for one or more datasets.

  Top-level counterpart of ``GData.info()`` (which *returns* the string).

  Examples:
    pg.info(data)
    pg.info(data_a, data_b)
  """
  for dat in _flatten_datasets(datasets):
    print(dat.info())
  # end


def pr(*datasets) -> None:
  """Print the values of one or more datasets (top-level counterpart of `pr`)."""
  for dat in _flatten_datasets(datasets):
    print(dat.get_values().squeeze())
  # end


# link the command line executable to the system
from postgkyl import pgkyl

