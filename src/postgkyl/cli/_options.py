"""Shared Click option decorators — the repeated option groups.

The ``--use``/``--tag``/``--label`` triad appears on almost every transform
command (``fft``, ``magsq``, ``differentiate``, ...): ``--use`` filters which
tagged subset of the working set a command applies to, ``--tag``/``--label``
name the result. Declaring each one once here keeps the flag spellings and
help text in lockstep instead of being copy-pasted across every command
module (one home for the fact, mirroring ``src_bak/postgkyl/commands/
_options.py``).

Note: ``select`` deliberately does not use ``tag_option``/``label_option`` --
see ``cli/commands/select.py``; it was already given its own option
declarations by an earlier pass of this layer.
"""

from __future__ import annotations

import click


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
