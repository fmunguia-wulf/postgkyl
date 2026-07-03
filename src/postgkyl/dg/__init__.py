"""Discontinuous-Galerkin layer — orchestrates Gkeyll's compiled DG engine.

Two modules, one per domain boundary:

- :mod:`.interp` — the one-way modal -> NumPy bridge (matrix from Gkeyll's
  basis functions, applied with NumPy).
- :mod:`.modal` — operations that stay in the modal domain (weak algebra,
  coefficient linear combinations, integration), all executed by Gkeyll
  kernels on native arrays.
"""

from .interp import interpolate, num_basis
from . import modal

__all__ = ["interpolate", "num_basis", "modal"]
