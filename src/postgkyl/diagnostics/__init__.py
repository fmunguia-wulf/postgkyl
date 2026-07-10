"""Equation-specific physics — the COMPOSITION tier, one module per equation
model.

Folds together the old ``models`` (array math) and ``ops`` physics-verb
(GData wrapping) layers into a single home per equation system: functions
here take loaded ``GData``/``GDataState`` (one or several) plus physical
scalars as keyword-only options, and return a ``GDataState`` (via
``_result``) or, in later layers, a ``Figure``. Equation-blind core verbs
stay in ``ops``; this is the layer that knows what the numbers mean.

Layers 12/13 extend this package with the equation-internal loaders
(``gyrokinetics/``, ``discovery.py``, ``pkpm.load_pkpm``) and the
program-scale diagnostics (``trajectory``, ``enstrophy``, ``ke_dke``) --
there is no separate ``loaders/`` package.
"""

from . import (
    five_moment,
    ten_moment,
    mhd,
    plasma,
    multispecies,
    rotations,
    kinetic,
    pkpm,
)

__all__ = [
    "five_moment", "ten_moment", "mhd", "plasma", "multispecies",
    "rotations", "kinetic", "pkpm",
]
