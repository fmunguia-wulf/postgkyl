"""Thin per-verb CLI command shells (one module per verb).

Each module exposes a ``command`` (a ``click.Command``). Adding a new verb is a
drop-in: create ``commands/<verb>.py`` with a ``command`` and add it to
``COMMANDS`` below (or discover via entry points).
"""

from . import load, interpolate, select, plot, info, write

COMMANDS = [
    load.command,
    interpolate.command,
    select.command,
    plot.command,
    info.command,
    write.command,
]

__all__ = ["COMMANDS"]
