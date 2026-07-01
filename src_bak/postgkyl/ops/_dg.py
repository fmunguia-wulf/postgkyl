"""Shared helpers for the DG-based verbs (interpolate, differentiate)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.data import GInterpModal, GInterpNodal

if TYPE_CHECKING:
  from postgkyl.data import GData
# end

# Short CLI basis code -> (long basis name, is_modal)
BASIS_MAP = {
    "ms": ("serendipity", True),
    "ns": ("serendipity", False),
    "mo": ("maximal-order", True),
    "mt": ("tensor", True),
    "gkhyb": ("gkhybrid", True),
    "pkpmhyb": ("hybrid", True),
}


def make_interpolator(data: "GData", basis: str | None = None,
    p: int | None = None, interp: int | None = None, read: bool | None = None):
  """Build a ``GInterpModal``/``GInterpNodal`` for ``data``.

  Mirrors the basis-resolution logic that used to live in the ``interpolate``
  and ``differentiate`` CLI commands: a short basis code (e.g. ``"ms"``)
  selects the long basis name and whether the data is modal; when no basis is
  given the values stored in ``data.ctx`` are used.
  """
  basis_long = None
  is_modal = None
  if basis:
    try:
      basis_long, is_modal = BASIS_MAP[basis]
    except KeyError:
      raise ValueError(
          f"Unknown basis '{basis}'. Choices: {sorted(BASIS_MAP)}") from None
    # end
  # end

  if basis is None and not data.ctx.get("basis_type"):
    raise ValueError(
        "No 'basis' was specified and the dataset has no stored 'basis_type'.")
  # end

  if is_modal or data.ctx.get("is_modal"):
    # GInterpModal translates the short basis code internally.
    return GInterpModal(data, poly_order=p, basis_type=basis, num_interp=interp, read=read)
  # end
  return GInterpNodal(data, poly_order=p, basis_type=basis_long, num_interp=interp, read=read)
