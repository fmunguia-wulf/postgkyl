"""Script-callable loader for pre-named gyrokinetic quantities.

Resolves a quantity name through the :mod:`postgkyl.gk.gk_quantities` registry,
loads the required source files, computes the quantity, and returns ready
:class:`~postgkyl.data.GData` datasets. Both ``pg.load.gk_quantity`` and the CLI
``gk-load-quantity`` command are thin wrappers over :func:`load_gk_quantity`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.gk.gk_quantities.registry import gk_quant_registry

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def available_quantities() -> list:
  """Return the list of registered quantity names."""
  return gk_quant_registry.list()


def load_gk_quantity(quantity: str, species: str | None, name: str,
    frame: str | int | None = None, *, path: str = "./",
    tag: str = "default", label: str | None = None,
    log=None, **extra) -> list:
  """Load and compute a pre-named gyrokinetic quantity.

  Args:
    quantity: str
      Registered quantity name (see :func:`available_quantities`).
    species: str | None
      Species name, or a comma-separated list of them; ``None`` for
      species-independent quantities.
    name: str
      Simulation name prefix (e.g. ``'gk_sheath_2x2v_p1'``).
    frame: str | int | None
      Frame number, comma-separated list, or ``'start:stop[:step]'`` range;
      ``':'`` / ``None`` selects all available frames.
    path: str
      Directory containing the simulation files.
    tag: str
      Tag for the output dataset(s); suffixed with the species when more than
      one species is requested.
    label: str | None
      Label override; defaults to the quantity's registered label.
    log: callable | None
      Optional progress callback (e.g. the CLI's ``verb_print``).
    **extra:
      Extra per-quantity parameters (e.g. ``dir=1``, ``mass=0.1``).

  Returns:
    A list of computed :class:`~postgkyl.data.GData` datasets.
  """
  def _log(msg):
    if log is not None:
      log(msg)
    # end

  if not gk_quant_registry.has(quantity):
    valid = gk_quant_registry.list()
    raise ValueError(f"Unknown quantity '{quantity}'. "
        f"Available quantities: {', '.join(valid)}.")
  # end

  gkquant = gk_quant_registry.get(quantity)
  path = path.rstrip("/") + "/"
  species_list = [s.strip() for s in species.split(",")] if species else [None]
  _log(f"Species: {species_list}")

  datasets = []
  for sp in species_list:
    src_combo_idx, frames = gkquant.get_avail_source(path, name, sp, frame)
    _log(f"  {sp}: will compute {gkquant.name} using source {src_combo_idx}, frames {frames}")

    for fr in frames:
      out = gkquant.fetch(path, name, sp, fr, src_combo_idx, **extra)

      default_label = gkquant.get_label(species=sp, direction=extra.get("dir", None))
      if label is not None:
        out_label = label + (f" {sp}" if len(species_list) > 1 else "")
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

  _log(f"Finished loading '{gkquant.name}'")
  return datasets
