# Layer 08 — ops (wave B): physics verbs + map — review

Scope: the working tree's uncommitted diff at review time — `src/postgkyl/ops/
{moments,agyro,current,energetics,rotate,transform_frame,laguerre,map}.py`
(new), `src/postgkyl/ops/{__init__.py,select.py}` (modified),
`tests/test_postgkyl.py` (`_ALLOWED` edge), `tests/test_ops_{moments,physics,
map}.py` (new). No implementer report file was found on disk (same as the
07 review's finding — this migration does not appear to persist per-layer
reports to `.claude/migration/`).

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. Every verb is a short, self-contained
  function: unwrap `GDataState` → call one `models`/`dg` function → `_result`.
  A reader can verify each verb's correctness by reading only its own file
  plus the one `models` function it calls.
- **I. Data is inert. Functions transform.** Adheres. No new classes; all
  physics logic is free functions in `models`/`dg`, called from `ops` verbs
  that take `GDataState` in and return `GDataState` out.
- **II. Make illegal states unrepresentable.** Violates —
  `models/energetics.py:79-82` (`accumulate_current`, exercised by
  `ops/current.py:49-50`): the docstring states `charge`/`mass` are
  "required when `qbym` is `True`", but the implementation silently falls
  back to the `qbym=False` formula (`factor = -1.0`) whenever `mass` is
  falsy, rather than raising. A "required" parameter that is silently
  ignored when absent is exactly an illegal state the type/contract should
  have refused. (This behavior is inherited unchanged from
  `src_bak/postgkyl/tools/accumulate_current.py:34-38` — see C2 — but the
  new code had the opportunity to fix it and instead a test in this layer's
  own suite (`tests/test_ops_physics.py:138-141`) locks the silent fallback
  in as intended behavior.)
- **III. A function is one idea.** Adheres. Each verb does exactly one thing
  (unwrap → delegate → wrap); `moments.py`'s `_dispatch` cleanly separates
  "look up the variable function" from "apply it".
- **IV. The signature tells the whole truth.** Mostly adheres, with one
  regression risk noted only for completeness: `current()` now takes
  `charge`/`mass` as explicit keyword parameters instead of reading them off
  `data.charge`/`data.mass` implicitly (`src_bak/postgkyl/ops/current.py:14`
  vs. `src/postgkyl/ops/current.py:14-17`) — a genuine improvement per this
  principle (no more spooky action at a distance). The gap is that nothing
  in the new signature enforces the "required when qbym=True" promise the
  docstring makes (see C2) — the signature says one thing, the body does
  another.
- **V. Every fact has one home.** Adheres for the physics verbs (each
  quantity's formula lives once, in `models`). Minor tension: the
  ".interp() first" field-domain guard is re-typed nearly verbatim in six
  new modules (`moments.py`, `agyro.py`, `energetics.py`, `rotate.py`,
  `transform_frame.py`, `laguerre.py`) as separate private
  `_require_field_domain` functions. This mirrors the layer-07 convention
  (`magsq.py`, `fft.py`, `relchange.py`, … all inline the same check), so it
  is not a new violation introduced by this layer, but the fact ("gkyl
  backend ⇒ raise before touching values") now has ~9 near-identical
  homes across `ops/`. Noted at low severity (C5).
- **VI. Separate what from how.** Adheres. `ops/map.py` reads like the
  MAPPING.md algorithm's driver (validate → locate axes → delegate to
  `dg.map_grid` → splice); all the *how* (cell-locate, basis eval) stays in
  `dg/map.py` (layer 03, out of scope here but correctly not duplicated).
- **VII. Notation is execution; lowering is transliteration.** Adheres.
  `ops/map.py` reproduces MAPPING.md's VERB row exactly: same parameter
  names, same offset arithmetic (`num_dims - m`), same validation order,
  same `ctx["grid_type"] = "mapped"` contract.
- **VIII. Earn your abstractions.** Adheres for `moments.py`'s dispatch
  tables (three variable tables sharing one `_dispatch` helper — a real,
  earned abstraction with one contract: "look up `variable`, apply it,
  wrap the result"). The six-times-duplicated `_require_field_domain` (see
  V above) has clearly earned centralization by now, but that debt predates
  this layer.
- **IX. An abstraction is a contract.** Adheres. `ops.map`'s contract is
  exactly stated in its docstring (grid changes, values untouched,
  `ctx["grid_type"]` set) and the tests verify each clause independently.
- **X. Trust the most formal thing first.** Violates in one place: the
  `select.py` curvilinear-guard code (C1) is exercised only by tests that
  happen to use `offset == 0`; no type or test catches the
  `offset != 0` case, so neither the "types" nor the "tests" layer catches
  this bug — it was only found by manual construction during this review.
  100% line coverage gave false confidence (see Coverage below).

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports).** Adheres — all new modules import via
  `from postgkyl import models` / `from postgkyl import dg` /
  `from postgkyl.core.state import GDataState`.
- **2 (respect the layer DAG).** Adheres — `ops → models` is a new edge,
  added to `tests/test_postgkyl.py`'s `_ALLOWED` with a comment explaining
  why it cannot create a cycle (verified: `models/*.py` only imports
  `numerics`, no upward imports).
- **6 (type-annotate every public function).** Adheres throughout.
- **7 (keyword-only options).** Adheres — every boolean/optional parameter
  (`inplace`, `qbym`, `gas_gamma`, `mu_0`, `measure`, `coords`, `space`) is
  keyword-only in every new verb.
- **9 (verbs unwrap, math takes arrays).** Adheres — every new verb unwraps
  `.grid`/`.values` before calling into `models`/`dg`.
- **10 (raise, don't print-and-continue).** Violates —
  `models/energetics.py:79-82` silently substitutes a different formula
  instead of raising when a documented-required argument is missing (C2).
  No new module in this layer's own code adds `print`/bare `except`.
- **17 (~100% coverage).** Met at the line level (100% on `src/postgkyl/
  ops/*`, see Coverage below) but the coverage figure does not detect C1 —
  a logic bug on an untested input combination, not an unreached line.
- **18 (tests assert values, not shapes).** Adheres well —
  `test_ops_moments.py`/`test_ops_physics.py` check exact numeric values
  (`np.testing.assert_allclose` against hand-computed expectations and
  against direct `models.*` calls) throughout, not just `.shape`.
- **21 (never silently change numerical behavior vs. src_bak).** Adheres
  for every verb except the pre-existing `current`/`accumulate_current`
  fallback, which is *unchanged* from src_bak (so, technically, adheres to
  "don't silently change" while perpetuating a latent defect — see C2).
- **24 (leave the tree green).** Adheres — `pytest tests/ -q` is 890 passed,
  0 failed; the four sacred architecture tests pass (verified directly).

## Criticisms

**C1 — `ops/select.py:61,76-77`: the curvilinear-axis guard indexes the
N-D grid array by the dataset's absolute dimension number, not by its
position within the mapped block, corrupting or crashing selection on any
`.map(space="vel")` result with `m > 1` behind a nonzero offset.**

`map_grid` (`dg/map.py`) returns, for an `m`-dimensional map, `m` new grid
arrays that are all shaped like the *tensor product of the m target axes*,
in mapped-dimension order (axis `k` of each array ↔ mapped dimension `k`,
i.e. absolute dimension `offset + k`). `select.py` instead treats array axis
`d` (the dataset's absolute dimension index) as the axis to inspect/slice.
For `offset == 0` (every conf-space map, and the only case exercised by
`tests/test_ops_map.py::TestSelectCurvilinearGuard`) `d` and `d - offset`
coincide, so the bug is invisible. For `offset > 0` — a `space="vel"` map
with `m ≥ 2`, e.g. the 1x2v vel-space case the layer instructions call out
by name — it does not:

- Selecting on the *last* mapped dimension (`d = offset + m - 1`) raises an
  unhandled `IndexError: tuple index out of range`, because
  `grid_arr.shape[d]` and the slicing tuple's `k == d` test both index past
  the array's actual `ndim == m`.
- Selecting on any *other* mapped dimension silently slices the wrong array
  axis: the returned grid keeps its full extent along the axis the caller
  asked to select on, and truncates an unrelated axis instead, while
  `values` is (correctly) sliced along the intended axis — the returned
  `GData`'s grid and values become mutually inconsistent with no error
  raised.

Reproduced directly against the code under review (1 conf + 2 vel dims,
non-square vel extents, `space="vel"`):
```
out = ops.map(target, mapping, space="vel")   # grid1, grid2 shape (6, 4)
ops.select(out, z2=2)   # -> IndexError: tuple index out of range
ops.select(out, z1=1)   # -> no error; out.grid[1].shape == (6, 2)
                        #    (still full-length along its own v0 axis;
                        #     the *other* axis got sliced instead)
```
No test in `tests/test_ops_map.py` combines `select()` with an `m > 1`
`space="vel"` map (`TestVelMap.test_2d_vel_can_be_genuinely_non_separable`
checks the mapped grid directly but never selects on it), so this is
undetected by the suite despite 100% line coverage on `select.py`.

Fix: `select.py` needs the mapped block's `offset` to convert `d` to a
relative index before indexing the curvilinear array, or `map.py`/`ctx`
needs to record which absolute axes a curvilinear array's own dimensions
correspond to (e.g. `ctx["mapped_axes"] = (offset, m)`) so `select` doesn't
have to infer it from `d` alone.

**C2 — `models/energetics.py:79-82` (exercised by `ops/current.py:49-50`):
`accumulate_current` silently substitutes the `qbym=False` formula when a
documented-required argument is missing, instead of raising, and this
layer's own test suite certifies the silent substitution as correct.**

The docstring is explicit: "`charge`: … required when `qbym` is `True`."
"`mass`: … required (and must be nonzero) when `qbym` is `True`." The body
does not enforce this — `if qbym and mass and charge is not None: factor =
charge/mass; else: factor = -1.0` — so `current(data, qbym=True,
charge=2.0)` (mass omitted) returns `-1.0 * values`, the *wrong-sign,
wrong-magnitude* answer for a caller who explicitly asked for charge/mass
scaling and forgot one argument. This is unchanged from
`src_bak/postgkyl/tools/accumulate_current.py:34-38` (same `if
qbym and data.mass and data.charge is not None` guard reading
`data.charge`/`data.mass` off the GData), so it is not a regression
introduced by this layer — but it is squarely this layer's chance to catch
it, and instead `tests/test_ops_physics.py:138-141`
(`test_qbym_without_mass_falls_back_to_minus_one`) locks the silent
fallback in as expected behavior rather than flagging it. `ops/current.py`
itself adds no defensive check either, despite its own docstring's
"Raises" section only documenting the modal-refusal case.

Fix: raise `ValueError` in `accumulate_current` when `qbym` is `True` and
`charge is None or not mass` (belongs in `models/energetics.py`, layer 06,
but `ops/current.py` should also refuse to call through with an
inconsistent `qbym=True`/missing-argument combination rather than silently
mask it).

**C3 — no implementer report was produced for this layer (Definition of
Done item 3).** There is no fixture-copy list, no coverage table, and no
statement of "divergence between old moments outputs and new (must be
none)" anywhere on disk, so a reviewer (or a future maintainer) cannot
cross-check what the implementer *believed* was true against what is
actually true without redoing the whole investigation (as this review did).
This matches the 07 review's same finding, so it is a process gap in the
migration, not unique to this layer — but it is worth re-flagging because
it is exactly what let C1 and C2 go unnoticed: nothing enumerates "checked
against src_bak, identical except for X" for a second pair of eyes to
verify.

**C4 — (informational, not a defect) the `-elc_mapc2p_vel.gkyl` real
vel-space fixture named in the layer instructions cannot exercise the new
engine.** `tests/test_ops_map.py`'s module docstring and
`test_vel_map_legacy_fixture_has_no_basis_metadata_and_cannot_fit` document
this precisely: the fixture's 4 components on a (16, 8) grid predate
MAPPING.md's "one joint m-D basis" contract and no `(basis_type,
poly_order)` combination produces `num_basis == 2` for a 2-D map, so
`num_comps == m * num_basis` can never hold for it. The implementer
substitutes a synthetic 2-D non-separable vel map instead
(`TestVelMap.test_2d_vel_can_be_genuinely_non_separable`) and explains the
mismatch rather than silently skipping the requested fixture. This is a
reasonable, honestly-documented deviation from the letter of the test list
— flagged here only so it is visible to whoever next touches `map`/fixture
inventory, not as something to fix.

**C5 — (minor, pre-existing pattern, not new) `_require_field_domain` is
redefined nearly identically in six new modules.** `moments.py`,
`agyro.py`, `energetics.py`, `rotate.py`, `transform_frame.py`,
`laguerre.py` each carry their own copy of the same three-line guard,
differing only in the wording of the "would mix basis functions" /
"has no basis-space meaning" clause. This mirrors the inline-guard
convention already established by layer 07 (`magsq.py`, `fft.py`, etc.), so
it is not this layer's regression, but by the sixth repetition within one
layer the abstraction has clearly earned centralization (Doctrine VIII).
Suggested fix (not urgent): a single `ops/_guards.py` (or a method on
`GDataState`) taking the verb name and a reason clause.

## Coverage

Measured directly (`coverage run -m pytest tests/ -q` then `coverage
report --include="src/postgkyl/ops/*" -m`); the whole suite passes
(890 passed) with `ffi.available() == True` so none of the gkyl-gated map
tests were skipped in this run:

```
Name                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
src/postgkyl/ops/__init__.py             28      0   100%
src/postgkyl/ops/agyro.py                16      0   100%
src/postgkyl/ops/arithmetic.py          126      0   100%
src/postgkyl/ops/collect.py              30      0   100%
src/postgkyl/ops/current.py               8      0   100%
src/postgkyl/ops/differentiate.py        12      0   100%
src/postgkyl/ops/energetics.py           12      0   100%
src/postgkyl/ops/ev.py                  102      0   100%
src/postgkyl/ops/extract_input.py         8      0   100%
src/postgkyl/ops/fft.py                  12      0   100%
src/postgkyl/ops/fit.py                  42      0   100%
src/postgkyl/ops/grid.py                 22      0   100%
src/postgkyl/ops/growth.py               24      0   100%
src/postgkyl/ops/info.py                  5      0   100%
src/postgkyl/ops/integrate.py            16      0   100%
src/postgkyl/ops/interpolate.py          20      0   100%
src/postgkyl/ops/laguerre.py             11      0   100%
src/postgkyl/ops/magsq.py                 8      0   100%
src/postgkyl/ops/map.py                  31      0   100%
src/postgkyl/ops/mask.py                 19      0   100%
src/postgkyl/ops/moments.py              31      0   100%
src/postgkyl/ops/plot.py                 11      0   100%
src/postgkyl/ops/relchange.py            11      0   100%
src/postgkyl/ops/represent.py            40      0   100%
src/postgkyl/ops/rotate.py               16      0   100%
src/postgkyl/ops/select.py               41      0   100%
src/postgkyl/ops/transform_frame.py      11      0   100%
src/postgkyl/ops/val2coord.py            38      0   100%
-------------------------------------------------------------------
TOTAL                                   751      0   100%
```

All new/changed modules for this layer (`moments.py`, `agyro.py`,
`current.py`, `energetics.py`, `rotate.py`, `transform_frame.py`,
`laguerre.py`, `map.py`, `select.py`, `__init__.py`) sit at 100% line
coverage — comfortably above the 90% floor the layer's Definition of Done
sets, and no "justified miss" needs adjudicating because there are none.

The justification gap is not in *reached* lines but in *reached
combinations*: `select.py`'s curvilinear branch is line-covered by the
`offset == 0` (conf-map) tests only; the `offset > 0`, `m > 1` combination
(C1) is never constructed by any test, so the 100% figure does not mean
what it appears to mean for that branch. Likewise, `current.py`'s `qbym`
path is covered, but only in the direction that confirms the (buggy)
fallback (C2) rather than probing whether it should be an error.

## Verdict

**PASS WITH FIXES.** The wiring — verb↔models dispatch tables, the `map`
verb's fidelity to MAPPING.md's algorithm and validation order, the
`ops → models` import-contract edge, docstrings, keyword-only signatures,
and test-value assertions — is careful, well-documented, and matches the
instruction file closely; the suite is green and coverage is complete at
the line level. But this layer introduces one reproducible, silent
correctness bug of its own (C1: the curvilinear select-guard's absolute-
vs-relative axis confusion, which corrupts or crashes selection on any
multi-dimensional `space="vel"` map — squarely inside this layer's stated
test-list scope) and knowingly certifies a second, inherited one as correct
via its own test (C2: `current`'s silent `qbym` fallback). Both are fixable
without re-architecture — C1 needs the mapped block's offset threaded
through (or recorded in `ctx`) so `select` can convert absolute to relative
axis indices, and C2 needs one `raise` in `accumulate_current` plus an
updated test. A fixer pass addressing C1 and C2 (and, time permitting, C5)
should be sufficient; nothing here calls for re-implementing the layer.

## Resolutions

**C1: FIXED** — `src/postgkyl/ops/map.py:112-122` now records, in
`ctx["mapped_axes"]`, a `{absolute_dim: block_offset}` entry for every
dimension a mapped block touches (merged with any prior block's entries,
so a `space="conf"` map followed by a `space="vel"` map keeps both). This
is a new `ctx` magic key (per `PYTHON_PRINCIPLES.md` #12, noted here since
this fixer pass has no separate report): a curvilinear grid array's own
axis `k` is mapped dimension `k` (absolute dimension `offset + k`), so
`select` needs the block's `offset` to convert an absolute dimension index
`d` to the array's own relative axis `d - offset`. `map.py`'s docstring
(`:52-58`) documents the new key.
`src/postgkyl/ops/select.py:58-64,78-80` now computes `rel = d -
mapped_axes.get(d, 0)` for curvilinear axes and indexes/slices the N-D grid
array on `rel` instead of `d` throughout (`shape[rel]` for the axis length,
and `k == rel` in the slice-tuple comprehension). Verified with a new
regression test, `tests/test_ops_map.py::TestSelectCurvilinearGuard::
test_select_on_2d_vel_map_uses_relative_axis_behind_a_nonzero_offset`,
which reproduces the review's exact repro (1 conf + 2 vel dims, non-square
vel extents, `space="vel"`) and asserts: selecting the last mapped
dimension (previously `IndexError`) now returns the correctly-sliced
`(6, 2)` grid array leaving the other mapped axis's `(6, 4)` array
untouched, and selecting the other mapped dimension (previously a silent
wrong-axis slice) now correctly slices `(2, 4)` instead of the unrelated
axis. Confirmed by re-deriving the expected shapes independently (by hand
and by direct script execution against the fixed code) before writing the
test's assertions.

**C2: FIXED (at the `ops` layer); DECLINED (at the `models` layer, by
design)** — `src/postgkyl/ops/current.py:43-47` now raises `ValueError`
before calling through to `models.accumulate_current` when `qbym=True` and
`charge is None or not mass`, closing the gap the review's own citation
names: "this layer's own test suite ... locks the silent fallback in as
[correct]" (`tests/test_ops_physics.py`, now
`test_qbym_without_mass_raises` / `test_qbym_without_charge_raises` instead
of `test_qbym_without_mass_falls_back_to_minus_one`).
Declining the `models/energetics.py` half of the review's suggested fix:
`models/energetics.py` is layer 06's file — it is not in this review's
scope list, was committed in `b0ec434` (before this layer's diff), and its
own already-committed test suite,
`tests/test_models_energetics.py::test_qbym_without_mass_falls_back_to_negation`
and `::test_qbym_without_charge_falls_back_to_negation`, explicitly locks
the fallback in as `accumulate_current`'s own (already-reviewed) contract.
Changing that function's behavior now would require also rewriting a
different layer's already-approved tests, which is outside this fixer's
mandate (stay in the layer's scope) and outside this review's scope
statement. The `ops/current.py` guard is sufficient to close the defect on
the only path the review demonstrated it through (the public verb); a
direct call to `models.accumulate_current` bypassing `ops` is layer 06's
contract to keep or change, not layer 08's.

**C3: DECLINED** — Backfilling a per-layer implementer report (verb
inventory, fixture-copy list, divergence statement) is Definition-of-Done
work for the *implementer* role for this layer, not a code defect for a
*fixer* pass to correct. Fabricating a report now, after the fact, under
the fixer's authorship would misrepresent what was actually tracked during
implementation (there would be nothing left to verify it against — the
review's own point). This document's Resolutions section is this fixer
pass's accountability artifact instead; it does not stand in for the
missing implementer report, which remains a process gap for the migration
as a whole (shared with layer 07, per the review).

**C4: ACKNOWLEDGED — no action.** Explicitly flagged in the review as
informational, not a defect ("not as something to fix"). No change made.

**C5: FIXED** — Centralized the six near-identical `_require_field_domain`
copies (`moments.py`, `agyro.py`, `energetics.py`, `rotate.py`,
`transform_frame.py`, `laguerre.py`) into one shared
`require_field_domain(data, who, reason)` in the new
`src/postgkyl/ops/_guards.py`, matching the review's suggested shape
("a single `ops/_guards.py` ... taking the verb name and a reason clause").
The check-and-raise logic (`backend == "gkyl"` → `ValueError` with the
standard `.interp() first` message shape) now has one home; each verb
module keeps its own `_REASON` string constant (the fact that varies per
verb — *why* raw coefficients are wrong for that verb — stays local
documentation, not hidden inside a shared function that would have to
special-case six different messages). `ops/relchange.py` and layer 07's
`magsq.py`/`fft.py` (committed in an earlier, already-reviewed layer, and
explicitly out of this review's file scope) were left untouched — the
review characterized their copies as "not this layer's regression."
Verified: full suite green (all six modules' guard tests still pass
unchanged; `src/postgkyl/ops/_guards.py` sits at 100% line coverage,
exercised transitively by every existing field-domain-guard test).
