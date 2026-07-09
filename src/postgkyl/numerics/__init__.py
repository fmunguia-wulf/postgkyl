"""Pure NumPy helpers — no internal imports (the leaf-most layer)."""

from .idx_parser import idx_parser
from .elementwise import grids_compatible, grid_is_prefix

__all__ = ["idx_parser", "grids_compatible", "grid_is_prefix"]
