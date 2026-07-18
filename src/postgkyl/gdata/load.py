"""``pg.load`` — the entry point that returns a fluent :class:`GData`."""

from __future__ import annotations

from postgkyl.gdata.gdata import GData


def load(file_name: str = "", *, tag: str = "default", label: str = "",
    ctx: dict | None = None, representation: str | None = None,
    **read_kwargs) -> GData:
  """Read a Gkeyll output file into a fluent ``GData``.

  ``pg.load('elc_M0_0.gkyl').interpolate().select(z0=0.0).plot()``

  ``representation`` overrides the ``"modal"``/``"nodal"``/``"quad"`` tag the
  file's header metadata would otherwise imply -- for files whose writer
  stamps DG basis metadata even though the stored values are already point
  values (e.g. a per-cell diagnostic like a CFL rate), not modal coefficients.
  """
  return GData(file_name, tag=tag, label=label, ctx=ctx,
      representation=representation, **read_kwargs)
# end
