# Layer 10 — diagnostics restructure: review

Scope reviewed: the working tree's diff at review time — new package
`src/postgkyl/diagnostics/{__init__,five_moment,ten_moment,mhd,plasma,
multispecies,rotations,kinetic,pkpm}.py`, new `src/postgkyl/core/guards.py`,
deletions of `src/postgkyl/models/` (all 8 modules + `__init__.py`) and the
seven physics-verb modules + `ops/_guards.py` in `src/postgkyl/ops/`, the
edits to `src/postgkyl/ops/{__init__.py,_materialize.py}`, the `_ALLOWED`
edit in `tests/test_postgkyl.py`, and the eight new test files
`tests/test_diagnostics_{five_moment,ten_moment,mhd,plasma,multispecies,
rotations,kinetic,pkpm}.py` (replacing `tests/test_models_*.py` and
`tests/test_ops_{moments,physics}.py`).

This is a RESTRUCTURE layer per its own instruction file
(`.claude/migration/layers/10-diagnostics.md`): the parity baseline is git
HEAD (the pre-layer state of `models/`+`ops/` physics verbs), not
`src_bak/`. Every moved function's math was diffed line-by-line against
`git show HEAD:<old path>` (not `src_bak/`), per the reviewer procedure for
restructure layers.

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. Each equation module is
  self-contained: a `_get_*` array helper followed immediately by its
  `GDataState`-facing wrapper, a `_REASON` constant stated once per module,
  and a `VARIABLES` table at the bottom naming every public function. The
  one preserved defect that needs cross-file context to fully understand
  (the extra broadcast axis in `pkpm.py:_laguerre_compose`) is documented
  *at the defect site* (`src/postgkyl/diagnostics/pkpm.py:65-69`), not only
  in tests — an improvement over the pattern criticized as C1 in the
  06-models review.
- **I. Data is inert. Functions transform.** Adheres. No classes introduced;
  every public function is `GDataState in -> GDataState out` via `_result`.
- **II. Make illegal states unrepresentable.** Adheres for this layer's own
  code. `multispecies.py:184-188`'s `accumulate_current` raises `ValueError`
  when `qbym=True` and `charge`/`mass` are missing — carried forward
  unchanged from the already-fixed `git show HEAD:src/postgkyl/ops/
  current.py` (the 08-ops-physics fixer's C2 resolution), not a regression
  to the silent-fallback behavior the 08 review originally flagged.
- **III. A function is one idea.** Adheres. Each `_get_*`/public-function
  pair computes exactly one named physical quantity; `_dispatch`-style
  string dispatch is gone from the public surface as the layer requires
  (`five_moment.pressure(d)` replaces `euler(d, variable="pressure")`).
- **IV. The signature tells the whole truth.** Adheres. `plasma.py`'s
  module docstring (lines 9-18) re-states and preserves the 06-review's
  verified rationale for dropping ctx-only parameters (`omegaC` has no
  `species`, `omegaP`/`d`/`lambdaD` have no `field`, `rho` has no
  `epsilon_0`) — carried forward unchanged, correctly, since nothing in
  this layer touches those signatures.
- **V. Every fact has one home.** Adheres, and this is the layer's central
  achievement: `require_field_domain` had six near-duplicate copies before
  layer 08's own fixer centralized them into `ops/_guards.py`; this layer
  moves that one home again, correctly, to `core/guards.py` (verified: `ops/
  _guards.py` no longer exists; `grep -rn "_guards\b" src/ tests/` finds
  only a stale `SOURCES.txt` build artifact, not source). The old
  `VARIABLES`-equivalent option-string tables (`_EULER_VARS`,
  `_TENMOMENT_VARS`, `_MHD_VARS` in the deleted `ops/moments.py`) now have
  exactly one home per equation module, each pinned by a test that asserts
  `set(module.VARIABLES) == {...the old keys...}` (verified in
  `tests/test_diagnostics_five_moment.py:281-283`,
  `tests/test_diagnostics_mhd.py:129-133`,
  `tests/test_diagnostics_ten_moment.py:337-341`).
- **VI. Separate what from how.** Adheres. `diagnostics/*.py` imports only
  `core.guards`, `numerics`, and sibling `diagnostics` modules (verified by
  grep across all eight files) — no `render`, `io`, or `cli` leakage, as the
  layer's own scope requires (layers 12/13 will add `api`/`render` edges,
  not this one).
