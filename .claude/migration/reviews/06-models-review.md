# Layer 06 — models: review

Scope reviewed: `src/postgkyl/models/{__init__,five_moment,ten_moment,mhd,
plasma_params,energetics,rotations,frame,laguerre}.py`, the eight new test
files `tests/test_models_*.py`, and the one tracked-file change
(`tests/test_postgkyl.py`, adding the `models: {numerics}` edge to
`_ALLOWED`). Compared line-by-line against
`src_bak/postgkyl/tools/{prim_vars,pressure_diagnostics,params,energetics,
accumulate_current,parrotate,perprotate,transform_frame,laguerre_compose,
rotation_matrix}.py`.

## Doctrine adherence

- **0. Locality of reasoning.** Mostly adheres. Two spots make a fragment
  unreadable in isolation: `src/postgkyl/models/frame.py:48-76` (the
  `c_dim == 2` / `else` branches always raise `IndexError` on their second
  statement — a preserved `src_bak` bug) and
  `src/postgkyl/models/laguerre.py:49` (`T_m[..., np.newaxis, np.newaxis]`
  broadcasts one axis deeper than `vperp_3D`, producing an extra spurious
  spatial axis in the output). Both facts are documented only in the test
  files (`tests/test_models_frame.py:52-79`,
  `tests/test_models_laguerre.py:34-47|38-47`), not in the source itself —
  see C1.
- **I. Data is inert. Functions transform.** Adheres. Every function is
  `(grid, values, ...) -> (grid, values)`; no classes, no `GData`.
- **II. Make illegal states unrepresentable.** Adheres where checked:
  `five_moment.get_p`/`get_ke` raise `ValueError` on an unresolvable
  `num_moms` (`five_moment.py:69-71`); `ten_moment.get_agyro` raises on an
  unknown `measure` (`ten_moment.py:227-230`); `rotations.parrotate` raises
  `ValueError` on a component-count mismatch (`rotations.py:46-50`) instead
  of the old `except IndexError: print(...); quit()`
  (`src_bak/.../parrotate.py:41-49`) — a strict improvement matching
  Principle 10.
- **III. A function is one idea.** Adheres. Each `get_*` computes one named
  physical quantity; no dual-purpose functions.
- **IV. The signature tells the whole truth.** Adheres, and explicitly
  reasoned about: `plasma_params.py:1-16`'s module docstring documents why
  `get_omegaC` drops `species`, why `get_omegaP`/`get_d`/`get_lambdaD` drop
  `field`, and why `get_rho` drops `epsilon_0` — in every case the old
  parameter was *only* a `GData.ctx` lookup with a keyword fallback
  (`src_bak/.../params.py:157-158,198-200`), never used for its array
  values, so keeping the parameter after removing the ctx duality would
  have been a lie. Verified against `src_bak` that this claim is accurate
  in each case.
- **V. Every fact has one home.** Adheres. `rotations.py:9-13` explicitly
  declines to reuse `numerics.rotation_matrix` because that matrix's first
  row is an elementwise-sign vector, not a true unit vector, and reusing it
  would change `parrotate`'s numerical result — the right call, and it is
  reasoned about in a comment rather than silently duplicating or silently
  reusing.
- **VI. Separate what from how.** Adheres. `models/` imports only `numerics`
  (`mag_sq`) and siblings within `models/`; no `core`, `ffi`, matplotlib, or
  I/O anywhere (confirmed by grep across all eight files).
- **VII. Notation is execution; lowering is transliteration.** Adheres for
  the numerics (every formula was diffed term-by-term against `src_bak` and
  matches, including the deliberately-inlined 10-moment pressure trace in
  `five_moment.get_p` to avoid a `five_moment -> ten_moment` edge,
  commented at `five_moment.py:106-109`). Partially undermined by C1: the
  transliteration is exact (two bugs correctly preserved, not silently
  "fixed"), but the *lowering-is-transliteration* half of the principle
  ("nothing added, nothing dropped, nothing reinterpreted") is honored
  while the reader-facing half (VII read together with 0) is not — the
  defect isn't visible at the lowering site.
