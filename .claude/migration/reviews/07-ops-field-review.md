# Layer 07 — ops (wave A): field-domain verbs — review

Reviewed files: `src/postgkyl/ops/{fft,magsq,relchange,mask,collect,grid,val2coord,
extract_input,fit,growth,differentiate,ev}.py`, `src/postgkyl/ops/__init__.py`
(re-export additions), `tests/test_ops_{field,collect,fit,growth,differentiate,ev}.py`.

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. Every verb is a short, self-contained
  function: read the guard, read the delegation to `numerics`, read the
  `_result(...)` call. No fact needed from outside the module to understand a
  verb's behavior.
- **I. Data is inert. Functions transform.** Adheres. All twelve verbs are
  plain functions `(GDataState, ...) -> GDataState` (or a terminal scalar/str/
  `DatasetGroup`); no new classes, no behavior attached to data.
- **II. Make illegal states unrepresentable.** Adheres, with one soft spot.
  Every verb guards `data.backend == "gkyl"` before touching NumPy semantics
  (`fft.py:46`, `magsq.py:35`, `relchange.py:15`, `mask.py:51`, `collect.py:54`,
  `grid.py:38`, `val2coord.py:73`, `fit.py:57`, `growth.py:50`,
  `differentiate.py:54`, `ev.py` via `select()`). `grid.py:46-49` additionally
  validates the grid/`num_dims` shape before indexing. The one soft spot is
  `mask.py`'s `mask_data` component-count precondition, which is documented
  but not actually checked before the `np.repeat` (see C2) — the illegal state
  is refused, but late and with an unrelated-looking error, not by construction.
- **III. A function is one idea.** Adheres. `collect`/`grid`/`val2coord`/
  `fit`/`growth` each do one job; `ev.py` splits cleanly into
  `apply_operator` (stack reduction), `_push_token` (token resolution), and
  `ev` (the public entry point).
- **IV. The signature tells the whole truth.** Adheres for parameters
  (keyword-only options throughout, no stringly-typed flags). One prose
  overclaim: `mask.py`'s docstring promises behavior ("evenly divide") the
  signature's implementation does not deliver (C2) — an outward-truth gap in
  the docstring, not the signature itself.
- **V. Every fact has one home.** Adheres. `differentiate.py` does not
  reimplement gradient math — it calls `numerics.ev_ops.grad`/`grad2`, the
  same functions `ev.py`'s `grad`/`grad2` tokens use, so there is exactly one
  gradient implementation shared by both entry points.
- **VI. Separate what from how.** Adheres. Every verb unwraps
  `grid`/`values`/`ctx` and hands the math to `numerics`; none reimplements
  FFT, fitting, or growth-rate math locally.
- **VII. Notation is execution; lowering is transliteration.** Not
  centrally applicable to this layer (no spec/lowering pair is introduced
  here); the one relevant case, `ev.py`'s RPN grammar, reproduces the
  `numerics.ev_cmds` table's arity contract exactly (byte-compatible tokens
  per the instruction file).
- **VIII. Earn your abstractions.** Adheres. `_require_field_domain` in
  `relchange.py` is justified by its two call sites in the same function.
  `_get_range` in `val2coord.py` is deliberately *not* unified with
  `numerics.idx_parser` (different grammar, single caller) — the module
  docstring calls this out explicitly rather than forcing a premature shared
  abstraction.
- **IX. An abstraction is a contract.** Mostly adheres. Every verb honors the
  `_result(...)` contract (returns the caller's concrete class, propagates
  `inplace`/`tag`/`label`). `ev.py:219-230` is the one place that reaches
  around the contract — it constructs via `_result(...)` and then directly
  overwrites `result.ctx` because `_result`'s `ctx_updates` are additive-only
  and cannot express "replace, don't merge" (needed to drop conflicting
  operand ctx keys per the RPN merge semantics). The workaround is correct
  and commented, but it means one verb depends on `GDataState.ctx` being a
  freely-mutable public attribute rather than going through the verb
  contract's single decision point — a minor crack in "an abstraction is a
  contract," not a bug.
- **X. Trust the most formal thing first.** Adheres. No type system is in
  play here beyond annotations; the layer leans on tests (100% line coverage,
  analytic assertions) rather than docs, consistent with the doctrine's
  ranking.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports, `postgkyl` not `postgkeyll`).** Adheres — every new
  file imports `from postgkyl...`. All new files use absolute imports
  (`from postgkyl.numerics import ...`, `from postgkyl.core.group import
  DatasetGroup`) rather than relative; this matches the pre-existing
  convention already established in `select.py`/`interpolate.py`, not a
  regression introduced here.
