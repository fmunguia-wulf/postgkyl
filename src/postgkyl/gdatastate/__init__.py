"""The object-model layer: the verb-less ``GDataState`` container."""

from .gdatastate import GDataState
from .collection import flatten_datasets
from .gdatastategroup import GDataStateGroup

__all__ = ["GDataState", "flatten_datasets", "GDataStateGroup"]