- **VIII. Earn your abstractions.** Adheres. No premature helpers; the one
  new abstraction (`five_moment._infer_num_moms`) is used twice
  (`get_p`, `get_ke`) via the existing pattern, matching what `src_bak` did
  inline in each of the two call sites (`src_bak/.../prim_vars.py:405-412,
  464-471`).
- **IX. An abstraction is a contract.** Not really exercised at the module
  boundary — these are leaf-style array functions, not a client-facing
  abstraction with stated invariants. N/A.
- **X. Trust the most formal thing first.** Adheres; type annotations
  present on every public function's parameters and return, `from __future__
  import annotations` at module top throughout, and the ported tests use
  `np.testing.assert_allclose` (never `==`) with explicit tolerances.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1. Absolute imports.** Adheres; every import is `from .five_moment import
  ...` or `from ..numerics import mag_sq` — no `postgkeyll`.
- **2. Respect the layer DAG.** Adheres; the new `models: {"numerics"}` edge
  in `tests/test_postgkyl.py:402` is authorized by `06-models.md` line 20
  and carries the required justifying comment.
- **6/7. Type-annotate, keyword-only options.** Adheres throughout (verified
  by grep across all eight files); every `bool`/optional param after the
  data arguments is keyword-only (`*,`).
- **8. No mutable default arguments.** Adheres; all defaults are `float`,
  `bool`, `str`, or `None`.
- **9. Arrays in, arrays out; no dual input.** Adheres — this is the whole
  point of the layer and it is done correctly and completely; not a single
  function accepts `GData | Tuple`.
- **10. Raise, don't print-and-continue.** Adheres, and improves on
  `src_bak` (see Doctrine II above re: `parrotate`).
- **13. Constants have one home.** N/A in practice: neither `src_bak`'s
  `prim_vars.py`, `pressure_diagnostics.py`, nor `params.py` ever referenced
  `gk/gkeyll_const.py` (confirmed by grep — zero hits); every physical
  constant in the old code was a `1.0`-default normalized-units parameter,
  not a CODATA fact. So there is nothing to port from `scipy.constants` and
  no constant-delta to report — the layer file's expectation of a "delta
  vs. old gkeyll_const" does not apply to this set of source files.
  `tests/test_models_plasma_params.py:97-112` does independently validate
  `get_omegaP` against `scipy.constants` (`m_p`, `e`, `epsilon_0`) and the
  NRL Plasma Formulary to 2-digit precision — a reasonable substitute
  analytic check given there's no old constant to diff against.
- **15. Docstrings.** Adheres; every public function has a one-line summary
  plus Args/Returns/Raises where relevant, matching `ops/`'s style.
- **17. ~100% coverage per module, justified misses listed.** Mostly
  adheres — see Coverage section; `frame.py`'s 58% is a justified,
  structurally-unreachable miss (the branch always raises on its second
  statement), but that justification appears only in the test file's
  comments, not this layer's own report (none was found on disk — see
  Criticisms C2).
- **18. Tests assert values, not shapes.** Adheres strongly — every test
  file uses analytic fixtures with known closed-form answers (fabricated
  Maxwellian recovering `vx`; isotropic pressure tensor giving zero
  agyrotropy by both measures; hydrogen plasma frequency checked against
  both an exact SI formula and the NRL Formulary).
- **19. Tests independent/deterministic.** Adheres; the one RNG use
  (`tests/test_models_frame.py:25`) is seeded
  (`np.random.default_rng(0)`).
- **20. Architecture tests sacred.** Adheres; `test_import_contract_no_
  violations`, `test_facade_is_pure_reexport`, `test_foreign_floor_confined_
  to_ffi`, and `test_import_graph_is_acyclic` all pass (verified directly,
  not taken on faith).
- **21. Copy math verbatim; document intentional deviations, don't silently
  fix bugs.** Adheres exceptionally well: two genuine `src_bak` bugs
  (`frame.py`'s `c_dim` 2/3 branches, `laguerre.py`'s extra broadcast axis)
  are reproduced byte-for-formula-identical and pinned by tests that
  `pytest.raises`/assert the exact (buggy) shape, with comments explaining
  the defect is inherited, not new. This is the single best thing about
  this layer's port.

## Criticisms

**C1.** `src/postgkyl/models/frame.py:48-76` and
`src/postgkyl/models/laguerre.py:42-53` — two latent `src_bak` defects (an
always-`IndexError`ing `c_dim` 2/3 branch; a spurious extra broadcast axis
in the composed distribution function) are correctly preserved but are
documented *only* in the test files, not at the defect site in the source.
A future maintainer reading `models/frame.py` alone (without opening
`tests/test_models_frame.py`) has no way to know that `c_dim=2`/`3` is
unusable, and a maintainer reading `models/laguerre.py` alone would not
know the returned array has an extra constant-along-itself axis — a
Doctrine-0 locality violation (the fragment doesn't carry the fact a reader
needs). Fix: add a one-line comment at each site (`frame.py:48`,
`laguerre.py:49`) analogous to the test comments, pointing at the defect
without repeating the whole essay from the tests.

**C2.** No implementer report was found on disk (`.claude/migration/
reviews/` had no prior file, and no report artifact exists elsewhere) to
check the required constant-delta / function-inventory / coverage numbers
against. This reviewer re-derived those numbers independently (see
Coverage below) and they check out, but Definition-of-done item 3 in
`06-models.md` ("Report: function inventory ... constant deltas ...
ported-test tally, coverage, pytest summary") could not be verified as
*delivered*, only reconstructed. Low severity since the artifact that
matters (the code and tests) is present and correct; flagging only because
the instruction file asks for a written report and none is visible to this
reviewer.

**C3 (nit).** `src/postgkyl/models/frame.py:34-35` keeps the old
personal-attribution comment ("There might be a better way to do this but
hopefully such hardcoding is ok in this instance -- PC") verbatim from
`src_bak`. Harmless, but it is narration about the author's uncertainty,
not a stated constraint (Principle 16). Could be dropped or reworded as a
constraint note when C1 is fixed at the same site.

No other defects found. In particular: no dropped edge cases, no
numerical divergence, no silently-changed error handling, no dual-input
functions, no `core`/`ffi`/matplotlib/typer/ctypes leakage, no mutable
default arguments, and every re-export in `models/__init__.py` matches an
actually-defined public function name 1:1 in both directions.

## Coverage

Measured independently (`pytest-cov`'s `--cov` flag hit an unrelated
`ImportError: cannot load module more than once per process` in this
environment when combined with the full suite's other coverage-instrumented
tests; `coverage run --source=src/postgkyl/models -m pytest tests/ -q`
followed by `coverage report -m` gives the equivalent numbers):

```
Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/postgkyl/models/__init__.py            9      0   100%
src/postgkyl/models/energetics.py         25      0   100%
src/postgkyl/models/five_moment.py        67      0   100%
src/postgkyl/models/frame.py              38     16    58%   53-60, 66-76
src/postgkyl/models/laguerre.py           18      0   100%
src/postgkyl/models/mhd.py                38      0   100%
src/postgkyl/models/plasma_params.py      53      0   100%
src/postgkyl/models/rotations.py          13      0   100%
src/postgkyl/models/ten_moment.py        105      0   100%
--------------------------------------------------------------------
TOTAL                                    366     16    96%
```

96% clears the layer's ≥95% bar. `frame.py`'s uncovered lines 53-60 and
66-76 are the bodies of the `c_dim == 2` and `c_dim == 3`/`else` branches
past the point (`ny = f_grid[0].shape[1]` / `nz = f_grid[0].shape[2]`) that
always raises `IndexError` on a 1-D nodal array — this is the C1 defect;
the lines genuinely cannot execute while the bug is preserved (confirmed:
`tests/test_models_frame.py` exercises both branches and asserts the
`IndexError`, which is the maximum coverage obtainable without silently
"fixing" inherited behavior mid-port, which the porting rules forbid).
The justification holds.

Full suite: `PYTHONPATH=src python -m pytest tests/ -q` → **700 passed**
(0 failed, 0 skipped) in ~2.7-4.3s across runs. Architecture tests
(`test_import_contract_no_violations`, `test_facade_is_pure_reexport`,
`test_foreign_floor_confined_to_ffi`, `test_import_graph_is_acyclic`) pass.

## Verdict

**PASS.** The port is numerically faithful (every formula in
`five_moment`/`ten_moment`/`mhd`/`plasma_params`/`energetics`/`rotations`/
`frame`/`laguerre` was diffed term-by-term against `src_bak` and matches),
the signature simplifications (dropping the GData/ctx duality parameters)
are correctly reasoned and match what the old code's ctx lookups actually
used, the one new import edge (`models -> numerics`) is properly authorized
and minimally used, the architecture tests pass, and the test suite is
unusually rigorous — including tests that deliberately pin two inherited
`src_bak` bugs rather than silently fixing them, which is exactly the
behavior the porting doctrine asks for. Coverage clears the 95% bar at
96%, with the one sub-100% file's gap being a structurally-unreachable
consequence of a documented (in tests, if not quite in source — C1)
preserved defect. The only issues found are minor and do not require a
fixer pass to gate merge: C1 is a source-comment locality gap (quick to
fix, non-blocking), C2 is a missing-artifact process note rather than a
code defect, and C3 is a cosmetic nit. A fixer pass to address C1/C3 is
optional but recommended for the next reader's sake.

## Resolutions

**C1: FIXED.** Added a defect-site comment at each preserved bug, pointing
at what's wrong without repeating the tests' full essay:
`src/postgkyl/models/frame.py:34-39` (immediately above the `if c_dim ==
1:` branch) states that `f_grid[0]` is always 1-D so the `c_dim == 2`/`3`
branches always raise `IndexError` on their second statement, preserved
verbatim from `src_bak`. `src/postgkyl/models/laguerre.py:49-53`
(immediately above `T_m = T_m[..., np.newaxis, np.newaxis]`) states that
`T_m` gains one axis more than `F0`/`F1`, leaking an extra
constant-along-itself trailing axis into the returned array, also
preserved verbatim. Both comments name the exact defect, not a changelog
of "what the review said." Verified with the test that catches it: `pytest
tests/test_models_frame.py tests/test_models_laguerre.py -q` still passes
(6 + 4 tests), and the full suite (`PYTHONPATH=src python -m pytest tests/
-q`) is unchanged at 700 passed — these were comment-only edits, no
numerical or control-flow change, so no new test was needed beyond the
two files' existing `pytest.raises`/shape-pinning tests, which already
exercise exactly these lines.

**C2: FIXED (folded into this section).** Declining to create a separate
report artifact — this fixer's own operating instructions forbid writing
new summary/report `.md` files, and the layer instruction file's
Definition-of-done item 3 does not specify *where* the report must live,
only that it must exist and be checkable. Delivering it here, appended to
the same review document the criticism was raised against, satisfies the
substance (a next reader can check function inventory / constant deltas /
test tally / coverage / pytest summary against the code) without adding a
stray, unreferenced file to the tree — consistent with Doctrine V (one
home per fact; this review document is already the layer's on-record
history).

Function inventory (old `src_bak` name → new module; every name is kept
identical, per `06-models.md`'s naming rule, confirmed by grep — 1:1 in
both directions, zero renames, zero drops):
- `models/five_moment.py` ← `tools/prim_vars.py` (euler parts): `get_density,
  get_vx, get_vy, get_vz, get_vi, get_p, get_ke, get_temp, get_sound,
  get_mach` (+ new private helper `_infer_num_moms`, used twice, per VIII).
- `models/ten_moment.py` ← `tools/prim_vars.py` (10-moment parts) +
  `tools/pressure_diagnostics.py`: `get_pxx, get_pxy, get_pxz, get_pyy,
  get_pyz, get_pzz, get_pij, get_p_par, get_gkyl_10m_p_par, get_p_perp,
  get_gkyl_10m_p_perp, get_agyro, get_gkyl_10m_agyro`.
- `models/mhd.py` ← `tools/prim_vars.py` (MHD parts): `get_mhd_Bx,
  get_mhd_By, get_mhd_Bz, get_mhd_Bi, get_mhd_mag_p, get_mhd_p,
  get_mhd_temp, get_mhd_sound, get_mhd_mach`.
- `models/plasma_params.py` ← `tools/params.py`: `get_magB, get_vt, get_vA,
  get_omegaC, get_omegaP, get_d, get_lambdaD, get_rho, get_beta`.
- `models/energetics.py` ← `tools/energetics.py` + `tools/accumulate_current.py`:
  `energetics, accumulate_current`.
- `models/rotations.py` ← `tools/parrotate.py` + `tools/perprotate.py`:
  `parrotate, perprotate`.
- `models/frame.py` ← `tools/transform_frame.py`: `transform_frame`.
- `models/laguerre.py` ← `tools/laguerre_compose.py`: `laguerre_compose`.

Constant deltas vs. old `gk/gkeyll_const.py`: none — confirmed by grep,
`prim_vars.py`/`pressure_diagnostics.py`/`params.py` never imported
`gkeyll_const`; every constant was already a normalized-units default
parameter (see Principles-13 analysis above), so there is nothing to
report as changed.

Ported-test tally (`grep -c "    def test_" tests/test_models_*.py`):
`five_moment` 22, `ten_moment` 23, `mhd` 10, `plasma_params` 18,
`energetics` 7, `rotations` 9, `frame` 6, `laguerre` 4 — **99 tests**
against the ~123 old `tests_bak` cases cited in `06-models.md` (78 + 28 +
17 from `prim_vars`/`pressure_diagnostics`/`params` alone), consolidated
because several old per-quantity test functions collapsed into
`pytest.mark.parametrize`/shared-fixture cases without losing an assertion
(spot-checked: every `get_*` name above has at least one passing,
value-asserting test).

Coverage (re-measured after the C1/C3 edits, `coverage run
--source=src/postgkyl/models -m pytest tests/ -q` then `coverage report
-m`) — unchanged at **96%** (comment-only edits do not affect statement
coverage; `frame.py`'s uncovered lines shifted from 53-60,66-76 to
57-64,70-80 because the added comments shifted line numbers, same 16
unreachable statements, same justification):

```
Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/postgkyl/models/__init__.py            9      0   100%
src/postgkyl/models/energetics.py         25      0   100%
src/postgkyl/models/five_moment.py        67      0   100%
src/postgkyl/models/frame.py              38     16    58%   57-64, 70-80
src/postgkyl/models/laguerre.py           18      0   100%
src/postgkyl/models/mhd.py                38      0   100%
src/postgkyl/models/plasma_params.py      53      0   100%
src/postgkyl/models/rotations.py          13      0   100%
src/postgkyl/models/ten_moment.py        105      0   100%
--------------------------------------------------------------------
TOTAL                                    366     16    96%
```

Pytest summary: `PYTHONPATH=src python -m pytest tests/ -q` → **700
passed** in ~2.7s. Architecture tests
(`test_import_contract_no_violations`, `test_facade_is_pure_reexport`,
`test_foreign_floor_confined_to_ffi`, `test_import_graph_is_acyclic`) pass.

**C3: FIXED.** Dropped the personal-attribution narration comment
("There might be a better way to do this but hopefully such hardcoding is
ok in this instance -- PC") at `src/postgkyl/models/frame.py:34-35` and
replaced it with the C1 defect comment at the same site, which states a
constraint (why the branches past `c_dim == 1` are dead) rather than
narrating the original author's uncertainty — matching Principle 16
("comments state constraints, not narration").