- **2 (respect the layer DAG).** Adheres, verified: `test_import_contract_no_violations`
  passes with no new entries needed in `_ALLOWED["ops"]` — every new import
  (`core`, `core.group`, `core.state`, `numerics`) was already licensed.
- **4 (no typer/ctypes).** Adheres — none present.
- **5 (`__init__.py` re-exports only).** Adheres — `ops/__init__.py`'s diff is
  pure `from .x import x` plus `__all__` additions.
- **6 (type-annotate every public function).** Partially violates, but
  matches established house style: every new verb annotates its parameters
  but omits the return type (e.g. `fft.py:14`, `growth.py:20`,
  `differentiate.py:26`), exactly mirroring the pre-existing exemplars
  `select.py`/`interpolate.py`, which have the same gap. Not a regression
  introduced by this layer, but also not fixed.
- **7 (keyword-only options).** Adheres throughout — every boolean/optional
  parameter after the data argument(s) is keyword-only.
- **8 (no mutable default arguments).** Adheres — `guess=None`,
  `mask_data=None`, etc.; no `[]`/`{}` defaults.
- **9 (arrays in/out for numerics; GDataState unwrapped in ops).** Adheres —
  every verb unwraps `grid`/`values` before calling `numerics.*`, and no
  "GData-or-tuple" dual-input pattern was ported.
