"""The verb library — one function per operation (the single seam).

Every verb takes a dataset first and returns a dataset (via ``_result``), so the
fluent ``GData`` methods, the operators, and any CLI all delegate here and can
never drift apart. Verbs are typed on ``GDataState`` but return the caller's
concrete (sub)class because ``_result`` rebuilds ``type(self)``.

``interpolate`` is the one-way modal -> NumPy bridge; ``arithmetic`` dispatches
on the container backend (Gkeyll kernels for modal data, NumPy for field data);
``integrate`` is a terminal verb that runs inside Gkeyll on modal data. The
physics verbs (``moments``/``agyro``/``current``/``energetics``/``rotate``/
``transform_frame``/``laguerre``) delegate to the equation-system functions in
``models``; ``map`` delegates to the grid-mapping engine in ``dg.map``.
"""

from . import arithmetic
from .interpolate import interpolate
from .select import select
from .info import info
from .integrate import integrate
from .plot import plot
from .represent import apply, represent

from .fft import fft
from .magsq import magsq
from .relchange import relchange
from .mask import mask
from .collect import collect
from .grid import grid
from .val2coord import val2coord
from .extract_input import extract_input
from .fit import fit
from .growth import growth
from .differentiate import differentiate
from .ev import ev

from .moments import euler, tenmoment, mhd, velocity
from .agyro import agyro, mom_agyro
from .current import current
from .energetics import energetics
from .rotate import parrotate, perprotate
from .transform_frame import transform_frame
from .laguerre import laguerre_compose
from .map import map

__all__ = ["interpolate", "select", "info", "integrate", "plot", "arithmetic",
    "represent", "apply",
    "fft", "magsq", "relchange", "mask", "collect", "grid", "val2coord",
    "extract_input", "fit", "growth", "differentiate", "ev",
    "euler", "tenmoment", "mhd", "velocity",
    "agyro", "mom_agyro", "current", "energetics",
    "parrotate", "perprotate", "transform_frame", "laguerre_compose",
    "map"]
