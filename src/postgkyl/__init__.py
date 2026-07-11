"""postgkyl — a small, layered post-processing library for Gkeyll data.

Public surface (the facade). The golden script::

    import postgkyl as pg
    pg.load('elc_M0_0.gkyl').interp().sel(z0=0.0).plot()

The facade is **pure re-export** — every public name is defined in the layer that
owns it and simply gathered here:

    load, GData, DatasetGroup        <- api/       (fluent surface)
    collect, ev, relchange, animate  <- api/       (module-level multi-dataset
                                                     verbs -- no single ``self``)
    plot                             <- render/    (multi-dataset rendering)
    info                             <- ops/       (the info verb, one-or-many)
    integrate                        <- ops/       (grid integral, via Gkeyll)
    interpolate/interp, select/sel   <- ops/       (functional verb spellings)
    represent, apply                 <- ops/       (representation verbs)
    write                            <- io/        (file output)

Every fluent ``GData`` method delegates to one of these ``ops`` functions, so
``pg.select(a, z0=0.0)`` and ``a.select(z0=0.0)`` are the same call — the
functional and fluent spellings can never drift apart. The rest of the
equation-blind ``ops`` verb inventory (``fft``, ``magsq``, ``mask``,
``val2coord``, ``extract_input``, ``fit``, ``growth``, ``differentiate``,
``map``, plus ``grid`` -- see ``api/gdata.py`` for why ``grid`` has no fluent
spelling) is reachable as a ``GData`` fluent method and via
``postgkyl.ops.<verb>``; this facade does not additionally promote each one to
a bare top-level name (one home per verb-vocabulary fact, not three).

Architecture (strict, cycle-free DAG; see REFACTOR_GKEYLL_FFI.md)::

    floor      ffi/        ctypes -> libg0core.so (the only foreign code)
    leaves     numerics/   (pure NumPy; imports nothing internal)
    engine     dg/         interp bridge + modal ops   -> ffi
    leaves     io/         readers (C-native first)    -> ffi
    container  core/       GDataState {gkyl|numpy} backend
    seam       ops/        one verb each
    backend    render/     matplotlib
    fluent     api/        GData(GDataState) + operators   <- above ops
    facade     __init__    re-exports only
"""

from postgkyl.api import GData, load, DatasetGroup, animate, collect, ev, relchange
from postgkyl.ops import apply, info, integrate, interpolate, represent, select
from postgkyl.render import plot
from postgkyl.io import write

# Short aliases, mirroring the fluent methods (a.interp() / a.sel()).
interp = interpolate
sel = select

__version__ = "0.1.0"

__all__ = ["GData", "load", "DatasetGroup", "plot", "info", "integrate",
    "interpolate", "interp", "select", "sel", "represent", "apply", "write",
    "collect", "ev", "relchange", "animate", "__version__"]
