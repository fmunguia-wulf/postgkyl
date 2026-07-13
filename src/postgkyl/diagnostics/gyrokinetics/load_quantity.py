"""Loader for pre-named gyrokinetic quantities.

Resolves a quantity name through the :mod:`postgkyl.diagnostics.gyrokinetics.
registry`, loads the required source files, computes the quantity, and
returns ready datasets. Ported from
``src_bak/postgkyl/loaders/gk_quantity.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import gk_quant_registry

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def available_quantities() -> list[str]:
  """Return the sorted list of registered quantity names."""
  return gk_quant_registry.list()
# end


def load_gk_quantity(quantity: str, species: str | None, name: str,
    frame: str | int | None = None, *, path: str = "./",
    tag: str = "default", label: str | None = None, **extra) -> list:
  """Load and compute a pre-named gyrokinetic quantity.

  Args:
    quantity: Registered quantity name (see :func:`available_quantities`).
    species: Species name, or a comma-separated list of them; ``None`` for
      species-independent quantities.
    name: Simulation name prefix (e.g. ``'gk_sheath_2x2v_p1'``).
    frame: Frame number, comma-separated list, or ``'start:stop[:step]'``
      range; ``':'``/``None`` selects all available frames.
    path: Directory containing the simulation files.
    tag: Tag for the output dataset(s); suffixed with the species when more
      than one species is requested.
    label: Label override; defaults to the quantity's registered label.
    **extra: Extra per-quantity parameters (e.g. ``dir=1``, ``mass=0.1``).

  Returns:
    A list of computed ``GDataState`` datasets.

  Raises:
    ValueError: if ``quantity`` is not registered.
  """
  if not gk_quant_registry.has(quantity):
    valid = gk_quant_registry.list()
    raise ValueError(
        f"Unknown quantity '{quantity}'. Available quantities: "
        f"{', '.join(valid)}.")
  # end

  gkquant = gk_quant_registry.get(quantity)
  path = path.rstrip("/") + "/"
  species_list = [s.strip() for s in species.split(",")] if species else [None]

  frame_inp = str(frame) if frame is not None else None
  datasets: list["GDataState"] = []
  for sp in species_list:
    src_combo_idx, frames = gkquant.get_avail_source(path, name, sp, frame_inp)

    for fr in frames:
      out = gkquant.fetch(path, name, sp, fr, src_combo_idx, **extra)

      default_label = gkquant.get_label(species=sp, direction=extra.get("dir"))
      if label is not None:
        out_label = label + (f" {sp}" if len(species_list) > 1 else "")
      # end
      else:
        out_label = default_label
      # end
      if len(frames) > 1:
        out_label += f" f{fr}"
      # end
      out.set_label(out_label)

      out_tag = tag + (f"_{sp}" if len(species_list) > 1 else "")
      out.set_tag(out_tag)

      datasets.append(out)
    # end
  # end

  return datasets
# end
