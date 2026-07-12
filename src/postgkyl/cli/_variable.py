"""Shared dispatch for the moment-diagnostic ``-v/--variable-name`` shells.

``euler``/``tenmoment``/``mhd`` each expose a table of named variables
(``diagnostics.<module>.VARIABLES``) whose functions take different optional
keyword arguments (``gas_gamma``, ``num_moms``, ``mu_0`` — see each module's
``VARIABLES`` table). Rather than hand-writing a branch per variable in every
one of the three CLI shells, :func:`call_variable` calls the resolved
function with only the keyword arguments it actually declares.
"""

from __future__ import annotations

import inspect
from typing import Callable


def call_variable(fn: Callable, data, *, tag: str | None, label: str | None,
    **extra):
  """Call a ``VARIABLES``-table function, forwarding only accepted kwargs.

  Args:
    fn: the variable's function (a value from a ``VARIABLES`` table).
    data: the dataset to pass positionally.
    tag: forwarded as ``tag=`` (every ``VARIABLES`` function accepts it).
    label: forwarded as ``label=`` (every ``VARIABLES`` function accepts it).
    **extra: candidate keyword arguments (e.g. ``gas_gamma``, ``num_moms``,
      ``mu_0``); only the ones ``fn`` declares in its signature are passed.

  Returns:
    Whatever ``fn`` returns.
  """
  accepted = inspect.signature(fn).parameters
  kwargs = {k: v for k, v in extra.items() if k in accepted}
  return fn(data, tag=tag, label=label, **kwargs)
