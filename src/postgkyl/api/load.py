"""``pg.load`` — the entry point that returns a fluent :class:`GData`."""

from __future__ import annotations

from postgkyl.api.gdata import GData


def load(file_name: str = "", *, tag: str = "default", label: str = "",
    ctx: dict | None = None, **read_kwargs) -> GData:
  """Read a Gkeyll output file into a fluent ``GData``.

  ``pg.load('elc_M0_0.gkyl').interpolate().sel(z0=0.0).plot()``
  """
  return GData(file_name, tag=tag, label=label, ctx=ctx, **read_kwargs)
