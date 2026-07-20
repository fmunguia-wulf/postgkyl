"""Shared CLI state — the chained pipeline's scratch space (``ctx.obj``)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DataSpace:
  """Datasets flowing through a chained command line.

  ``datasets`` is the working set every verb transforms; ``in_data_strings`` is
  the queue of file globs the bare-filename dispatch feeds to ``load``.
  """

  datasets: list = field(default_factory=list)
  in_data_strings: list = field(default_factory=list)
  batch: bool = False
  prefix: str = "pgkyl"
  value_form: str | None = None

  def __iter__(self):
    return iter(self.datasets)
  # end
# end
