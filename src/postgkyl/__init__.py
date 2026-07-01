"""postgkyl — a small, layered post-processing library for Gkeyll data.

Public surface (the facade). The golden script::

    import postgkyl as pg
    pg.load('elc_M0_0.gkyl').interp().sel(z0=0.0).plot()

The facade is **pure re-export** — every public name is defined in the layer that
owns it and simply gathered here:

    load, GData   <- api/       (fluent surface)
    plot          <- render/    (multi-dataset rendering)
    info          <- ops/       (the info verb, one-or-many)
    write         <- io/        (file output)

Architecture (strict, cycle-free DAG; see HIERARCHY_2.md / HIERARCHY_3.md)::

    leaves     numerics/   dg/   io/        (import nothing internal)
    container  core/       GDataState        (state only)
    seam       ops/        one verb each
    backend    render/     matplotlib
    fluent     api/        GData(GDataState) + operators   ← above ops
    facade     __init__    re-exports only
"""

from postgkyl.api import GData, load
from postgkyl.ops import info
from postgkyl.render import plot
from postgkyl.io import write

__version__ = "0.1.0"

__all__ = ["GData", "load", "plot", "info", "write", "__version__"]
