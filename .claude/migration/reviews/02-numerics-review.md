# Layer 02 — numerics: review

Scope reviewed: `src/postgkyl/numerics/{calculus,mag_sq,rel_change,rotation_matrix,
fft,fit,growth,filters,ev_ops,grid_centering,downsample}.py`,
`src/postgkyl/numerics/__init__.py` (diff), and the corresponding
`tests/test_numerics_*.py`. Every new/changed file was read in full and
diffed conceptually against its `src_bak/postgkyl/{tools,utils}/*.py`
original.

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. Every function takes plain arrays/
  scalars and returns plain arrays/tuples; nothing requires reading another
  module to understand a function's behavior, except the two duplicated
  `_parse_axis` helpers (see C4), which forces a reader to compare two files
  to know whether they agree.
- **I. Data is inert. Functions transform.** Adheres. No classes anywhere in
  the diff; every module is free functions over arrays/dicts.
- **II. Make illegal states unrepresentable.** Not applicable in the strong
  sense — this layer has no constructors/types to guard. `ev_ops.cmds`'
  entries are a plain dict-of-dicts (`{"num_in":..., "num_out":..., "func":...}`)
  rather than a frozen record, but the layer instruction file explicitly
  mandates keeping "the table's keys and arities identical so layer 07's `ev`
  verb can consume it unchanged" — this is an authorized exception, not a
  violation.
- **III. A function is one idea.** Adheres for nearly everything. `ev_ops.py`'s
  `curl` is the one borderline case (one function, three dimensionality
  branches with different validation rules) — but that mirrors the math
  (1D/2D/3D curl genuinely differ) rather than mixing unrelated concerns, so
  it reads as one idea with three cases, not two ideas.
- **IV. The signature tells the whole truth.** Adheres. `growth.fit_growth`
  is the one function whose signature does not disclose that it prints to
  stdout on every call (`src/postgkyl/numerics/growth.py:51,69-71,73,77`) —
  see C1. Every other function is effect-free and its signature is complete.
- **V. Every fact has one home.** Violates in one place: axis-string parsing
  (`"0,1"` / `"0:2"` / bare int) is implemented twice, in
  `calculus.py:15-32` (`_parse_axis(axis, num_dims)`) and
  `ev_ops.py:196-214` (`_parse_axis(axis)`), with overlapping but not
  identical bodies (see C4). Everywhere else — `FIT_FUNCTIONS`/`FIT_NDIM`,
  `RPN_OPERATORS`/`RPN_FUNCTIONS`, `cmds` — is a single table with one owner.
- **VI. Separate what from how.** Adheres, and is the layer's best-executed
  principle: `filters.py`'s module docstring and signature change (`cutoff`
  now required, no matplotlib picker) is exactly the "effects belong at the
  edge, machinery stays below" call the instruction file asked for. The one
  crack is `growth.fit_growth`'s printing (C1) — an interactive-progress
  effect leaking into a leaf module that is supposed to be effect-free.
- **VII. Notation is execution; lowering is transliteration.** Adheres.
  `calculus.py` and `fft.py`'s module docstrings state precisely what was
  dropped (unimplemented `grad`/`div`/`curl` stubs) and where the real
  vector-calculus operators actually live (`ev_ops.py`), so the spec layer
  does not silently lie about capability.
- **VIII. Earn your abstractions.** Adheres, modulo C4 (a premature
  non-abstraction: two near-duplicate helpers instead of one shared one, or
  two honestly-separate one-off inlined blocks).
- **IX. An abstraction is a contract.** Adheres for `cmds`: the contract
  (`num_in`/`num_out`/`func`, `func(in_grid, in_values) -> ([grid],[values])`)
  is stated in the module docstring and every entry honors it uniformly.
- **X. Trust the most formal thing first.** Adheres well: 100%-line-covered
  by value-asserting tests (analytic integrals, analytic curl/divergence,
  seeded fit recovery) rather than shape-only tests — see Coverage below.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports, no `postgkeyll`).** Adheres — `grid_centering.py`
  drops the old `postgkeyll` `TYPE_CHECKING` import entirely; no module
  imports anything outside `numerics/` itself.
- **2 (respect the layer DAG).** Adheres — `numerics/` imports only `numpy`,
  `scipy.{fft,optimize,signal}`, `sys`, `typing`, and its own siblings via
  relative import (`ev_ops.py` → `.idx_parser`). Verified
  `test_import_contract_no_violations` / `test_import_graph_is_acyclic` /
  `test_foreign_floor_confined_to_ffi` all pass.
