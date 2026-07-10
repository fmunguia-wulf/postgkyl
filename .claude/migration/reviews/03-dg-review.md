# Layer 03 — dg: review

Scope reviewed: `src/postgkyl/dg/{__init__.py,map.py,rep.py}` (diff),
`src/postgkyl/ffi/__init__.py` (diff), `tests/test_coverage_leaf.py` (diff),
`tests/test_dg_map.py`, `tests/test_dg_rep.py` (new), and
`.claude/migration/notes/differentiate-decision.md`. `dg/interp.py`/`dg/modal.py`
are unchanged in this diff and were read for context only. Every new/changed
file was read in full; `dg/rep.py` was diffed byte-for-byte against the
pre-move `ffi/rep.py` (`git show HEAD:src/postgkyl/ffi/rep.py`) — identical,
confirming job 1 is a pure relocation. `dg/map.py`'s algorithm was checked
against `MAPPING.md`'s spec line by line and against `src_bak/postgkyl/ops/map.py`
(the old alignment-arithmetic algorithm MAPPING.md deliberately replaces).
The differentiate-decision document's factual claims (shim function coverage,
hybrid/gkhybrid kernel terms) were independently re-verified by grepping
`gkeyll/core/zero/gkyl_pg0.h`, `gkeyll/core/zero/gkyl_basis.h`,
`src/postgkyl/ffi/csrc/_g0pymodule.c`, and
`gkeyll/core/ker/basis/basis_eval_{hyb,gkhyb}.c`.

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. `eval_at_points` and `map_grid` take
  plain arrays/dicts and return plain arrays; a reader can verify either
  function against `MAPPING.md`'s four-step algorithm without opening any
  other module.
- **I. Data is inert. Functions transform.** Adheres. No classes introduced;
  `dg/map.py` is two free functions over NumPy arrays.
- **II. Make illegal states unrepresentable.** Not applicable in the strong
  sense (no new constructors), but `eval_at_points` refuses malformed inputs
  at the boundary (`map.py:58-66`: cell-count mismatch, points-dimension
  mismatch) rather than producing a silently wrong shape — the right
  parse-don't-validate posture for a leaf function.
- **III. A function is one idea.** Adheres. `eval_at_points` is exactly the
  four steps MAPPING.md names; `map_grid` is exactly "build target points,
  call `eval_at_points` once per mapped dimension."
- **IV. The signature tells the whole truth.** Adheres. Both functions are
  pure (arrays in, arrays out); `modal`/`basis_type`/`poly_order` are
  keyword-only and disclosed; no hidden state.
