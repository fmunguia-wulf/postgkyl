# Layer 11 — api (the fluent surface): review

Scope reviewed: the working tree's uncommitted diff at review time —
`src/postgkyl/__init__.py` (facade re-exports), `src/postgkyl/api/__init__.py`,
`src/postgkyl/api/gdata.py` (9 new fluent verb methods: `fft`, `magsq`, `mask`,
`val2coord`, `extract_input`, `fit`, `growth`, `differentiate`, `map`), new
`src/postgkyl/api/group.py` (fluent `DatasetGroup`), new `src/postgkyl/api/verbs.py`
(module-level `collect`/`ev`/`relchange`/`animate`), and new
`tests/test_api_fluent.py`. (The `gkeyll` submodule dirtiness and `pyproject.toml`/
`src/postgkyl/render/plotly.py`/`tests/test_render_{plotly,pyvista}.py` changes
in `git status` predate this layer and are out of scope, per the task.)

Every new fluent method's signature was diffed against its matching
`ops/<verb>.py` signature; every multi-dataset verb in `api/verbs.py` and
`api/group.py` was diffed against `ops/collect.py`, `ops/ev.py`,
`ops/relchange.py`, `ops/animate.py`. The `__getattr__`-broadcast design and
the "no fluent `grid`" exception were diffed against `src_bak/postgkyl/group.py`
and `src_bak/postgkyl/data/gdata.py:1258-1259` (this is not a restructure layer,
so `src_bak/` is the correct parity baseline, not git HEAD).

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. Every fluent method is a one-line
  delegation adjacent to a one-line docstring pointing at its `ops` verb; the
  `grid` exception is explained with its reasoning inline at the call site
  (`src/postgkyl/api/gdata.py:157-164`) rather than requiring the reader to
  reconstruct it; `api/group.py`'s module docstring states the full broadcast
  contract up front instead of scattering it across methods.
- **I. Data is inert. Functions transform.** Adheres. No new mutation is
  introduced; every fluent method still funnels through `ops`/`_result`; the
  new `DatasetGroup.with_`/`__and__` return new groups, mirroring
  `core.DatasetGroup`.
- **II. Make illegal states unrepresentable.** Adheres / not applicable — no
  new constructors; `DatasetGroup(results)` reuses the already-guarded
  `core.DatasetGroup.__init__` (`TypeError` on non-`GDataState` members).
- **III. A function is one idea.** Adheres for every one-line delegation.
  Minor tension only in `DatasetGroup.__getattr__` (see C1): the single
  `broadcast` closure serves both "broadcast a verb, get a group back" and
  "broadcast a terminal verb, get a list back" — two behaviors under one
  entry point — but this is the layer instruction file's own explicitly
  sanctioned trade-off (`11-api.md` "a small `__getattr__`-based delegation
  ... IF you document its contract"), not an undisclosed violation.
- **IV. The signature tells the whole truth.** Mostly adheres. Every
  `api/gdata.py` and `api/verbs.py` signature is keyword-accurate against its
  `ops` counterpart (verified verb-by-verb below). Weakened once: `api/group.py`'s
  module docstring says "Any attribute name ... is resolved by `__getattr__`"
  (`src/postgkyl/api/group.py:12-15`) but the implementation only behaves
  correctly for **callable** members (verb methods); calling it on a
  non-callable attribute (a property such as `num_dims`, `grid`, `backend`)
  returns a closure that raises a confusing `TypeError` only when *invoked*,
  not an `AttributeError` at access time. See C1.
- **V. Every fact has one home.** Adheres, and is a highlight of this layer.
  The facade docstring (`src/postgkyl/__init__.py:8-27`) explicitly declines
  to add a third home (bare top-level export) for verbs that already have two
  (fluent method + `postgkyl.ops.<verb>`) — a one-sentence design rule stated
  once. The `collect`/`ev`/`animate` functions in `api/verbs.py` are the single
  implementation reused by both the module-level spelling and
  `DatasetGroup`'s explicit terminal methods (`src/postgkyl/api/group.py:93-106`
  calls `verbs.collect`/`verbs.ev`/`verbs.animate`, not a second copy).
