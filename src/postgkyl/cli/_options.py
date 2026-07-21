"""Shared Click option decorators — the repeated option groups.

The ``--use``/``--tag``/``--label`` triad appears on almost every transform
command (``fft``, ``magsq``, ``differentiate``, ...): ``--use`` filters which
tagged subset of the working set a command applies to, ``--tag``/``--label``
name the result. Declaring each one once here keeps the flag spellings and
help text in lockstep instead of being copy-pasted across every command
module (one home for the fact, mirroring ``src_bak/postgkyl/commands/
_options.py``).
"""

from __future__ import annotations

import os
import sys

import click


def _is_headless() -> bool:
  """True when no GUI display is reachable (e.g. an SSH session on a
  cluster node with no X11/Wayland forwarding) -- the case where
  ``plt.show()`` or opening a browser tab has nowhere to put a window."""
  if sys.platform in ("darwin", "win32"):
    return False
  # end
  return not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
# end


def show_option(help: str = "Open the rendered output preview."):
  """``--show``/``--no-show``: defaults to *off* on a headless session (no
  DISPLAY/WAYLAND_DISPLAY on Linux), since there popping a GUI window or a
  browser tab can't do anything useful; an explicit ``--show``/``--no-show``
  always overrides the detected default."""
  def decorator(f):
    return click.option("--show/--no-show", default=not _is_headless(), help=help)(f)
  # end
  return decorator
# end


def use_option(f):
  """``--use``/``-u``: restrict a transform to datasets tagged with this tag."""
  return click.option("--use", "-u", default=None,
      help="Restrict to datasets tagged with this tag (default: all).")(f)
# end


def tag_option(default: str | None = None, help: str = "Optional tag for the resulting array."):
  """``--tag``/``-t``: tag for the command's result."""
  def decorator(f):
    return click.option("--tag", "-t", default=default, help=help)(f)
  # end
  return decorator
# end


def label_option(default: str | None = None, help: str = "Custom label for the result."):
  """``--label``/``-l``: custom label for the command's result."""
  def decorator(f):
    return click.option("--label", "-l", default=default, help=help)(f)
  # end
  return decorator
# end
