"""The ``energetics`` verb — decompose plasma energy components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.energetics import energetics as _energetics

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def energetics(elc: "GData", ion: "GData", field: "GData", *, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GData":
  """Decompose energy (kinetic, thermal, EM) for a two-species plasma.

  Splits the plasma energy into its constituent parts for a two-species
  (electron/ion) plasma plus an EM field. The result carries the EM field's
  grid and metadata and has seven components, in order:

  0. electron thermal energy
  1. electron kinetic energy
  2. ion thermal energy
  3. ion kinetic energy
  4. electric field energy (|E|^2 / 2)
  5. magnetic field energy (|B|^2 / 2)
  6. total energy (sum of the above)

  Args:
    elc: GData
      Electron fluid moments (used to compute thermal pressure and kinetic
      energy).
    ion: GData
      Ion fluid moments (used to compute thermal pressure and kinetic energy).
    field: GData
      EM field whose components 0:3 are the electric field and 3:6 are the
      magnetic field; its grid/metadata are carried to the output.
    inplace: bool
      When True, mutate and return ``field``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new seven-component GData of the energy decomposition (or the mutated
    ``field`` when inplace=True).
  """
  grid, values = _energetics(elc, ion, field)
  return field._result(grid, values, inplace=inplace, tag=tag, label=label)
