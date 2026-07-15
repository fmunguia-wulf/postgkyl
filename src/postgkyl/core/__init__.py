"""The object-model layer: the verb-less ``GDataState`` container."""

from .state import GDataState
from .collection import flatten_datasets
from .group import GDataStateGroup

__all__ = ["GDataState", "flatten_datasets", "GDataStateGroup"]