- **10 (raise, don't print-and-continue).** Adheres for this layer's own
  code — every guard raises `ValueError` naming the offending state and the
  fix (`.interp() first` style, consistently copied from `select.py`).
- **11 (pure core, effects at the edges).** Adheres — no I/O, printing, or
  plotting in any of the 12 new verbs.
- **12 (frozen records; grandfathered `ctx`).** Adheres under the
  grandfather clause — `fit.py`'s `fit_params`/`fit_std`/`fit_R2` and
  `growth.py`'s `growth_rate` are new `ctx` keys, consistent with existing
  practice (`interpolated`, `representation`, etc.).
- **14 (NumPy discipline; no bare `==` on floats in tests).** Mostly adheres.
  `tests/test_ops_ev.py:78-80` compares floats with a bare `==`
  (`... == 1.0`, `... == 4.0`, `... == 2.5`) instead of
  `np.testing.assert_allclose`/`pytest.approx`; the values happen to be exact
  in binary floating point (min/max of literals, and 2.5 = 10/4 is exact), so
  it is not flaky today, but it is a rule-14 violation (see C4).
- **17 (≥ ~100% coverage, justified misses reported).** Exceeded — measured
  100% line coverage on every `ops/*.py` module touched by this layer (see
  Coverage below), against a 90% floor. No implementer report was found on
  disk (`.claude/migration/reviews/` had no prior 07 entry and no report file
  exists elsewhere under `.claude/migration/`) to check claimed vs. measured
  numbers against; the numbers below are independently measured, not
  inherited from a claim.
- **18 (tests assert values via analytic cases).** Adheres well — sine-wave
  FFT peak check, exact linear/quadratic/gaussian/plane fit recovery,
  analytic growth-rate recovery, analytic gradient of `x^2 + y`, RPN-vs-direct
  parity (`ops.ev("f0 f1 +", ...)` vs. direct arithmetic intent).
- **19 (independent, deterministic tests).** Adheres — no RNG, no network, no
  filesystem writes; the one file-backed test (`test_rejects_modal_data`)
  reads from `tests/test_data/` and is skip-gated on `ffi.available()`.
- **20 (architecture tests sacred).** Adheres, verified —
  `test_facade_is_pure_reexport`, `test_import_contract_no_violations`,
  `test_foreign_floor_confined_to_ffi`, `test_import_graph_is_acyclic`, and
  the full `tests/test_postgkyl.py` (32/32) pass.
- **21 (copy liberally; document numerical divergence).** Adheres, with one
  disclosed, tested, and — on inspection — *correct* divergence: `fft.py:51-56`
  inserts a nodal→cell-centered grid conversion before calling
  `numerics.fft` that `src_bak`'s `tools/fft.py`/`ops/fft.py` never had.
  `src_bak`'s FFT computes its sample count as `N = len(grid[0])`; when fed
  the nodal (edge) grid that `.interp()` actually produces (one longer than
  `values`), that `N` is off by one from the true sample count, producing a
  frequency axis for a hypothetical `N+1`-sample signal instead of the real
  `N`-sample one — a latent bug in `src_bak` for exactly the "real workflow"
  case (`file.gkyl interp fft`) that matters. The new code detects the
  length mismatch and normalizes to a matching cell-centered grid first;
  `tests/test_ops_field.py::TestFft::test_analytic_sine_peak` is a real
  regression guard for this (it would fail under the old, unconverted
  behavior, confirmed by manual trace). This is exactly the "documented
  intentional change" the rule asks for, not a silent one.

## Criticisms

**C1 (major, but scoped to `io/`, not this layer).**
`src/postgkyl/ops/extract_input.py:34-38` reads `data.ctx.get("input_file")`,
but no reader in `src/postgkyl/io/` ever populates that key (grepped
`io/*.py` for `input_file`/`inputfile`: zero matches). `src_bak`'s
`extract_input` worked by re-reading a file attribute (`get_input_file()` →
`fh.read_attribute_string("inputfile")`) at call time, independent of `ctx`.
The migration changed the mechanism to "decode from `ctx`" (per this layer's
own instruction file: "Base64-decode the embedded input file from ctx"), but
no layer has yet wired a reader to fill that key — so `extract_input()`
**always returns `""` on every real Gkeyll file today**, a full, currently
undiscoverable capability regression. It is honestly disclosed in the module
docstring, and the instruction file's wording arguably licenses exactly this
(read from `ctx`, don't reach back into `io`), so it is not a rule violation
of this layer's contract — but it is unverified against any real ADIOS2 file
with an embedded input in the test suite, and it is untracked: no persisted
implementer report exists, `CHECKPOINTS.md` doesn't mention it, and the
04-io layer review doesn't mention the `inputfile` attribute at all.
*Fix*: file a tracked follow-up against `io/gkyl_adios_reader.py` to read the
ADIOS2 `inputfile` attribute into `ctx['input_file']` (mirroring
`src_bak`'s `read_attribute_string("inputfile")` call), and add a
`test_data` fixture that actually has one so this verb gets exercised
end-to-end at least once anywhere in the suite.

**C2 (minor).** `src/postgkyl/ops/mask.py:33-35,59` documents that
`mask_data`'s "component count must be 1 or evenly divide `data`'s", but the
implementation (`np.repeat(mask_field, data.num_comps, axis=-1)`) only
actually works when `mask_field` has exactly one component — for any
`mask_field` with `k > 1` components, `np.repeat` produces
`k * data.num_comps` elements (not `data.num_comps`), which does not
broadcast against `values` and raises a `ValueError` from
`np.ma.masked_where` rather than "evenly dividing." This is inherited
unchanged from `src_bak` (same call, same limitation), so it is not a new
numerical bug — but the docstring's "evenly divide" claim is new prose that
overclaims what the ported code does, and no test exercises a multi-component
`mask_data` to catch the gap (`tests/test_ops_field.py::TestMask::test_mask_from_dataset`
only covers the 1-component case). *Fix*: narrow the docstring to "must have
exactly one component" (matching the code), or implement the tiling the
docstring promises (e.g. `np.tile` per-block instead of `np.repeat`) and add
a test for `k > 1`.

**C3 (informational; not currently reachable).**
`src/postgkyl/ops/collect.py:60` computes the per-frame time stamp as
`dat.ctx.get("time", dat.ctx.get("frame", i))`, which differs from
`src_bak`'s `stamp = ctx.get("time"); if stamp is None: stamp = ctx.get("frame")`
in one edge case: if a dataset's `ctx` explicitly stores `"time": None`
(as opposed to omitting the key), `src_bak` falls through to `"frame"`/the
positional index, while the new code returns `None` directly (`dict.get`'s
default only applies when the key is *absent*, not when its value is
falsy/`None`). No reader in `src/postgkyl/io/` ever sets `ctx["time"] = None`
explicitly (they only set the key when the file has real time data — see
`gkyl_h5_reader.py:60`, `gkyl_adios_reader.py:165`), so this is unreachable
with any current loader; noted for completeness, not as a blocking defect.

**C4 (nit).** `tests/test_ops_ev.py:78-80` compares floats with a bare `==`
(`... == 1.0`, `... == 4.0`, `... == 2.5`) rather than
`np.testing.assert_allclose`/`pytest.approx`, contrary to
PYTHON_PRINCIPLES §14. The specific values are exact in IEEE-754 double
(min/max of literal array entries; `2.5` is exactly representable and the
underlying sum/divide are both exact for this input), so the test is not
flaky — but it sets a bad precedent to copy from later, and costs nothing to
fix. *Fix*: swap to `pytest.approx` for consistency with every other
numeric assertion in the same file.

No correctness bugs were found in the numerics delegation itself: `fit.py`'s
guess-forwarding, `growth.py`'s `p0`-omission-when-`None` (which correctly
avoids `numerics.fit_growth`'s `np.asarray(p0, dtype=float)` raising on a
bare `None` — a real crash risk that `src_bak`'s call site did not have to
worry about, because `src_bak`'s own `fit_growth` used `best_params = p0`
without the `asarray` wrap), `collect.py`'s sort/fold logic, `grid.py`'s three
grid-shape branches, and `differentiate.py`'s `grad`/`grad2` dispatch were
all traced against `src_bak` line-by-line and found to preserve numerical
behavior exactly (or to improve it, per C-adjacent note under Principle 21).

## Coverage

Measured directly (`pytest --cov` fails to collect in this environment due to
a NumPy/`coverage` double-import interaction unrelated to this layer; used
`coverage run -m pytest` + `coverage report` instead, which is equivalent):

```
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
src/postgkyl/ops/__init__.py           20      0   100%
src/postgkyl/ops/arithmetic.py        126      0   100%
src/postgkyl/ops/collect.py            30      0   100%
src/postgkyl/ops/differentiate.py      12      0   100%
src/postgkyl/ops/ev.py                102      0   100%
src/postgkyl/ops/extract_input.py       8      0   100%
src/postgkyl/ops/fft.py                12      0   100%
src/postgkyl/ops/fit.py                42      0   100%
src/postgkyl/ops/grid.py               22      0   100%
src/postgkyl/ops/growth.py             24      0   100%
src/postgkyl/ops/info.py                5      0   100%
src/postgkyl/ops/integrate.py          16      0   100%
src/postgkyl/ops/interpolate.py        20      0   100%
src/postgkyl/ops/magsq.py               8      0   100%
src/postgkyl/ops/mask.py               19      0   100%
src/postgkyl/ops/plot.py               11      0   100%
src/postgkyl/ops/relchange.py          11      0   100%
src/postgkyl/ops/represent.py          40      0   100%
src/postgkyl/ops/select.py             35      0   100%
src/postgkyl/ops/val2coord.py          38      0   100%
-----------------------------------------------------------------
TOTAL                                 601      0   100%
```

100% on every module this layer touched (`fft`, `magsq`, `relchange`, `mask`,
`collect`, `grid`, `val2coord`, `extract_input`, `fit`, `growth`,
`differentiate`, `ev`), well above the 90% floor the instruction file sets.
No implementer report exists to cross-check claimed misses/justifications
against — there simply are no misses to justify. Full suite: 790 passed (via
plain `pytest`) / 790 passed (via `coverage run -m pytest`), 0 failures,
0 skips observed in this environment (the `needs_gkeyll`-gated modal-refusal
tests ran, i.e. the compiled `libg0core.so` is available here).

## Verdict

**PASS (fixer optional).** All twelve verbs are faithful, well-guarded ports
that funnel through the existing `_result(...)` contract, delegate every
numeric computation to `numerics/`, and reject modal (gkyl-backed) input with
the house `.interp() first` guard style. Coverage is 100% (exceeding the 90%
floor) and the full suite plus all four sacred architecture tests pass with
no new DAG edges. The one genuinely undesirable finding, C1, is a real
capability gap (`extract_input` is inert against every current reader) but
it is honestly disclosed in the code's own docstring and is arguably licensed
by the instruction file's exact wording ("decode... from ctx"), so it reads
as a known, tracked-by-neither-report gap rather than a defect introduced
against spec — it belongs to a future `io/` follow-up, not a re-do of this
layer. C2–C4 are documentation/test-hygiene nits with no numerical
consequence. Nothing here requires re-implementation; a fixer pass to correct
the `mask.py` docstring, tighten `test_ops_ev.py`'s float comparisons, and
open a follow-up ticket for `extract_input`/`ctx['input_file']` would close
the loop but is optional.

## Resolutions

**C1: DECLINED (accepted as out-of-scope).** Confirmed by re-inspection:
`src/postgkyl/io/*.py` still has zero writers of `ctx['input_file']`
(`grep -rn "input_file" src/postgkyl/io/` returns nothing), so
`ops/extract_input.py` continues to always return `""` against every current
reader. The fix belongs entirely to `io/` — this layer's instruction file
scopes it to "Base64-decode the embedded input file from ctx", which this
verb does correctly; there is no `ops/`-side code change that closes the
gap without reaching into `io/` and violating the layer boundary (rule 2,
"respect the layer DAG" — `ops` may not gain new responsibilities that
belong to `io`). Recording this explicitly so it is tracked rather than
silently dropped: **a follow-up is needed against `io/gkyl_adios_reader.py`
(and any other ADIOS2/HDF5 reader) to populate `ctx['input_file']` from the
file's embedded `inputfile` attribute, plus a `tests/test_data/` fixture
that actually carries one**, so `extract_input()` gets exercised
end-to-end at least once. No code changed in this layer for C1.

**C2: FIXED.** `src/postgkyl/ops/mask.py`'s docstring overclaimed that
`mask_data`'s component count "must be 1 or evenly divide" `data`'s; traced
the `np.repeat(mask_field, data.num_comps, axis=-1)` call
(`mask.py:66`) by hand for a `k=2`-component mask against `m=2`-component
data: `np.repeat` produces `k*m = 4` trailing entries, not `m = 2`, so the
"evenly divide" case never actually works — the implementation only
supports `k=1`. Narrowed the docstring (`mask.py:22-25,33-40,52-56`) to
state the true, narrower contract: `mask_data` must have exactly one
component, and a multi-component `mask_data` raises `IndexError` from
`np.ma.masked_where`'s shape check (verified directly: constructed a
`(5,2)` mask against `(5,2)` data and confirmed the actual exception type
is `IndexError`, not a generic broadcast `ValueError` — the "Raises" section
now names it correctly). Declined to implement the `np.tile`-based
"evenly divide" behavior the old docstring promised: that would be new
functionality beyond what `src_bak` ever supported (rule 21 — copy
liberally, don't invent), and no caller in this layer or its tests needs
it. Added a regression test,
`tests/test_ops_field.py::TestMask::test_mask_from_dataset_multi_component_raises`,
that passes a 2-component `mask_data` against 2-component data and asserts
the `IndexError`, so the k>1 gap is now covered instead of silently
untested.

**C3: ACKNOWLEDGED — no code change.** Confirmed the review's trace:
`collect.py`'s `dat.ctx.get("time", dat.ctx.get("frame", i))` differs from
`src_bak`'s `None`-check fallthrough only when a dataset's `ctx` explicitly
stores `"time": None` (as opposed to omitting the key), which no current
reader in `src/postgkyl/io/` does (`gkyl_h5_reader.py`/`gkyl_adios_reader.py`
only ever set `ctx["time"]` to a real value when present, never to `None`).
Since the divergent branch is unreachable with every loader that exists
today, there is nothing to fix without inventing a reader behavior that
doesn't exist; changing `collect.py` speculatively to guard against a state
no code produces would be complexity ahead of need (doctrine VIII — earn
your abstractions, don't pre-defend against a hypothetical). Left as
informational, consistent with the review's own verdict that this is not a
blocking defect.

**C4: FIXED.** `tests/test_ops_ev.py:78-80` (`TestMinMaxMean`-style
assertions in `test_min_max_mean`) compared floats with bare `==`. Replaced
all three with `pytest.approx(...)` per PYTHON_PRINCIPLES §14 ("never
compare floats with `==` in tests"). Verified the swap doesn't mask a
regression: reran the test in isolation
(`PYTHONPATH=src python -m pytest tests/test_ops_ev.py::test_min_max_mean -q`)
— still passes, now via `pytest.approx` rather than exact equality.

### Verification

Full suite after fixes: `PYTHONPATH=src python -m pytest tests/ -q` →
**791 passed** (790 + 1 new regression test for C2's k>1 case).
`ops/` coverage re-measured via `coverage run -m pytest tests/ -q` +
`coverage report --include="src/postgkyl/ops/*"`: **100% (601/601
statements)**, unchanged from the pre-fix measurement — `mask.py` stayed at
19/19 statements (docstring-only change plus a docstring-accurate `Raises`
entry; no new guard branch was added, since C2 was declined as a
docstring/test fix, not a new-check fix).
