"""Discontinuous-Galerkin interpolation engine (leaf layer).

Pure NumPy in / NumPy out. The single public entry point is
:func:`interpolate`; matrix construction lives in :mod:`.matrices`.
"""

from .interp import interpolate, num_basis

__all__ = ["interpolate", "num_basis"]
