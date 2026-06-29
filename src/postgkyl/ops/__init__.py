"""Postgkyl verb library — one implementation per operation.

Each function here is the single source of truth for an operation. The fluent
``GData`` methods, the ``DatasetGroup`` methods, and the CLI commands all
delegate to these verbs, so the script and command-line interfaces can never
drift apart.

Verb contract
-------------
Every verb takes a ``GData`` as its first argument and returns a ``GData``::

    op(data, *, ..., inplace=False, tag=None, label=None) -> GData

By default a *new* ``GData`` is returned (so a stored handle stays stable);
pass ``inplace=True`` to mutate and return the input (useful for large data).
The (grid, values) result is always funnelled through ``GData._result`` which
centralizes the in-place/new-dataset branch.
"""

from postgkyl.ops.select import select
from postgkyl.ops.interpolate import interpolate
from postgkyl.ops.differentiate import differentiate
from postgkyl.ops.dg_local_poly import dg_local_poly
from postgkyl.ops.map import map
from postgkyl.ops.integrate import integrate
from postgkyl.ops.fft import fft
from postgkyl.ops.magsq import magsq
from postgkyl.ops.relchange import relchange
from postgkyl.ops.mask import mask
from postgkyl.ops.agyro import agyro, mom_agyro
from postgkyl.ops.current import current
from postgkyl.ops.energetics import energetics
from postgkyl.ops.rotate import parrotate, perprotate
from postgkyl.ops.transform_frame import transform_frame
from postgkyl.ops.moments import euler, tenmoment, mhd, velocity
from postgkyl.ops.collect import collect
from postgkyl.ops.grid import grid
from postgkyl.ops.val2coord import val2coord
from postgkyl.ops.extract_input import extract_input
from postgkyl.ops.laguerre import laguerre_compose
from postgkyl.ops.fit import fit
from postgkyl.ops.growth import growth

__all__ = [
    "select",
    "interpolate",
    "differentiate",
    "dg_local_poly",
    "map",
    "integrate",
    "fft",
    "magsq",
    "relchange",
    "mask",
    "agyro",
    "mom_agyro",
    "current",
    "energetics",
    "parrotate",
    "perprotate",
    "transform_frame",
    "euler",
    "tenmoment",
    "mhd",
    "velocity",
    "collect",
    "grid",
    "val2coord",
    "extract_input",
    "laguerre_compose",
    "fit",
    "growth",
]
