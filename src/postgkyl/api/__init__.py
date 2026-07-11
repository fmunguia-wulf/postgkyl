"""The fluent API surface: the public ``GData``, ``load``, ``DatasetGroup``,
and the module-level multi-dataset verbs (``collect``/``ev``/``relchange``/
``animate``)."""

from .gdata import GData
from .load import load
from .group import DatasetGroup
from .verbs import animate, collect, ev, relchange

__all__ = ["GData", "load", "DatasetGroup", "collect", "ev", "relchange",
    "animate"]
