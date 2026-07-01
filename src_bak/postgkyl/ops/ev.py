"""The ``ev`` verb — evaluate RPN math expressions over datasets.

The numeric operators live in :mod:`postgkyl.tools.ev_ops` (pure
``(grid, values)`` functions). This module is the L2 glue: a stack machine
(:func:`apply_operator`) shared by the CLI ``ev`` command and a script-facing
:func:`ev` that resolves ``f``/``fN`` tokens against an explicit list of
``GData`` inputs.

Expressions use Reverse Polish Notation, e.g. ``"f0 f1 +"`` adds two datasets
and ``"f 2 *"`` doubles one. Data tokens are:

- ``f`` / ``fN``  — the ``N``-th provided dataset (``f`` == ``f0``),
- ``fN[c]``       — component ``c`` of that dataset (slices like ``0:3`` work),
- ``fN.key``      — the scalar ``ctx[key]`` of that dataset.

Anything else is parsed as a numeric/axis literal (a float, a ``"0,1"`` /
``"0:3"`` axis spec, or a Python literal in brackets/parens).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np

from postgkyl.tools.ev_ops import cmds

if TYPE_CHECKING:
  from postgkyl.data import GData
# end

# f, f0, f12 ... with optional [comp] selection and optional .ctxkey suffix.
_DATA_TOKEN = re.compile(r"^f(\d*)(?:\[([^\]]*)\])?(?:\.(\w+))?$")


def _compare(a, b) -> bool:
  """Equality that also handles NumPy arrays (used when merging ctx dicts)."""
  if isinstance(a, np.ndarray):
    return np.array_equal(a, b)
  # end
  return a == b


def apply_operator(grid_stack, value_stack, ctx_stack, token: str) -> bool:
  """Reduce the RPN stacks in place by applying ``token`` if it is an operator.

  Each stack entry is a list of "sets" (grids/values/ctx dicts); an operator
  pops ``num_in`` entries, applies its pure function from
  :data:`postgkyl.tools.ev_ops.cmds` over every set (broadcasting shorter
  inputs), and pushes ``num_out`` results. The ctx of the output is the merge of
  the inputs' ctx with any conflicting keys dropped.

  Args:
    grid_stack, value_stack, ctx_stack: list
      The parallel RPN stacks, mutated in place.
    token: str
      The candidate operator token (e.g. ``'+'``, ``'sqrt'``, ``'int'``).

  Returns:
    bool: True if ``token`` was a known operator and the stacks were reduced;
    False if ``token`` is not an operator (the stacks are untouched).

  Raises:
    ValueError: If the operator's function raises while evaluating.
  """
  if token not in cmds:
    return False
  # end
  num_in = cmds[token]["num_in"]
  num_out = cmds[token]["num_out"]
  func = cmds[token]["func"]

  in_grid, in_values, in_ctx, num_sets = [], [], [], []
  for _ in range(num_in):
    in_grid.append(grid_stack.pop())
    in_values.append(value_stack.pop())
    in_ctx.append(ctx_stack.pop())
    num_sets.append(len(in_values[-1]))
  # end
  for _ in range(num_out):
    grid_stack.append([])
    value_stack.append([])
    ctx_stack.append([])
  # end

  for set_idx in range(max(num_sets)):
    tmp_grid, tmp_values, tmp_ctx = [], [], []
    for i in range(num_in):
      tmp_grid.append(in_grid[i][min(set_idx, num_sets[i] - 1)])
      tmp_values.append(in_values[i][min(set_idx, num_sets[i] - 1)])
      tmp_ctx.append(in_ctx[i][min(set_idx, num_sets[i] - 1)])
    # end
    try:
      out_grid, out_values = func(tmp_grid, tmp_values)
    except Exception as err:
      raise ValueError(str(err)) from err
    # end

    # Merge ctx of all inputs; drop keys that disagree between inputs.
    out_ctx = {}
    remove_list = []
    for i in range(num_in):
      for key in tmp_ctx[i]:
        if key in out_ctx and _compare(tmp_ctx[i][key], out_ctx[key]):
          pass  # already copied and matches; nothing to do
        elif key in out_ctx:
          remove_list.append(key)  # discrepancy; mark for removal
        else:
          out_ctx[key] = tmp_ctx[i][key]
        # end
      # end
    # end
    for key in dict.fromkeys(remove_list):
      out_ctx.pop(key)
    # end

    for i in range(num_out):
      grid_stack[-num_out + i].append(out_grid[i])
      value_stack[-num_out + i].append(out_values[i])
      ctx_stack[-num_out + i].append(out_ctx)
    # end
  # end
  return True


def _push_token(token: str, datasets, grid_stack, value_stack, ctx_stack) -> bool:
  """Push a single non-operator ``token`` (data reference or literal) onto the stacks.

  Returns False only if the token cannot be interpreted at all.
  """
  match = _DATA_TOKEN.match(token)
  if match:
    from postgkyl.data import select as pselect

    idx = int(match.group(1)) if match.group(1) else 0
    comp = match.group(2)
    ctx_key = match.group(3)
    dat = datasets[idx]
    if ctx_key is not None:
      if ctx_key not in dat.ctx:
        raise ValueError(f"ev: unknown ctx key '{ctx_key}' on dataset f{idx}")
      # end
      grid, values = None, np.array(dat.ctx[ctx_key])
    else:
      grid, values = pselect(dat, comp=comp)
    # end
    grid_stack.append([grid])
    value_stack.append([values])
    ctx_stack.append([dat.ctx])
    return True
  # end

  # Numeric / axis literal fallback (mirrors the CLI token parser).
  if "(" in token or "[" in token:
    value_stack.append([eval(token)])
  elif ":" in token or "," in token:
    value_stack.append([str(token)])
  else:
    try:
      value_stack.append([np.array(float(token))])
    except ValueError:
      return False
    # end
  # end
  grid_stack.append([None])
  ctx_stack.append([{}])
  return True


def ev(chain: str, datasets, *, tag: str | None = None,
    label: str | None = None) -> "GData":
  """Evaluate an RPN expression over an explicit list of datasets.

  Script-facing core of the ``ev`` verb. ``f``/``fN`` tokens in ``chain`` refer
  to ``datasets[N]`` (``f`` == ``f0``); see the module docstring for the token
  grammar. The result is the single value left on top of the stack.

  Args:
    chain: str
      The RPN expression, e.g. ``"f0 f1 +"`` or ``"f sq 2 *"``.
    datasets: Iterable[GData]
      The datasets referenced positionally by the ``f``/``fN`` tokens.
    tag: str | None
      Tag for the returned dataset. Defaults to 'default'.
    label: str | None
      Label for the returned dataset. Defaults to ``chain``.

  Returns:
    GData: A new dataset holding the evaluated grid/values and the merged ctx.

  Raises:
    ValueError: If the expression is empty, a token is unrecognized, or an
      operator fails.
  """
  from postgkyl.data.gdata import GData

  datasets = list(datasets)
  grid_stack, value_stack, ctx_stack = [], [], []
  for token in filter(None, chain.split(" ")):
    if apply_operator(grid_stack, value_stack, ctx_stack, token):
      continue
    # end
    if not _push_token(token, datasets, grid_stack, value_stack, ctx_stack):
      raise ValueError(f"ev: token '{token}' is neither data nor an operator")
    # end
  # end

  if not value_stack:
    raise ValueError("ev: expression produced no result")
  # end

  out = GData(tag=(tag or "default"), label=(label if label is not None else chain),
      ctx=dict(ctx_stack[-1][0]))
  out.push(grid_stack[-1][0], value_stack[-1][0])
  return out
