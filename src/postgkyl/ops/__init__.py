"""The verb library — one function per operation (the single seam).

Every verb takes a dataset first and returns a dataset (via ``_result``), so the
fluent ``GData`` methods, the operators, and any CLI all delegate here and can
never drift apart. Verbs are typed on ``GDataState`` but return the caller's
concrete (sub)class because ``_result`` rebuilds ``type(self)``.
"""

from . import arithmetic
from .interpolate import interpolate
from .select import select
from .info import info
from .plot import plot

__all__ = ["interpolate", "select", "info", "plot", "arithmetic"]