- **4 (no typer, no ctypes).** Adheres — every `typer.echo`/`typer.style`
  call in `src_bak/postgkyl/tools/ev_ops.py` (divergence/curl warnings) and
  `tools/fft.py`/`tools/fit.py` callers is gone; converted to `raise
  ValueError` per rule 10 (see C2 for the documentation gap around that
  conversion).
- **5 (`__init__.py` re-exports only).** Adheres — the diff only adds
  `from .x import y` lines and an `__all__` list; no `def`/`class` added.
- **6/7/8 (type-annotate, kw-only booleans, no mutable defaults).** Adheres
  throughout: `fft(..., *, psd=False, iso=False)`,
  `fft_filtering(..., *, cutoff)`, no mutable default args anywhere (`p0:
  list | None = None`, `p0: tuple = (1, 1)`).
- **9 (arrays in/out, no dual-input).** Adheres — this is the layer's core
  mandate and it is met cleanly: every function takes `(grid, values, ...)`
  or plain arrays; `utils/input_parser.py` was correctly not ported (grep
  confirms zero references to `input_parser` anywhere in `src/postgkyl/numerics/`).
- **10 (raise, don't print-and-continue).** Mostly adheres — the
  `typer.echo`-warning-then-continue pattern in `divergence`/`curl` was
  converted to `raise ValueError`, which is exactly what this rule asks for.
  But rule 11 is violated by the same file's sibling module, `growth.py`
  (C1): `print`/`sys.stdout.write` progress reporting was carried over
  verbatim from `src_bak` rather than removed.
- **11 (pure core, effects at the edges).** Violates — see C1.
- **13 (constants have one home).** Not applicable; no physical constants
  appear in this layer.
- **17 (one test file per module, ~100% coverage).** Adheres in substance;
  `mag_sq`/`rel_change`/`rotation_matrix` share `test_numerics_misc.py`
  rather than three separate files, but that mirrors the source grouping the
  layer file itself names (`tests_bak/test_tools_misc.py`) — not a
  deviation worth flagging. Coverage is 100% for every file in scope
  (measured directly, see Coverage below), exceeding the ≥95% bar.
- **18 (assert values, not shapes).** Adheres well: quadratic/linear
  analytic integrals in `test_numerics_calculus.py`, analytic curl/divergence
  in `test_numerics_ev_ops.py`, seeded-noise parameter recovery in
  `test_numerics_fit.py`/`test_numerics_growth.py`.
- **19 (independent, deterministic tests).** Adheres — no unseeded RNG found
  in the new test files (fit/growth tests use exact analytic data, not
  random noise, so no seeding is even needed); no network; no ordering
  dependence observed (full suite passes with default `pytest` ordering).
- **21 (copy liberally, document behavioral differences).** Two fixed
  latent bugs are copied down *and* documented and tested exactly as rule 21
  requires: the `range(str, str)` axis-slice bug (`calculus.py:56-61` test,
  `test_numerics_calculus.py:55-61`) and the `nkx == 1 & nky == 1`
  operator-precedence bug in `fft.py:155-162,187-190` (documented inline,
  tested in `test_numerics_fft.py`). One behavioral change is present but
  under-documented at the point of change (C2), and one inherited-but-latent
  bug was neither fixed nor flagged (C3).
- **23 (never edit `src_bak`/`tests_bak`).** Adheres — `git status` shows no
  modifications under either tree.
- **24 (leave the tree green).** Adheres — `PYTHONPATH=src python -m pytest
  tests/ -q` passes: 522 passed, 1 skipped, 0 failed.

## Criticisms

**C1 — `growth.fit_growth` prints progress to stdout from a "pure NumPy
math" leaf module.**
`src/postgkyl/numerics/growth.py:51,67-71,73,77`. The layer's own mission
statement says functions here "take plain arrays (and scalars) and return
plain arrays" and PYTHON_PRINCIPLES §11 says effects belong at the edges
(io/render/cli), not in numerics. `fit_growth` calls `print(...)` before the
scan, `sys.stdout.write`+`sys.stdout.flush()` on every iteration of an
`O(N)` loop, and `print(...)` again at the end — carried over verbatim from
`src_bak/postgkyl/tools/growth.py`. Failure scenario: any caller that
invokes `fit_growth` inside a larger batch job, a Jupyter widget, or a
non-TTY log pipe gets an unrequested, unsilenceable wall of `\r`-carriage
progress text; tests already have to work around it with `capsys` fixtures.
Fix: strip the `print`/`sys.stdout` calls (or gate them behind an explicit
`verbose: bool = False` keyword-only parameter honestly declared in the
signature), matching how `filters.py` in this same layer already stripped
its interactive effect.

**C2 — `divergence`/`curl`'s warn-and-continue → raise conversion is
undocumented at the call site.**
`src/postgkyl/numerics/ev_ops.py:262-266,312-317,324-327`. `src_bak`'s
`divergence`/`curl` printed a `typer.echo` warning when the component count
exceeded the dimension count and then *still computed a result* using only
the first `num_dims` (or first 3) components. The port replaces every one of
those warnings with `raise ValueError(...)` — the right call per
PYTHON_PRINCIPLES §10, and it is proven by tests
(`test_numerics_ev_ops.py:306-310,358-362,370-374`). But nothing in
`ev_ops.py` itself says so; a maintainer reading the source next to
`src_bak` would have to diff the two files to discover that a previously
non-fatal, partially-computed-and-warned case is now a hard failure for
existing callers that relied on the graceful degradation. Fix: one-line
comment at each raise, e.g. "`src_bak` warned and computed a partial result
here; this raises instead per PYTHON_PRINCIPLES §10" (the module docstring
already does this well for the `mult`/`divide` transpose trick and
`scale_zi_axis`'s aliasing — this is the one place the pattern was skipped).

**C3 — `fit_growth` inherits a crash if every fitting window fails to
converge.**
`src/postgkyl/numerics/growth.py:47,72,76`. `best_params` is initialized to
the caller-supplied `p0` tuple. If `opt.curve_fit` raises `RuntimeError` for
*every* `n` in the scan range (all windows fail to converge), `best_params`
is never reassigned to an ndarray, and line 76 (`best_params[1] =
best_params[1]/max_x`) then attempts item assignment on a `tuple`, raising
`TypeError: 'tuple' object does not support item assignment` instead of a
clear domain error. This is inherited unchanged from
`src_bak/postgkyl/tools/growth.py:76`, so it is not a new bug introduced by
the port, but the instruction file's porting rules ask agents to "prove [a
fix] with a test and document it" when old code had a bug worth fixing —
this one was neither fixed nor flagged in-file. `test_numerics_growth.py`
covers the "some windows fail" path (`test_curve_fit_failure_for_some_windows_is_skipped`)
but not the "all windows fail" path, so this crash is untested. Fix: convert
`p0` to a mutable array up front (`best_params = np.asarray(p0, dtype=float)`)
so the reassignment always works, or raise a clear `RuntimeError("fit_growth:
no fitting window converged")` when `best_R2` is still `0.0` at the end.

