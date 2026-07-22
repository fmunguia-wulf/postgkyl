"""``pg.load`` -- the entry point that returns a fluent :class:`GData`."""

from __future__ import annotations

from postgkyl.gdata.gdata import GData


def load(file_name: str = "", *, tag: str = "default", label: str = "",
    ctx: dict | None = None, value_form: str | None = None,
    basis_type: str | None = None, poly_order: int | None = None,
    **read_kwargs) -> GData:
  """Read a Gkeyll output file into a fluent ``GData``.

  ``pg.load('elc_M0_0.gkyl').interpolate().select(z0=0.0).plot()``

  ``basis_type``, ``poly_order``, and ``value_form`` are properties of the
  data itself, fixed here at load time (from the file's header metadata, or
  the override below) -- no downstream verb (``interpolate``, ``average``,
  ...) ever re-specifies them; they always read ``ctx["basis_type"]``/
  ``ctx["poly_order"]``/``ctx["value_form"]`` off the loaded dataset.

  ``value_form`` overrides the ``"modal"``/``"nodal"``/``"quad"`` tag the
  file's header metadata would otherwise imply -- for files whose writer
  stamps DG basis metadata even though the stored values are already point
  values (e.g. a per-cell diagnostic like a CFL rate), not modal coefficients.

  ``basis_type`` overrides the ``"basis_type"`` (e.g. ``"serendipity"``,
  ``"tensor"``, ``"gkhybrid"``) the file's header metadata would otherwise
  imply -- for files with no basis metadata at all, or metadata that
  mislabels the basis actually used. Setting it also defaults ``value_form``
  to ``"modal"`` (unless ``value_form`` is given too), so downstream verbs
  that read ``ctx["basis_type"]`` resolve the right basis.

  ``poly_order`` overrides the ``"poly_order"`` the file's header metadata
  would otherwise imply. It is independent of ``basis_type``/``value_form`` --
  passing it alone corrects only the polynomial order and asserts nothing
  about whether the dataset is modal.
  """
  return GData(file_name, tag=tag, label=label, ctx=ctx,
      value_form=value_form, basis_type=basis_type,
      poly_order=poly_order, **read_kwargs)
# end