- **VI. Separate what from how.** Adheres. `api/` still imports only
  `core`/`ops`/`io` (verified by grep of every new/changed file's imports); no
  `render` import anywhere in `api/`, honored even though it costs a
  capability (see C2) — the layer chose contract purity over silently
  reaching around the DAG.
- **VII. Notation is execution; lowering is transliteration.** Adheres. Every
  fluent method reproduces its `ops` verb's keyword vocabulary verbatim
  (parameter names, defaults, and types match exactly — verified line-by-line
  below); nothing is added, dropped, or renamed in the lowering.
- **VIII. Earn your abstractions.** Adheres. `DatasetGroup.__getattr__` is
  justified by the fact that ~15 verbs need identical broadcast treatment
  (a genuine "n-th use", n large) and mirrors the *identical* choice already
  made in `src_bak/postgkyl/group.py:137-151`; no premature generalization
  invented for this layer.
- **IX. An abstraction is a contract.** Mostly adheres. The contract is
  stated explicitly (broadcast → group if every result is a `GDataState`,
  else → list; underscore-prefixed names never broadcast); verified against
  its own tests (`tests/test_api_fluent.py:271-347`). The one place the stated
  contract is broader than the implementation is the "any attribute name"
  phrasing discussed under C1 — the contract as *documented* over-promises
  relative to the contract as *implemented*.
- **X. Trust the most formal thing first.** Adheres. Every public function in
  the diff is type-annotated; `from __future__ import annotations` is present
  in every new/changed module; `tests/test_api_fluent.py` uses
  `np.testing.assert_allclose` for every numeric assertion, never `==`.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports, `postgkyl` not `postgkeyll`).** Adheres — every
  import in the diff is `from postgkyl...` or a same-package relative
  (`from .group import DatasetGroup`, `from . import verbs`).
- **2 (respect the layer DAG; no silent `_ALLOWED` edit).** Adheres —
  `tests/test_postgkyl.py`'s `_ALLOWED["api"]` is untouched
  (`{"core", "ops", "io"}`); confirmed no new edge was needed by grepping
  every import in the four changed/new `api/` files (listed above) and by a
  passing `test_import_contract_no_violations`.
- **5 (`__init__.py` re-exports only).** Adheres — both `api/__init__.py` and
  the facade `__init__.py` contain only imports and `__all__`; `ast`-checked
  by `test_facade_is_pure_reexport` (passing) for the facade, and manually
  verified for `api/__init__.py` (5 lines, no `def`/`class`).
- **6/7 (type-annotate; keyword-only booleans).** Adheres — every new method's
  boolean/optional parameters sit after a bare `*`; verified in every new
  signature in `gdata.py`, `group.py`, `verbs.py`.