- **VII. Notation is execution; lowering is transliteration.** Adheres
  exceptionally well. Every array-level formula in `five_moment.py`,
  `ten_moment.py`, `mhd.py`, `plasma.py`, `multispecies.py`, `rotations.py`,
  `kinetic.py`, `pkpm.py` was diffed against `git show HEAD:<old path>` and
  is either byte-identical modulo the mandated `get_x -> _get_x` rename, or
  differs only in which module now owns the call site (e.g. `mhd.py`
  calling `five_moment._get_density` instead of its own copy). No formula
  changed.
- **VIII. Earn your abstractions.** Adheres. `five_moment._infer_num_moms`
  (used twice within `five_moment.py`, and again via `_get_p`/`_get_ke`
  reuse from `ten_moment.py`, `mhd.py`, `plasma.py`, `multispecies.py`) is a
  genuinely multiply-used helper. The layer itself is doctrine VIII in
  action: it dissolves the unearned `models`/`ops` split the layer's own
  mission statement calls out.
- **IX. An abstraction is a contract.** Adheres. `core.guards.
  require_field_domain(data, who, reason)`'s contract (raise iff
  `data.backend == "gkyl"`, with a `.interp() first` message naming `who`
  and `reason`) is stated once in its docstring and honored identically by
  every one of the eight call sites across `diagnostics/`.
- **X. Trust the most formal thing first.** Adheres. Every public function
  is type-annotated; `from __future__ import annotations` is present in
  every new module; tests use `np.testing.assert_allclose` throughout, never
  `==`, with explicit `rtol`.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports).** Adheres — all new imports are `from ..core.
  guards import ...` / `from .. import numerics` / `from .five_moment import
  ...`, no `postgkeyll`.
- **2 (respect the layer DAG).** Adheres — the `_ALLOWED` edit
  (`tests/test_postgkyl.py`) removes `"models"` entirely and the
  `"models"` entry from `"ops"`'s edge set, and adds
  `"diagnostics": {"core", "ops", "numerics"}` with a comment naming
  `10-diagnostics.md`, exactly as the instruction file specifies. Verified
  the actual imports (`grep` across `diagnostics/*.py`) use only `core` and
  `numerics` today — `ops` is an authorized-but-currently-unused edge,
  reserved for layers 12/13, which is what the instruction file's own
  comment says to expect.
- **5 (`__init__.py` re-exports only).** Adheres —
  `diagnostics/__init__.py` is 31 lines of import + `__all__`, no defs.
- **6/7 (type-annotate, keyword-only).** Adheres throughout, verified by
  reading every public function's signature.
- **9 (arrays in ops/numerics, no dual input).** Adheres — every `_get_*`
  helper takes `(grid, values, ...)` and returns `(grid, values)`; every
  public function unwraps `GDataState` before delegating.
