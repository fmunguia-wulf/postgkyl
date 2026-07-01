"""The object-model layer: the verb-less ``GDataState`` container."""

from .state import GDataState
from .collection import flatten_datasets

__all__ = ["GDataState", "flatten_datasets"]