**C4 — Axis-string parsing is implemented twice with silently diverging
bodies.**
`src/postgkyl/numerics/calculus.py:15-32` and
`src/postgkyl/numerics/ev_ops.py:196-214`. Both are private `_parse_axis`
helpers that parse `int`/`tuple`/comma-string/colon-slice-string into a
tuple of axes, and both exist because `ev_ops.integrate`'s axis comes off an
RPN value stack (so it also needs to handle bare `float`/`np.ndarray` and
the `"all"` sentinel) while `calculus.integrate`'s axis is a direct
parameter (so it also needs to handle `None` and bare `int`). The overlap
(comma-split and colon-split bodies) is copy-pasted rather than shared. This
is Doctrine V's exact failure mode: if the colon-slice bug fix (already
applied and tested in `calculus.py`, per PYTHON_PRINCIPLES §21) needs a
second fix later, a maintainer has to remember there is a second, differently-
shaped copy in `ev_ops.py` to update too. Severity is minor because the two
functions are not literally identical (different accepted input types), so
there is no premature-abstraction case for merging them outright, but at
minimum a shared private `_split_axis_string(s: str) -> tuple[int, ...]`
for just the comma/colon-string branch (the part that is byte-for-byte
identical) would remove the duplication rule V forbids.

**C5 (minor) — `fft.py`'s `iso=True` path is well-tested in isolation but
not exercised end-to-end through `fft()` itself with real 3D PSD data in a
single test that checks shell-averaging conservation (e.g. total power
before/after binning).** Coverage is 100% line-wise (the `iso` branch does
execute), but the instruction file's own "add what they miss" list does not
mention this, and no test asserts the physically meaningful invariant that
isotropic binning preserves total spectral power (mean-of-shell × count ==
sum of the shell's contributions). This is a coverage-vs-correctness gap
that line coverage cannot see. Not blocking — the existing tests do assert
values, not just shapes, for the sub-pieces (`init_polar`/`polar_isotropic`)
— but worth a follow-up test if `fft(iso=True)` is ever relied on for
quantitative spectral analysis.

## Coverage

Measured directly with `PYTHONPATH=src python -m coverage run -m pytest
tests/ -q` (plain `pytest --cov=...` hit an unrelated numpy
"cannot load module more than once per process" collection error in this
environment; `coverage run -m pytest` avoids it and measures the same
statements) followed by `coverage report --include="*/postgkyl/numerics/*" -m`:

```
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src/postgkyl/numerics/__init__.py             14      0   100%
src/postgkyl/numerics/calculus.py             35      0   100%
src/postgkyl/numerics/downsample.py           27      0   100%
src/postgkyl/numerics/elementwise.py          10      0   100%
src/postgkyl/numerics/ev_ops.py              231      0   100%
src/postgkyl/numerics/fft.py                 119      0   100%
src/postgkyl/numerics/filters.py              22      0   100%
src/postgkyl/numerics/fit.py                 171      0   100%
src/postgkyl/numerics/grid_centering.py       24      0   100%
src/postgkyl/numerics/growth.py               39      0   100%
src/postgkyl/numerics/idx_parser.py           43      0   100%
src/postgkyl/numerics/mag_sq.py                7      0   100%
src/postgkyl/numerics/rel_change.py            8      0   100%
src/postgkyl/numerics/rotation_matrix.py      16      0   100%
------------------------------------------------------------------------
TOTAL                                        766      0   100%
```

100% line coverage on every file in the layer, well above the ≥95%
threshold, with no misses to justify. Line coverage does not, however,
catch C3 (the all-windows-fail crash in `growth.py`, which sits on an
already-covered line but is never reached with the failing-precondition
state) or C5 (missing a physically-meaningful assertion for `fft(iso=True)`)
— both are branch/assertion gaps, not statement gaps, and are called out
above rather than in this table.

## Verdict

**PASS WITH FIXES.** The port is numerically faithful — every ported
function was compared line-by-line against its `src_bak` original and the
math bodies are unchanged except for two already-fixed-and-documented
latent bugs (string-range axis parsing, `&`-vs-`==` polar-binning
precedence) and one deliberate, principle-mandated warn→raise conversion
that is tested but not commented at the call site (C2). The layer stays a
true leaf (verified against the import-contract/acyclic/foreign-floor
tests), keeps `numerics/` free of `GData`/`ctx`/typer/matplotlib as
mandated, and has 100% line coverage backed by value-level (not
shape-level) assertions. None of the five criticisms are numerically
wrong — nothing here silently produces a different number than `src_bak`
for any input a caller was actually relying on — so this is not a FAIL. But
C1 (stdout side effects in a leaf module) is a real doctrine/principle
violation that a fixer should remove before layer 07's `ops.ev`/growth
verbs build on top of it and inherit the same non-purity, and C3 is a
genuine unhandled-crash path worth closing with a one-line guard while the
file is open. C2 and C4 are cheap documentation/dedup fixes. None require
re-implementation.

## Resolutions

C1: FIXED — Removed the `print`/`sys.stdout.write`/`sys.stdout.flush`
progress-reporting calls from `fit_growth` and the now-unused `import sys`
(`src/postgkyl/numerics/growth.py:1-8,44-79`, was `:1-9,44-78`). The leaf
module is now effect-free per PYTHON_PRINCIPLES §11: it takes arrays,
returns arrays, and never touches stdout. Verified by
`tests/test_numerics_growth.py` (the `capsys` fixture/assertions that
existed only to work around the old prints were removed from
`test_recovers_known_growth_rate`, `test_returns_three_elements`,
`test_best_N_is_within_bounds`, `test_custom_min_N`,
`test_curve_fit_failure_for_some_windows_is_skipped`,
`test_custom_function_is_used`) and the full suite passing with no stdout
assertions remaining for this function.

C3: FIXED — `best_params` is now initialized as `np.asarray(p0,
dtype=float)` instead of the caller-supplied tuple, so the closing
`best_params[1] = best_params[1]/max_x` item-assignment never hits a
`tuple` (`src/postgkyl/numerics/growth.py:50`). Additionally, if no window
ever improves on the initial `best_R2 = 0.0` (every `curve_fit` call
raised `RuntimeError`, or — the same underlying bug — every window that
did converge produced a non-positive R²), `fit_growth` now raises a clear
`RuntimeError("fit_growth: curve_fit failed to converge for every window
in [...]")` instead of silently returning a meaningless
initial-guess-derived result (`growth.py:73-77`). Proven by the new test
`test_all_windows_failing_to_converge_raises`
(`tests/test_numerics_growth.py:79-93`), which monkeypatches
`opt.curve_fit` to always raise and asserts the `RuntimeError` is now
raised instead of crashing with `TypeError: 'tuple' object does not
support item assignment`.

C4: FIXED — Extracted the byte-for-byte-identical comma/colon-string
parsing branch into a single shared helper,
`calculus._split_axis_string(axis: str) -> tuple`
(`src/postgkyl/numerics/calculus.py:15-29`), documented as the one home
for that grammar (Doctrine V). `calculus._parse_axis` now delegates to it
(`calculus.py:40-41`); `ev_ops._parse_axis` imports it
(`src/postgkyl/numerics/ev_ops.py:18`) and delegates its own string branch
to it too (`ev_ops.py:196-203`), keeping only the genuinely
non-overlapping type dispatch (`float`/`np.ndarray`/`"all"` for `ev_ops`,
`None`/bare `int` for `calculus`) local to each function. No behavior
changed — every existing axis-string test in
`tests/test_numerics_calculus.py` (`test_string_integer_axis`,
`test_colon_slice_axis_string`, `test_comma_separated_string_axes`) and
`tests/test_numerics_ev_ops.py` (`test_integrate_colon_slice_axis`,
`test_integrate_comma_string_axis`, `test_integrate_single_int_string_axis`,
`test_integrate_axis_all_string`) still passes unchanged, now exercising
the single shared implementation from both call sites.

C2: FIXED — Added a one-line comment at each of the three sites where a
`src_bak` warn-and-continue (`typer.echo` + partial-result computation)
was converted to a hard `raise ValueError`, naming the rule that motivated
it: `src/postgkyl/numerics/ev_ops.py:262-265` (`divergence`,
`num_comps > num_dims`), `ev_ops.py:314-317` (`curl`, 2D branch,
`num_comps > 3`), and `ev_ops.py:325-328` (`curl`, 3D branch,
`num_comps > 3`). The three `raise ValueError` calls that were already
hard errors in `src_bak` (1D `num_comps != 3`, 2D `num_comps < 2`, 3D
`num_comps < 3`) were left uncommented since their behavior did not
change. No test changes needed — the existing raise-path tests
(`test_too_many_components_raises`, `test_2d_too_many_components_raises`,
`test_3d_too_many_components_raises`) already cover exactly these three
lines.

C5: FIXED (was explicitly non-blocking, but cheap and closes a real
correctness-vs-line-coverage gap). Added
`TestFftIsotropic.test_iso_preserves_total_power_end_to_end`
(`tests/test_numerics_fft.py`, in the `iso` test class) which calls the
public `fft(..., psd=True, iso=True)` entry point on random 3D data,
independently reconstructs the expected isotropic spectrum via direct
`init_polar`/`polar_isotropic` calls (reproducing `fft()`'s internal
`nkpolar` derivation from the nodal grid lengths) to confirm agreement,
and then asserts the physically meaningful invariant that
`sum(shell_mean * shell_cell_count)` over all populated shells equals the
total input PSD power (`np.sum(ft_cartesian)`) to `rtol=1e-10` — proving
shell-averaging is power-conserving, not just shape-correct.

## Post-fix verification

Full suite: `PYTHONPATH=src python -m pytest tests/ -q` → `524 passed, 1
skipped` (up from 522 passed/1 skipped; net +2 tests:
`test_all_windows_failing_to_converge_raises` and
`test_iso_preserves_total_power_end_to_end`, with `capsys`-only workaround
assertions removed from 6 pre-existing `growth` tests).

Coverage (`coverage run -m pytest tests/ -q` then `coverage report
--include="*/postgkyl/numerics/*" -m`): 100% line coverage on every file
in the layer, `TOTAL 759 stmts, 0 miss, 100%` (down from 766 stmts —
removing the dead `print`/`sys.stdout` lines and the duplicated
axis-string-parsing body reduced statement count without reducing
coverage). Architecture tests
(`test_import_contract_no_violations`/`test_import_graph_is_acyclic`/
`test_foreign_floor_confined_to_ffi`/`test_facade_is_pure_reexport`) all
still pass; `ev_ops.py`'s new `from .calculus import _split_axis_string`
is an intra-`numerics` relative import (sibling-to-sibling), which does
not add any new edge to the layer DAG.