- **10 (raise, don't print-and-continue).** Adheres.
- **12 (frozen records, grandfathered ctx).** N/A / adheres — no new `ctx`
  magic keys introduced by this layer.
- **15 (docstrings).** Adheres — every public function has Args/Returns/
  Raises matching the pre-existing style.
- **16 (comments state constraints, not narration).** Adheres, and
  improves on the prior layer: the `pkpm.py:65-69` and `mhd.py`-style
  comments explaining *why* a formula looks the way it does (not "what it
  does") are present at the defect/decision site itself.
- **17 (~100% coverage).** Met — see Coverage below: 100% on
  `postgkyl.diagnostics`, 100% on `postgkyl.ops`, 100% on `postgkyl.core`.
- **18 (tests assert values).** Adheres strongly across all eight new test
  files — analytic fixtures (isotropic pressure tensors, hydrogen plasma
  frequency vs. NRL Formulary, Maxwellian recovery in `pkpm.py`'s tests)
  throughout, not shape-only checks.
- **19 (deterministic tests).** Adheres — the one RNG use found
  (`tests/test_diagnostics_kinetic.py:47`, `np.random.default_rng(0)`) is
  seeded.
- **20 (architecture tests sacred).** Adheres — verified directly (not
  taken on faith): `test_import_contract_no_violations`,
  `test_facade_is_pure_reexport`, `test_foreign_floor_confined_to_ffi`, and
  `test_import_graph_is_acyclic` all pass (4 passed in isolation).
- **21 (copy verbatim; document deviations, never silently fix bugs).**
  Adheres. The `kinetic.py`/`_transform_frame` c_dim==2/3 branches are
  *not* buggy at this layer's baseline (HEAD) — an out-of-band commit
  (`ce9d0af`, predating this migration's layer-by-layer commits) already
  fixed the `f_grid[0].shape[1]` → `f_grid[1].shape[0]` indexing bug in
  `models/frame.py` before layer 06's review was written, so the 06-review's
  "preserved bug" language is now stale relative to HEAD. This layer
  correctly moves the *current* (already-fixed) HEAD code verbatim — the
  restructure's zero-behavior-change bar is against HEAD, and it holds.
  Confirmed by reading `tests/test_diagnostics_kinetic.py`'s
  `TestTransformFrameCdim2`/`Cdim3` classes, which assert real (non-crashing)
  shift values, not `pytest.raises`. The second known preserved bug (the
  extra broadcast axis in `pkpm.py:_laguerre_compose`) genuinely is still
  present at HEAD and is correctly preserved and documented (see above).

## Criticisms

No numerical, structural, or architectural defects were found in this
layer. The only findings are process-level and match a pattern already
noted (at the same low severity) in the 06 and 08 reviews.

**C1 (low severity, recurring process gap).** No implementer report was
found on disk for this layer (`.claude/migration/reviews/` had no prior
`10-diagnostics` file, and no report artifact exists elsewhere), so
Definition-of-done item 4 ("Report: move map, VARIABLES vocabulary per
module, any inlined helpers, `_ALLOWED` diff, coverage, pytest summary") could
not be checked as *delivered*, only reconstructed by this review. This is
the same finding as C2 in the 06-models review and C3 in the 08-ops-physics
review — a gap in the migration's process, not unique to this layer. Low
severity: every number this review needed (move map, `_ALLOWED` diff,
coverage, pytest summary) was independently re-derivable and checks out
(see below).

**C2 (informational, not a defect).** The 06-models review's C1 finding
("the `c_dim==2`/`3` branches always raise `IndexError`, documented only in
tests") is now stale: an out-of-band commit (`ce9d0af`) fixed that bug
before this layer's diff, unrelated to this review's own fixer process.
Nothing in *this* layer's diff caused or masks that discrepancy — the
06-review document itself is simply describing an earlier state of the code
than what now sits at HEAD. Flagged here only so a future reader comparing
the 06-review to current `diagnostics/kinetic.py` isn't confused by the
mismatch; no action needed from this layer.

No other issues found. In particular: no dropped edge cases, no numerical
divergence from HEAD, no silently changed error handling, no dual-input
functions, no `render`/`io`/`cli`/`ctypes`/`typer` leakage into
`diagnostics/`, no mutable default arguments, every `VARIABLES` table is
pinned by a test asserting it equals the old dispatch table's key set, and
`git grep`/plain `grep` for `postgkyl.models` or `from postgkyl import
models` across `src/` and `tests/` (tracked and untracked) returns nothing.

## Coverage

Measured directly (`coverage run --source=src/postgkyl/diagnostics,src/
postgkyl/ops,src/postgkyl/core -m pytest tests/ -q` then `coverage report
-m`; full suite passes, 1054 passed, 2 skipped — `ffi.available() == True`
in this environment, so no gkyl-gated guard tests were skipped):

```
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src/postgkyl/core/__init__.py                  4      0   100%
src/postgkyl/core/collection.py               13      0   100%
src/postgkyl/core/group.py                    25      0   100%
src/postgkyl/core/guards.py                    5      0   100%
src/postgkyl/core/state.py                   202      0   100%
src/postgkyl/diagnostics/__init__.py           2      0   100%
src/postgkyl/diagnostics/five_moment.py      116      0   100%
src/postgkyl/diagnostics/kinetic.py           46      0   100%
src/postgkyl/diagnostics/mhd.py               79      0   100%
src/postgkyl/diagnostics/multispecies.py      41      0   100%
src/postgkyl/diagnostics/pkpm.py              26      0   100%
src/postgkyl/diagnostics/plasma.py            95      0   100%
src/postgkyl/diagnostics/rotations.py         26      0   100%
src/postgkyl/diagnostics/ten_moment.py       178      0   100%
src/postgkyl/ops/__init__.py                  22      0   100%
src/postgkyl/ops/_materialize.py              11      0   100%
src/postgkyl/ops/animate.py                   11      0   100%
src/postgkyl/ops/arithmetic.py               126      0   100%
src/postgkyl/ops/collect.py                   30      0   100%
src/postgkyl/ops/differentiate.py             12      0   100%
src/postgkyl/ops/ev.py                       102      0   100%
src/postgkyl/ops/extract_input.py              8      0   100%
src/postgkyl/ops/fft.py                       12      0   100%
src/postgkyl/ops/fit.py                       42      0   100%
src/postgkyl/ops/grid.py                      22      0   100%
src/postgkyl/ops/growth.py                    24      0   100%
src/postgkyl/ops/info.py                       5      0   100%
src/postgkyl/ops/integrate.py                 16      0   100%
src/postgkyl/ops/interpolate.py               20      0   100%
src/postgkyl/ops/magsq.py                      8      0   100%
src/postgkyl/ops/map.py                       33      0   100%
src/postgkyl/ops/mask.py                      19      0   100%
src/postgkyl/ops/plot.py                       6      0   100%
src/postgkyl/ops/relchange.py                 11      0   100%
src/postgkyl/ops/represent.py                 40      0   100%
src/postgkyl/ops/select.py                    42      0   100%
src/postgkyl/ops/val2coord.py                 38      0   100%
------------------------------------------------------------------------
TOTAL                                       1518      0   100%
```

100% on `postgkyl.diagnostics` (the layer's own bar) and 100% on
`postgkyl.ops`/`postgkyl.core` (which the layer's Definition-of-done also
requires to "stay 100%"). No uncovered region exists in this layer's scope,
so there are no "justified miss" claims to adjudicate — the implementer's
(unwritten, per C1) coverage report would have had nothing to justify.

Full suite: `PYTHONPATH=src python -m pytest tests/ -q` → **1054 passed, 2
skipped** in ~57s. Architecture tests (`test_import_contract_no_violations`,
`test_facade_is_pure_reexport`, `test_foreign_floor_confined_to_ffi`,
`test_import_graph_is_acyclic`) verified to pass in isolation (4 passed).
`git grep -l "postgkyl.models\|from postgkyl import models" -- src/ tests/`
(tracked files) and a matching check over untracked files both return
nothing; `src/postgkyl/models/` does not exist.

## Verdict

**PASS.** This is an unusually clean restructure layer: every one of the
roughly 60 moved public/private functions across eight new equation modules
was diffed against `git show HEAD:<old path>` and found numerically
identical (modulo the mandated `get_x -> _get_x` rename and the folding of
`ops`-side guard/wrapper code with `models`-side array math, exactly as
`10-diagnostics.md` prescribes); the two previously-known defects
(`kinetic.py`'s c_dim branches, now already fixed upstream of this layer;
`pkpm.py`'s extra broadcast axis, still present) are both correctly
preserved relative to HEAD and, in the `pkpm.py` case, documented directly
at the defect site rather than only in tests. The `_ALLOWED` import-contract
edit exactly matches the instruction file's prescribed text and the actual
import graph; `core/guards.py` correctly centralizes the guard that layer
08's own fixer had already begun centralizing; `ops/` is left as a
genuinely equation-blind core-verb library; every `VARIABLES` vocabulary
table is pinned against its old dispatch-table key set by a dedicated test.
Coverage is 100% on `diagnostics`, `ops`, and `core`; the full suite is
green (1054 passed, 2 skipped) with all four architecture tests passing.
The only findings (C1, C2) are process/documentation notes with no code
impact and require no fixer pass.
