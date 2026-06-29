"""Script-callable loader for Gkeyll PKPM data.

Loads a PKPM distribution and its companion ``pkpm_vars`` file, interpolates
them, and applies the standard Laguerre-compose + frame-transform pipeline,
returning a ready :class:`~postgkyl.data.GData`. Both ``pg.load.pkpm`` and the
CLI ``pkpm`` command are thin wrappers over :func:`load_pkpm`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def load_pkpm(name: str, species: str, idx: str | int, poly_order: int, *,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Load, interpolate, and transform Gkeyll PKPM data.

  Args:
    name: str
      Root name (file prefix) of the simulation.
    species: str
      Species name.
    idx: str | int
      Frame/file number.
    poly_order: int
      Polynomial order of the DG representation.
    tag: str | None
      Optional tag for the resulting dataset.
    label: str | None
      Optional label for the resulting dataset.

  Returns:
    The interpolated, frame-transformed PKPM dataset as a
    :class:`~postgkyl.data.GData`.
  """
  from postgkyl import ops
  from postgkyl.data import GData, GInterpModal

  gf = GData(f"{name:s}-{species:s}_{idx!s:s}.gkyl")
  gvars = GData(f"{name:s}-{species:s}_pkpm_vars_{idx!s:s}.gkyl")

  c_dim = gf.get_num_dims() - 1

  GInterpModal(gf, poly_order, "pkpmhyb").interpolate((0, 1), overwrite=True)

  dg_vars = GInterpModal(gvars, poly_order, "ms")
  grid_and_T_m = dg_vars.interpolate(3)
  grid_and_us = dg_vars.interpolate((0, 1, 2))

  ops.laguerre_compose(gf, grid_and_T_m, inplace=True)
  ops.transform_frame(gf, grid_and_us, cdim=c_dim, inplace=True)

  if tag is not None:
    gf.set_tag(tag)
  # end
  if label is not None:
    gf.set_label(label)
  # end
  return gf
