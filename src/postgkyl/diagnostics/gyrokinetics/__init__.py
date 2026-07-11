"""Gyrokinetic diagnostics: distribution-function + derived-quantity loading
and physics.

The whole gyrokinetic-quantity stack -- naming-convention file resolution
(``quantity.py``), the derived-quantity physics (``quantities.py``), the
registry (``registry.py``), and the "physics-ready data by name" entry point
(``load_quantity.py``) -- lives together in this subpackage (see the layer-12
instruction file's decision record): splitting resolution from physics would
give gyrokinetics two homes for one piece of equation knowledge. Only the
equation-blind stem/frame discovery is shared, via
``postgkyl.diagnostics.discovery``.
"""

from __future__ import annotations

from .distf import load_gk_distf, resolve_frames
from .load_quantity import available_quantities, load_gk_quantity
from .quantities import (
    fetch_beta_from_bmag_press,
    fetch_diamag_vel,
    fetch_ExB_vel,
    fetch_gradB_vel,
    fetch_M1_from_H,
    fetch_press_from_BiMax,
    fetch_press_from_Max,
    fetch_press_p,
    fetch_Tpar_from_BiMax,
    fetch_Tpar_from_M0_M1_M2par,
    fetch_temp_from_Max,
    fetch_temp_from_Tpar_Tperp,
    fetch_Tperp_from_BiMax,
    fetch_Tperp_from_M0_M2perp,
)
from .registry import gk_quant_registry

__all__ = [
    "load_gk_distf", "resolve_frames",
    "available_quantities", "load_gk_quantity", "gk_quant_registry",
    "fetch_beta_from_bmag_press", "fetch_diamag_vel", "fetch_ExB_vel",
    "fetch_gradB_vel", "fetch_M1_from_H", "fetch_press_from_BiMax",
    "fetch_press_from_Max", "fetch_press_p", "fetch_Tpar_from_BiMax",
    "fetch_Tpar_from_M0_M1_M2par", "fetch_temp_from_Max",
    "fetch_temp_from_Tpar_Tperp", "fetch_Tperp_from_BiMax",
    "fetch_Tperp_from_M0_M2perp",
]