- **8 (no mutable default arguments).** Adheres — every default is `None`,
  a literal `bool`/`str`/`float`, or (for `fit`/`growth`'s `guess`) `None`
  resolved downstream in `ops`.
- **9 (verbs take `GDataState`, math stays in `numerics`).** Adheres — this
  layer adds no math, only delegation.
- **10 (raise, don't print-and-continue).** Adheres — no new error handling
  introduced; `DatasetGroup.__getattr__` correctly re-raises `AttributeError`
  for underscore-prefixed names (`src/postgkyl/api/group.py:61-63`) rather
  than swallowing it.
- **15 (docstrings).** Adheres — every new public method/function has at
  least a one-line summary; the more load-bearing ones (`group.py`'s module
  docstring, `gdata.py`'s `grid` comment) carry full rationale.
- **16 (comments state constraints, not narration).** Adheres — the `grid`
  comment states *why* (shadowing risk), not a changelog; no "ported from
  src_bak" comments found.
- **17 (~100% coverage).** Met — see Coverage below: 100% on `postgkyl.api`
  (114/114 statements).
- **18 (tests assert values, not shapes).** Adheres — e.g.
  `tests/test_api_fluent.py:147` (`fit` recovers exact linear coefficients),
  `:156` (`growth_rate` in ctx), `:178` (`ev` sum checked numerically),
  `:232-233`/`:239-240` (`magsq`/`mask` keyword pass-through checked against
  exact expected numbers), not just `isinstance`/shape checks.
- **19 (deterministic, independent tests).** Adheres — no RNG used in this
  test file; `tmp_path` used for the one file-writing test
  (`test_broadcast_write_returns_a_list_of_paths`).
- **20 (architecture tests sacred).** Adheres — verified directly:
  `test_facade_is_pure_reexport`, `test_import_contract_no_violations`,
  `test_foreign_floor_confined_to_ffi`, `test_import_graph_is_acyclic` all
  pass (32 passed in `tests/test_postgkyl.py` in isolation).
- **21 (copy verbatim; document deviations).** Adheres — every fluent
  signature matches its `ops` verb's signature exactly; the one deliberate,
  documented deviation is `DatasetGroup.plot()` broadcasting to one figure
  per member instead of `src_bak`'s shared-overlay group plot (see C2) — a
  gap inherited from layer 09's `ops.plot(data, **kwargs)` being single-dataset
  only, not something this layer could fix without an unauthorized new
  `api → render` edge.

## Criticisms

**C1 (moderate).** `DatasetGroup.__getattr__`'s documented contract
("Any attribute name that is not defined on this class itself ... is
resolved by `__getattr__`", `src/postgkyl/api/group.py:12-15`) is broader than
what the implementation actually handles correctly: it only works for
callable members (verb methods). Accessing a non-callable attribute that
exists on every member but isn't a verb — e.g. `group.num_dims`,
`group.backend`, `group.native` — silently returns a `broadcast` closure
instead of raising `AttributeError` or a list of the members' values; the
failure only surfaces later, as a confusing `TypeError` (`'int' object is not
callable`), when the caller naturally tries to use the result. Verified live:

```
>>> g.num_dims
<function DatasetGroup.__getattr__.<locals>.broadcast at 0x...>
>>> g.num_dims()
TypeError: 'int' object is not callable
```

No test in `tests/test_api_fluent.py` exercises this path (the closest is
`test_private_and_unknown_attributes_are_not_broadcast`, which only covers
names that don't exist on members at all, not properties that do). Cost: a
user exploring a group interactively (`group.grid`, `group.bounds`) gets a
plausible-looking but wrong result instead of an immediate, honest error.
Fix: either (a) narrow the docstring to state the contract is for verb
methods only and is undefined for properties, or (b) make `__getattr__`
itself resolve non-callable member attributes by returning
`[getattr(m, name) for m in self._datasets]` directly (no closure), so
`group.num_dims` "just works" the same way a broadcast verb call does.
Either fix is small; this does not block acceptance since no currently
documented fluent verb triggers it (every entry in `INSTANCE_VERBS` is a
method), but it is a real trap for the next caller who reaches for a
property through the group instead of a verb.

**C2 (informational, not a defect in this layer).** `DatasetGroup.plot()`
broadcasts to one matplotlib figure per member (verified by
`tests/test_api_fluent.py:285-289`), a behavioral divergence from
`src_bak/postgkyl/group.py:154-193`'s `plot`, which explicitly overlaid all
members onto one shared figure ("Plot all members together onto a shared
figure."). This is a real capability regression relative to `src_bak` for
anyone doing `pg.load(...).collect_group(...).plot()`-style comparisons. It
is correctly and honestly documented at the decision site
(`src/postgkyl/api/group.py:20-27`), and it is not something layer 11 could
fix without either (a) an unauthorized `api → render` DAG edge, which the
instruction file's own definition of done rules out ("api sits above
ops/render — no new edges needed"), or (b) `ops.plot` accepting `*datasets`
(a layer 09 decision, already committed, out of this layer's scope: `ops/
plot.py:24-26` is `def plot(data: "GDataState", **kwargs)`, singular). Flagged
here only so a future reader isn't surprised; no action expected from this
layer's fixer.

**C3 (low severity, pre-existing environment issue, not this layer's
defect).** `pytest --cov=postgkyl.api` crashes with `ImportError: cannot load
module more than once per process` during collection of unrelated test
modules (`numpy`'s C extension re-imported under coverage's import hook) —
reproduced independently in this review, and confirmed unrelated to this
layer's code (the same crash occurs collecting `test_core_group.py`,
`test_ffi_array.py`, etc., none of which this layer touches). The
implementer's workaround (`coverage run -m pytest` instead of `pytest --cov`)
is legitimate and reproduces the claimed 100% figure exactly. No fix needed
from this layer; noted for whoever eventually addresses the environment
issue.

No other issues found. In particular: no diagnostics-layer physics method
leaked onto `GData` (`five_moment`/`ten_moment`/`agyro`/`energetics`/etc. do
not appear anywhere in `api/gdata.py`, `api/group.py`, or `api/verbs.py`,
confirmed by grep); no new mutable default arguments; no positional booleans;
no dual-input functions; facade remains a pure re-export (AST-checked); no
unauthorized DAG edge; every multi-dataset verb (`collect`, `ev`, `relchange`,
`animate`) has exactly one implementation reused by both its module-level and
group-method spellings.

## Coverage

Measured directly, both ways:

`PYTHONPATH=src python -m pytest tests/ -q --cov=postgkyl.api --cov-report=term-missing`
— **crashes during collection** (confirms C3; not this layer's fault, and
unrelated test modules fail identically).

`PYTHONPATH=src python -m coverage run --source=src/postgkyl/api -m pytest tests/ -q`
then `coverage report -m`:

```
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
src/postgkyl/api/__init__.py       5      0   100%
src/postgkyl/api/gdata.py         65      0   100%
src/postgkyl/api/group.py         29      0   100%
src/postgkyl/api/load.py           4      0   100%
src/postgkyl/api/verbs.py         11      0   100%
------------------------------------------------------------
TOTAL                            114      0   100%
```

This matches the implementer's claimed 100% (114 stmts, 0 miss) exactly — no
uncovered region exists, so there is no "justified miss" to adjudicate (this
project's coverage tooling measures line coverage, not branch coverage, so
the empty-`results`/no-members branch in `DatasetGroup.__getattr__`'s
`if results and all(...)` short-circuit is not separately exercised by a
0-member-group test, but no line goes uncovered as a result).

Full suite: `PYTHONPATH=src python -m pytest tests/ -q` → **1107 passed, 2
skipped** in ~58-63s across two runs — matches the implementer's claim
exactly. Both skips are `test_render_pyvista.py` (missing optional `trame`/
`trame_vtk` packages), unrelated to this layer. `ffi.available()` is `True`
in this environment, so every `@needs_gkeyll`-gated test in
`tests/test_api_fluent.py` (the `map` test, the `mul`/`div`/`interp`/
`to_modal`/`to_nodal`/`to_quad`/`apply`/`integrate` chain, the end-to-end
chains, `test_animate_is_explicit_not_broadcast`) ran and passed, not just
collected. Architecture tests verified in isolation:
`PYTHONPATH=src python -m pytest tests/test_postgkyl.py -q` → 32 passed.

## Verdict

**PASS.** Every new fluent method's signature was checked keyword-by-keyword
against its `ops` verb and matches exactly (`fft`, `magsq`, `mask`,
`val2coord`, `extract_input`, `fit`, `growth`, `differentiate`, `map`,
`collect`, `ev`, `relchange`, `animate`); the fluent surface stays
equation-blind (no diagnostics-layer physics method leaked onto `GData`,
confirmed by grep); the `grid` exception is verbatim-consistent with
`src_bak/postgkyl/data/gdata.py:1258-1259`'s identical reasoning; the
`DatasetGroup.__getattr__` broadcast design mirrors `src_bak/postgkyl/
group.py:137-151` exactly and correctly reproduces the same non-broadcast
worklist (`info`/`collect`/`ev`/`animate`) that layer 05's review deferred to
this layer; the facade addition is a genuinely pure re-export (AST-enforced,
verified passing) that deliberately avoids creating a third home for
already-doubly-homed verbs; no unauthorized DAG edge was added or needed;
coverage is 100% on `postgkyl.api` (independently re-measured, matching the
implementer's claim exactly); the full suite is green (1107 passed, 2
skipped, independently re-run twice). The only findings are C1 (a moderate,
non-blocking documentation/behavior gap in the group's `__getattr__` contract
for non-callable attributes — no currently-supported fluent verb triggers
it, but it is a real trap worth a small follow-up fix or a narrowed
docstring) and two informational notes (C2: an honestly-documented,
out-of-this-layer's-control capability difference from `src_bak` in
`DatasetGroup.plot()`; C3: a pre-existing, unrelated environment issue with
`pytest --cov`). A fixer pass on C1 is worthwhile but optional — nothing
here represents a numerical, structural, or architectural defect in this
layer's own work.

## Resolutions

**C1: FIXED.** `DatasetGroup.__getattr__` (`src/postgkyl/api/group.py`) now
resolves each member's attribute eagerly (`values = [getattr(member, name)
for member in self._datasets]`) before deciding what to return: if every
member's value is non-callable, it returns `values` directly as a plain
list (no closure); only when every value is callable does it return the
`broadcast` closure, exactly as before. An attribute missing from a member
now raises `AttributeError` at access time rather than only once the
returned closure is called. The module docstring's contract section was
rewritten to state both branches explicitly, so the documented contract no
longer over-promises relative to the implementation (Doctrine IX). New test
`test_broadcast_non_callable_property_returns_a_plain_list`
(`tests/test_api_fluent.py`) exercises `g.num_dims` and asserts it returns a
plain list of each member's value, matching `g[0].num_dims`; the existing
`test_private_and_unknown_attributes_are_not_broadcast` (unchanged) still
passes, confirming `g.this_verb_does_not_exist()` still raises
`AttributeError`, now surfaced at attribute-access time instead of
call-time. Full suite: `PYTHONPATH=src python -m pytest tests/ -q` →
**1108 passed, 2 skipped** (one more than the pre-fix 1107, for the new
test). Coverage re-measured: `postgkyl.api` is still 100%, now 117/117
statements (up from 114, for the 3 added lines).

C2 and C3 remain informational, out of this layer's control, and require
no fix.
