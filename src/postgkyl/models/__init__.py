"""Equation-system physics — one module per model, arrays in and out.

Every function here takes a grid (list of nodal coordinate arrays), a
values array, and physical scalars as keyword-only options, and returns a
new ``(grid, values)`` pair. No ``GData``, no dual GData-or-tuple input: the
``ops`` verb layer (layer 08) unwraps ``GDataState`` and calls these.
"""

from .five_moment import (
    get_density, get_vx, get_vy, get_vz, get_vi,
    get_p, get_ke, get_temp, get_sound, get_mach,
)
from .ten_moment import (
    get_pxx, get_pxy, get_pxz, get_pyy, get_pyz, get_pzz, get_pij,
    get_p_par, get_p_perp, get_agyro,
    get_gkyl_10m_p_par, get_gkyl_10m_p_perp, get_gkyl_10m_agyro,
)
from .mhd import (
    get_mhd_Bx, get_mhd_By, get_mhd_Bz, get_mhd_Bi,
    get_mhd_mag_p, get_mhd_p, get_mhd_temp, get_mhd_sound, get_mhd_mach,
)
from .plasma_params import (
    get_magB, get_vt, get_vA, get_omegaC, get_omegaP, get_d, get_lambdaD,
    get_rho, get_beta,
)
from .energetics import energetics, accumulate_current
from .rotations import parrotate, perprotate
from .frame import transform_frame
from .laguerre import laguerre_compose

__all__ = [
    "get_density", "get_vx", "get_vy", "get_vz", "get_vi",
    "get_p", "get_ke", "get_temp", "get_sound", "get_mach",
    "get_pxx", "get_pxy", "get_pxz", "get_pyy", "get_pyz", "get_pzz", "get_pij",
    "get_p_par", "get_p_perp", "get_agyro",
    "get_gkyl_10m_p_par", "get_gkyl_10m_p_perp", "get_gkyl_10m_agyro",
    "get_mhd_Bx", "get_mhd_By", "get_mhd_Bz", "get_mhd_Bi",
    "get_mhd_mag_p", "get_mhd_p", "get_mhd_temp", "get_mhd_sound", "get_mhd_mach",
    "get_magB", "get_vt", "get_vA", "get_omegaC", "get_omegaP", "get_d",
    "get_lambdaD", "get_rho", "get_beta",
    "energetics", "accumulate_current",
    "parrotate", "perprotate",
    "transform_frame",
    "laguerre_compose",
]
