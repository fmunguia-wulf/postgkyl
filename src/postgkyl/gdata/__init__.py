"""The fluent API surface: the public ``GData``, ``load``, ``GDataGroup``,
and the module-level multi-dataset verbs (``collect``/``evaluate``/``relchange``/
``animate``)."""

from .gdata import GData
from .load import load
from .group import GDataGroup
from .verbs import animate, collect, evaluate, relchange

__all__ = ["GData", "load", "GDataGroup", "collect", "evaluate", "relchange",
    "animate"]
