"""Typed application state for the pgkyl CLI.

Replaces the untyped ``ctx.obj`` dict with a dataclass so reads are
type-checked and discoverable. Commands access it by attribute::

    state: AppState = ctx.obj
    state.data, state.compgrid, ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from postgkyl.commands.data_space import DataSpace


@dataclass
class AppState:
  """Shared per-invocation CLI state, attached to ``ctx.obj``."""

  data: DataSpace = field(default_factory=DataSpace)
  verbose: bool = False
  batch_mode: bool = False
  saveframes_prefix: str = ""
  compgrid: bool = False
  global_var_names: list[str] | None = None
  global_cuts: tuple = (None, None, None, None, None, None, None)
  in_data_strings: list[str] = field(default_factory=list)
  in_data_strings_loaded: int = 0
  start_time: float = 0.0
  rcParams: dict = field(default_factory=dict)
  fig: Any = ""
  ax: Any = ""
  plot_handles: dict = field(default_factory=dict)
