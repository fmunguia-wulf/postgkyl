"""The ``ev`` verb — evaluate RPN math expressions over datasets.

The numeric operators live in :mod:`postgkyl.numerics.ev_ops` (pure
``(grid, values)`` functions, keyed by token in ``numerics.ev_cmds``); this
module is the stack machine that drives them and the glue that resolves
``f``/``fN`` tokens against an explicit list of datasets.

Expressions use Reverse Polish Notation, e.g. ``"f0 f1 +"`` adds two datasets
and ``"f 2 *"`` doubles one. Data tokens are:

- ``f`` / ``fN``  -- the ``N``-th provided dataset (``f`` == ``f0``),
- ``fN[c]``       -- component ``c`` of that dataset (slices like ``0:3`` work),
- ``fN.key``      -- the scalar ``ctx[key]`` of that dataset.

Anything else is parsed as a numeric/axis literal (a float, a ``"0,1"`` /
``"0:3"`` axis spec, or a Python literal in brackets/parens). Every operator
in ``numerics.ev_cmds`` is a plain array function -- none needed a
``NotImplementedError`` GData-only placeholder (see the numerics module
docstring), so there is nothing left to resolve here.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np

from postgkyl.numerics import ev_cmds
from postgkyl.ops.select import select

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
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
  :data:`postgkyl.numerics.ev_cmds` over every set (broadcasting shorter
  inputs), and pushes ``num_out`` results. The ctx of the output is the merge
  of the inputs' ctx, dropping any key whose value disagrees between inputs.

  Args:
    grid_stack, value_stack, ctx_stack: the parallel RPN stacks, mutated in
      place.
    token: the candidate operator token (e.g. ``'+'``, ``'sqrt'``, ``'int'``).

  Returns:
    True if ``token`` was a known operator and the stacks were reduced;
    False if ``token`` is not an operator (the stacks are untouched).

  Raises:
    ValueError: if the operator's function raises while evaluating.
  """
  if token not in ev_cmds:
    return False
  # end
  num_in = ev_cmds[token]["num_in"]
  num_out = ev_cmds[token]["num_out"]
  func = ev_cmds[token]["func"]

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
    out_ctx: dict = {}
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
  """Push a single non-operator ``token`` (data reference or literal).

  Returns False only if the token cannot be interpreted at all.
  """
  match = _DATA_TOKEN.match(token)
  if match:
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
      # select() carries the field-domain guard (".interp() first") for
      # every data token, comp-sliced or not.
      sel = select(dat, comp=comp)
      grid, values = sel.grid, sel.values
    # end
    grid_stack.append([grid])
    value_stack.append([values])
    ctx_stack.append([dat.ctx])
    return True
  # end

  # Numeric / axis literal fallback (mirrors the CLI token parser).
  if "(" in token or "[" in token:
    value_stack.append([eval(token)])  # noqa: S307 -- trusted expression source
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


def ev(chain: str, *datasets: "GDataState", tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Evaluate an RPN expression over an explicit list of datasets.

  ``f``/``fN`` tokens in ``chain`` refer to ``datasets[N]`` (``f`` == ``f0``);
  see the module docstring for the token grammar. The result is built via
  ``datasets[0]._result(...)`` (so it stays the caller's concrete dataset
  class) and holds the single value left on top of the stack.

  Args:
    chain: the RPN expression, e.g. ``"f0 f1 +"`` or ``"f sq 2 *"``.
    *datasets: the datasets referenced positionally by the ``f``/``fN``
      tokens. At least one is required (it anchors the result's class).
    tag: optional tag for the returned dataset (defaults to ``'default'``).
    label: optional label for the returned dataset (defaults to ``chain``).

  Returns:
    A dataset holding the evaluated grid/values and the merged ctx.

  Raises:
    ValueError: if ``datasets`` is empty, the expression is empty, a token
      is unrecognized, or an operator fails.
  """
  if not datasets:
    raise ValueError("ev: at least one dataset is required.")
  # end

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

  final_grid = grid_stack[-1][0]
  final_values = value_stack[-1][0]
  final_ctx = dict(ctx_stack[-1][0])
  out_grid = final_grid if final_grid is not None else datasets[0].grid
  result = datasets[0]._result(out_grid, final_values,
      tag=(tag or "default"), label=(label if label is not None else chain))
  # The result's ctx is the RPN merge (apply_operator already resolved every
  # conflict), not datasets[0]'s ctx that '_result' copied as a starting
  # point -- a key apply_operator dropped as conflicting must not survive
  # just because it happened to be on datasets[0]. 'cells'/'num_comps'/
  # 'lower'/'upper' are the shape/grid-derived facts '_result's push() just
  # recomputed from the actual final_grid/final_values; keep those.
  derived = {"cells", "num_comps", "lower", "upper"}
  kept = {k: result.ctx[k] for k in derived if k in result.ctx}
  result.ctx = final_ctx
  result.ctx.update(kept)
  return result
