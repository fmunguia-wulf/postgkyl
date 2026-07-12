"""The fluent API surface: the public ``GData``, ``load``, ``DatasetGroup``,
and the module-level multi-dataset verbs (``collect``/``evaluate``/``relchange``/
``animate``)."""

from .gdata import GData
from .load import load
from .group import DatasetGroup
from .verbs import animate, collect, evaluate, relchange

__all__ = ["GData", "load", "DatasetGroup", "collect", "evaluate", "relchange",
    "animate"]