- **V. Every fact has one home.** Adheres. The cell-locate/clip convention
  exists once (`map.py:79`); the boundary-continuity assumption ("mapc2p
  fields are continuous") is stated once, in the module's spec (MAPPING.md)
  and echoed briefly in the docstring rather than re-derived.
- **VI. Separate what from how.** Adheres, and job 1 is exactly this
  principle in action: `ffi/rep.py` (a floor primitive's home) held
  orchestration logic that CLAUDE.md says belongs one layer up; moving it to
  `dg/rep.py` without touching a line of its body is the textbook "logic and
  machinery are different concerns" move, done cleanly. `ffi/__init__.py`'s
  new docstring paragraph (`ffi/__init__.py:21-23`) states the boundary
  explicitly instead of leaving it implicit.
- **VII. Notation is execution; lowering is transliteration.** Adheres.
  `eval_at_points`'s four numbered steps in the code (`map.py:78,80,88,96`)
  are labeled with the same step numbers MAPPING.md uses — the spec and the
  code are the same document read at two levels of detail.
- **VIII. Earn your abstractions.** Adheres. No premature generalization —
  `eval_at_points` takes exactly the primitive shape MAPPING.md specifies,
  and `map_grid` is the one caller that needs the tensor-product wrapper, not
  a speculative N-caller abstraction.
- **IX. An abstraction is a contract.** Adheres. `eval_at_points`'s contract
  (shape in → shape out, exact for in-basis polynomials, clip convention at
  domain edges) is stated in its docstring and every test checks exactly that
  contract, not implementation details.
- **X. Trust the most formal thing first.** Adheres well: 100%-line-covered,
  and every test in `test_dg_map.py`/`test_dg_rep.py` asserts against an
  independently-computed expected value (projected-from-a-known-function
  coefficients, an analytic constant-basis value), never against the code
  under test's own output. The differentiate-decision itself is "trust the
  most formal thing first" applied to a decision, not just code: it re-derives
  the exactness bound from the kernel source rather than trusting the
  instruction file's suggested approach at face value, and correctly declines
  to ship an approach that cannot be proven exact for the tool's primary
  basis family (gkhybrid).

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports, no `postgkeyll`).** Adheres. `dg/map.py:21` uses
  `from postgkyl import ffi`; `dg/rep.py`'s imports were already absolute
  (`from postgkyl.ffi import basis as ffi_basis`) before the move and needed
  no change.
- **2 (respect the layer DAG).** Adheres. `dg → ffi` is the only new edge
  exercised, already allowed in `_ALLOWED`. `test_import_contract_no_violations`,
  `test_import_graph_is_acyclic`, `test_foreign_floor_confined_to_ffi` all
  pass (verified directly, not taken on faith).
- **5 (`__init__.py` re-exports only).** Adheres. `dg/__init__.py`'s diff is
  purely `from .map import ...` / `from . import modal, rep` plus an updated
  `__all__`/docstring; no `def`/`class` added.
- **6/7 (type-annotate, keyword-only options).** Adheres.
  `eval_at_points`/`map_grid` are fully annotated (`list[np.ndarray]`,
  `dict`, `np.ndarray`); every option after the data arguments in
  `eval_at_points` (`basis_type`, `poly_order`, `modal`) is keyword-only.
- **9 (arrays in, arrays out in leaves).** Adheres. Neither function touches
  `GData`/`GDataState`; `map_grid` takes a plain `ctx`-shaped dict, not a
  container object, matching the ENGINE row's contract in MAPPING.md exactly.
- **10 (raise, don't print-and-continue).** Adheres. Both malformed-input
  paths in `eval_at_points` raise `ValueError` naming the offending shape.
- **12 (frozen records for structured data).** `map_ctx` is a plain dict —
  but this is the pre-existing, grandfathered `ctx` convention (rule 12
  explicitly grandfathers it), and `map_grid`'s docstring states exactly
  which keys it reads, so it is not an undocumented magic-key extension.
- **15 (docstrings).** Adheres. Both new functions have full
  Args/Returns/Raises sections; edge cases (nodal-basis conversion, `m == 1`
  vs `m > 1`, the clip convention) are documented, not just narrated in
  comments.
- **17 (one test file per module, ~100% coverage).** Adheres:
  `tests/test_dg_map.py` for `dg/map.py`, `tests/test_dg_rep.py` for the
  post-move `dg/rep.py`; measured coverage is 100% on all of `postgkyl.dg`
  (see Coverage below).
- **18 (assert values, not shapes).** Adheres strongly. Every map test
  computes its expected value from an independent projection helper
  (`_project_1d`/`_project_2d`), never from the code under test; the rotation
  test (`test_map_grid_2d_rotation_is_exact_non_separable`) is a genuine
  non-separable analytic case, not a shape check.
- **19 (independent, deterministic tests).** Adheres. No RNG, no network, no
  ordering dependence; both new test files gate on `ffi.available()` via the
  established `needs_gkeyll` pattern.
- **21 (copy liberally, never change numerics silently).** Adheres by
  design: MAPPING.md explicitly supersedes `src_bak/postgkyl/ops/map.py`'s
  algorithm (confirmed by reading `src_bak/postgkyl/ops/map.py` — it uses
  `num_interp`/cell-count alignment arithmetic that MAPPING.md's own header
  says is deliberately dropped), so this is a documented intentional
  divergence, not a silent one.

## Criticisms

1. **C1 — `dg/map.py:126` (minor, documentation-only).** `map_grid` derives
   the mapped dimensionality `m` from `len(target_axes)` rather than from
   `len(map_ctx["lower"])`; if a future caller passes a `target_axes` whose
   length doesn't match the mapping's own dimensionality, `nb =
   ffi.basis.num_basis(basis_type, m, poly_order)` (`map.py:135`) computes
   `num_basis` for the *wrong* `m` before `eval_at_points`'s internal
   `points.shape[-1] != m` check (`map.py:63-66`) catches the inconsistency
   and raises. The mismatch is always caught — verified by tracing both
   checks — so this is not a silent-wrong-number bug, only a design choice
   (engine trusts the caller; MAPPING.md's VERB row places the "map fits the
   dataset" validation in `ops/map.py`, not yet implemented) that a future
   reader might mistake for a missing guard. No fix required before merging
   this layer; worth a one-line comment when `ops/map.py` is built pointing
   back to this contract.
2. **C2 — `MAPPING.md`'s own boundary-convention prose vs. the literal
   formula (documentation nit, not a code defect).** MAPPING.md's algorithm
   text says "shared interior edge points evaluate in the left cell at η =
   +1," but the literal formula it also gives —
   `i = clip(floor((z - lower)/dz), 0, cells - 1)`, reproduced verbatim at
   `dg/map.py:79` — places an exact interior boundary point in the *right*
   cell at η = −1, not the left cell at η = +1. Confirmed this is harmless in
   practice: MAPPING.md's own justification ("well defined because mapc2p
   fields are continuous") means both cells' polynomials agree at the shared
   edge, and `test_map_grid_identity_1d_matches_target_axis` /
   `test_map_grid_identity_2d_curvilinear_matches_meshgrid` both place
   targets exactly on the mapping's own interior cell edges and pass at
   1e-12 — so no numerical divergence exists today. It only becomes a live
   risk if `ffi.available()` is False in production and no test exercises
   this path, or if a future genuinely-discontinuous-per-cell field is ever
   passed as a "mapping" against the documented continuity assumption. Not
   flagged as an ambiguity in any note file the reviewer could find; the
   layer instruction file asked implementers to record spec ambiguities in
   their report, and this is exactly that kind of ambiguity, so it would be
   worth adding a one-line note (not a code change) either to
   `dg/map.py`'s docstring or a follow-up note file.
3. **C3 — coverage/test gap, low severity.** No test exercises the
   boundary-clip convention with a genuinely curved (degree ≥ 2), multi-cell
   map — `test_eval_at_points_in_basis_quadratic_is_exact_at_edges`
   deliberately uses a single cell to "sidestep cell-boundary continuity
   questions" (its own docstring), and every multi-cell test uses an affine
   (degree-1) map, where any cell-boundary convention gives the same answer
   trivially. A subtle sign or off-by-one error in the clip/floor logic that
   only manifests for higher-order multi-cell maps at interior edges would
   not be caught by the current suite despite 100% line coverage (the same
   lines execute either way). Suggested fix: add one 2-cell, `poly_order=2`
   1-D test evaluating exactly at an interior edge with a genuinely
   quadratic (not just linear) map function.

No other criticisms found. Job 1 (the `ffi/rep.py` → `dg/rep.py` move) is
byte-identical apart from its file path and is fully re-wired (verified via
`grep` that no importer anywhere still says `ffi.rep`/`ffi import rep`
outside an intentional historical-context docstring in
`tests/test_dg_rep.py:3`). Job 3's decision document is factually accurate
against the actual C sources and reaches a defensible, evidence-based
"defer" conclusion rather than shipping something proven wrong for the
tool's primary gyrokinetic (gkhybrid) basis family.

## Coverage

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/postgkyl/dg/__init__.py       4      0   100%
src/postgkyl/dg/interp.py        39      0   100%
src/postgkyl/dg/map.py           43      0   100%
src/postgkyl/dg/modal.py         32      0   100%
src/postgkyl/dg/rep.py           84      0   100%
-----------------------------------------------------------
TOTAL                           202      0   100%
```

Measured independently with `PYTHONPATH=src python -m coverage run
--source=src/postgkyl/dg -m pytest tests/ -q` followed by `coverage report
-m` (the `--cov` pytest-cov flag fails to collect in this environment with an
unrelated "cannot load module more than once per process" numpy error;
`coverage run` sidesteps it and gives the same numbers). 100% exceeds the
layer's ≥ 90% bar with no misses to justify. Full suite: 541 passed, 0
failed, 0 skipped (`ffi.available()` is `True` in this environment, so every
`needs_gkeyll`-gated test actually ran, not just collected).

## Verdict

**PASS.** Both required jobs are executed cleanly and match their specs:
job 1 is a verified byte-identical relocation with every importer updated and
no stale references left behind; job 2's `eval_at_points`/`map_grid`
implement MAPPING.md's algorithm exactly, are tested with independently-derived
expected values including a genuinely non-separable (rotation) case, and
correctly diverge from the superseded `src_bak` alignment-arithmetic
algorithm as the spec demands; job 3 produces the required decision document
with technically accurate, independently-verified evidence and a defensible
"defer" call rather than shipping an unproven approximation. The layer hits
100% coverage on `postgkyl.dg` and leaves the full suite and all four
architecture tests green. The three criticisms above are a design-contract
observation (C1), a spec-prose vs. spec-formula inconsistency that is
provably harmless today (C2), and a narrow test-coverage gap for an
untested-but-plausible edge case (C3) — none rise above minor/maintenance
severity, and none block merging this layer as-is. A fixer pass is optional,
not required.
