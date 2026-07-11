# Layer 12 — diagnostics loaders — review

Scope reviewed: `src/postgkyl/diagnostics/discovery.py`,
`src/postgkyl/diagnostics/gyrokinetics/{__init__,quantity,quantities,registry,
load_quantity,distf,utils}.py`, `src/postgkyl/diagnostics/pkpm.py` (the
`load_pkpm` addition), the `diagnostics`/root `__init__.py` re-exports, the
`_ALLOWED` edge-map change in `tests/test_postgkyl.py`, and the new/extended
tests (`tests/test_diagnostics_discovery.py`, `tests/test_diagnostics_gk_load.py`,
`tests/test_diagnostics_pkpm.py`). Every new/changed file was read in full and
diffed line-by-line against its `src_bak` original
(`src_bak/postgkyl/loader.py`, `src_bak/postgkyl/loaders/{gk_distf,gk_quantity,
pkpm}.py`, `src_bak/postgkyl/gk/{gk_utils,gkeyll_enums}.py`,
`src_bak/postgkyl/gk/gk_quantities/{gkquantity,fetch_funcs,registry}.py`).

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. The one genuinely non-local decision
  in this layer — abandoning weak-DG-kernel math for "interpolate first, then
  plain NumPy" in every `fetch_*` — is stated right where it matters, at the
  top of `quantities.py` (lines 1–27), not buried in a changelog or a separate
  design doc.
- **I. Data is inert. Functions transform.** Partially in tension, by
  instruction. `GkQuantity` (`quantity.py:27`) is a frozen dataclass (inert
  data) but its methods (`get_avail_source`, `fetch`, `get_src_gdata`) glob the
  filesystem and recursively invoke fetch functions — a data object that
  "does things." This is not an invention of this layer: the instruction
  file's source→target map explicitly mandates "`GkQuantity` (make it a
  frozen dataclass...)" mirroring `src_bak`'s `GkQuantity` class one-for-one.
  Given the explicit authorization, this is a documented, deliberate
  compromise rather than a silent violation.
- **II. Make illegal states unrepresentable.** Adheres. `_get_ctx_val`
  (`quantities.py:44`) raises `KeyError` with an actionable message instead of
  returning `None`/a sentinel; `get_avail_source` raises `FileNotFoundError`
  when no combo resolves; `load_gk_quantity` raises `ValueError` listing valid
  names for an unknown quantity.
- **III. A function is one idea.** Adheres for the fetch functions and
  discovery helpers (each computes exactly one formula or one filesystem
  fact). `GkQuantity.fetch`/`get_src_gdata` mix resolution + recursive fetch
  invocation, but that is the registry's stated job (dispatch on nested
  sources), not scope creep.
- **IV. The signature tells the whole truth.** Violates in one place: see
  **C1** (`distf.py:73-84`, `load_gk_distf` — booleans and other options are
  positional-or-keyword, not forced keyword-only). Everywhere else in this
  layer (`load_gk_quantity`, `resolve_frames`, `load_pkpm`, `available_frames`)
  correctly puts a `*` before every option.
- **V. Every fact has one home.** Adheres. `discovery.py` is the sole home
  for stem/frame globbing (`GkQuantity._avail_frames_src` and
  `distf.resolve_frames` both call into it instead of globbing themselves);
  physical constants come from `scipy.constants` instead of a re-typed
  `gk/gkeyll_const.py` (`quantities.py:35,194`); the fetch-function naming
  convention (`s#`/`c#`/`add`/`sub`/…) is preserved verbatim so the registry
  mapping in `registry.py` stays recognizable against `src_bak`.
- **VI. Separate what from how.** Adheres. `set_tick_font_size` and the
  plotting-only constants in `gk_utils.py` are correctly left out of
  `utils.py` (rendering concern, not loading); the module docstring says so
  for the one matplotlib function actually referenced elsewhere in the old
  tree.
- **VII. Notation is execution; lowering is transliteration.** Adheres for
  the algebraic formulas (`fetch_Tpar_from_M0_M1_M2par`'s docstring states the
  identity `upar*M1 + M0*Tpar/m = M2par` and the code is a direct
  transliteration; verified algebraically identical to `src_bak`'s weak-kernel
  version, see Criticisms/Coverage discussion below).
- **VIII. Earn your abstractions.** Adheres. `_make_fetch_comp`/
  `_make_fetch_binop` are used many times over (6 and 6 call sites
  respectively) before being factored into a helper, mirroring the multiple
  uses that justified the same factories in `src_bak`.
- **IX. An abstraction is a contract.** Adheres. `GkQuantity`'s docstring
  states its guarantees (source-combination list, fetch function per
  combination, label/flag semantics) and `GkQuantityRegistry` exposes exactly
  `register`/`get`/`list`/`has`, matching `src_bak`'s contract.
- **X. Trust the most formal thing first.** Adheres: every public function in
  this layer is type-annotated; the physics is additionally pinned by
  analytic tests (`TestFetchPhysics`, `TestCrossGradDivB.test_linear_scalar_1d`)
  rather than relying on docstrings alone.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports).** Adheres — no `postgkeyll` imports anywhere in
  `src/`; the doubled-e package only appears inside doc-comments explaining
  what was *not* copied.
- **2 (respect the layer DAG).** Adheres. The `diagnostics -> api` edge and
  the facade `-> diagnostics` edge were added to `_ALLOWED`
  (`tests/test_postgkyl.py`) exactly as the instruction file specifies, with
  a comment naming the authorizing layer file; `test_import_contract_no_
  violations` and the other three architecture tests pass.
- **4 (no typer/ctypes).** Adheres — `GkeyllDGops`/`ctypes` are gone; grepped
  the whole `diagnostics/` tree, no hits outside comments.
- **6 (type-annotate every public function).** Adheres almost everywhere;
  see **C1** for the one signature that also fails rule 7.
- **7 (keyword-only options; booleans never positional).** **Violates** at
  `distf.py:73-84` (`load_gk_distf`) — see **C1**. Every other new public
  function in the layer (`resolve_frames`, `load_gk_quantity`, `load_pkpm`,
  `available_frames`) correctly enforces this with `*`.
- **8 (no mutable default arguments).** Adheres — every default is `None`,
  a literal, or an immutable value.
- **10 (raise, don't print-and-continue).** Adheres — `KeyError`/`ValueError`/
  `FileNotFoundError`/`NameError` throughout, no `print`+`return None`.
  `utils.read_gfile_if_present` additionally *drops* an inherited bug (the old
  function referenced a free variable `ctx` that was never a parameter, an
  existing `NameError` bug in `src_bak`) in favor of a clean boolean flag —
  a positive, documented divergence (module docstring, `utils.py:9-11`).
- **12 (frozen records).** Adheres — `GkQuantity` is
  `@dataclass(frozen=True)`.
  Minor nit: `field` is imported from `dataclasses` (`quantity.py:15`) but
  never used (see **C3**).
  `Also see 13.
- **13 (constants have one home).** Adheres — `fetch_beta_from_bmag_press`
  uses `scipy.constants.mu_0` instead of the old hardcoded
  `gk/gkeyll_const.GKYL_MU0`. Noted for the record (not a defect): the two
  values differ at the ~7×10⁻⁷ relative level (`GKYL_MU0` was the exact
  pre-2019-SI `4π×10⁻⁷`; `scipy.constants.mu_0` is the current CODATA/SI
  measured value) — an intentional, policy-mandated, and negligible-magnitude
  change, not a silent one.
- **17 (one test file per module; ~100% coverage).** Adheres, with the layer
  instruction file explicitly overriding the generic "one file per module"
  default: it names a single consolidated `tests/test_diagnostics_gk_load.py`
  covering `distf`/`quantity`/`quantities`/`registry`/`load_quantity` as one
  corpus, which is exactly what was delivered. Coverage is 99% overall for
  `postgkyl.diagnostics` (see Coverage below), comfortably above the 85%
  floor.
- **18 (assert values, not shapes).** Adheres — `TestFetchPhysics` checks
  hand-computed numbers (e.g. `Tpar = mass*(M2par - M1**2/M0)/M0 = -16.0`);
  `TestCrossGradDivB.test_linear_scalar_1d` checks a linear scalar field's
  known derivative against the Levi-Civita cross-product formula.
- **19 (independent, deterministic tests).** Adheres — every test uses
  `tmp_path`/`monkeypatch`, no RNG is needed (all fixtures are constant
  fields), `needs_gkeyll` gates every test that touches the compiled shim.
- **21 (copy liberally, document divergence).** Adheres, and is this layer's
  strongest point: every `fetch_*` function is algebraically verified against
  its `src_bak` weak-DG-kernel original (see below) and the wholesale
  interpolate-first rewiring is explained, with its cost (why a literal
  "stay-modal" port is impossible given this layer's allowed imports), in
  `quantities.py`'s module docstring.
- **23 (never edit src_bak).** Adheres — `git status` shows no changes under
  `src_bak/`.
- **24 (leave the tree green).** Adheres — `PYTHONPATH=src python -m pytest
  tests/ -q` passes in full (see Coverage below for the exact numbers).

## Criticisms

**C1 — `load_gk_distf`'s boolean/option parameters are positional-callable, not keyword-only** (`src/postgkyl/diagnostics/gyrokinetics/distf.py:73-84`).
The signature is
```python
def load_gk_distf(
    name: str, species: str, frame: int,
    tag: str = "f", suffix: str = "", use_c2p_vel: bool = False,
    use_mc2nu: bool = False, use_mapc2p: bool = False, block_idx: int | None = None,
    interp: int | None = None,
    jf_file: str | None = None, mapc2p_vel_file: str | None = None,
    jacobvel_file: str | None = None, mc2nu_file: str | None = None,
    mapc2p_file: str | None = None, jacobtot_inv_file: str | None = None,
) -> GData:
```
with no `*` separator after the three data arguments, so
`load_gk_distf("sim", "ion", 250, "f", "", True, False, True)` is legal and
silently ambiguous about which flag is which — exactly the foot-gun
PYTHON_PRINCIPLES rule 7 exists to prevent. Every sibling function this layer
introduces (`resolve_frames`, `load_gk_quantity`, `load_pkpm`) gets this
right with a `*`. No current call site in the codebase actually passes these
positionally (both `quantities.load_distf` and the test suite call
everything by keyword), so there is no live bug today, but the guard is
absent for the next caller (e.g. a layer-13/14 CLI command wiring this up).
Fix: insert `*` immediately after `frame: int,`.

**C2 — No on-disk implementer report for this layer.**
The instruction file's Definition of Done item 3 asks for "Report: fetch_*
rewiring tally (ported/deferred+reason), enum tables ported and their Gkeyll
header sources, coverage, pytest summary." No such file exists under
`.claude/migration/notes/` or elsewhere (checked `find ... -newer
layers/11-api.md`). The equivalent content is present, just distributed
across docstrings instead of collected in one place: `quantities.py`'s module
docstring covers the rewiring rationale, and this review independently
verified the fetch-function tally is 100% ported / 0 deferred (`diff` of the
`fetch_*`/`load_distf` symbol sets between `src_bak/.../fetch_funcs.py` and
the new `quantities.py` — identical sets, no `NotImplementedError` entries).
Informational/non-blocking (mirrors the same gap flagged, and treated as
non-blocking, in the 10-diagnostics review), since the substance is
independently reconstructible and checks out.

**C3 — Unused import** (`src/postgkyl/diagnostics/gyrokinetics/quantity.py:15`).
`from dataclasses import dataclass, field` — `field` is never used (confirmed
with `pyflakes`, the only finding across the whole layer). Trivial; delete it.

**C4 — `distf.load_gk_distf`'s coordinate-mapping branches are untested end-to-end** (`src/postgkyl/diagnostics/gyrokinetics/distf.py:166-177`).
The `use_mc2nu`/`use_mapc2p`/`grid_type` bookkeeping lines are the only gap in
an otherwise-100%-covered module (90% on this file alone). The test module's
own docstring explains why: the staged `rt_gk_tcv_iwl_1x2v_p1` fixtures'
`mapc2p_vel`/`jacobvel` files carry no `basis_type`/`poly_order` metadata, so
`ops.map` (which needs that metadata) cannot be exercised against them. This
is an honest, load-bearing justification rather than a shrug — `ops.map`
itself is unit-tested elsewhere (layer 9) — but it does mean this layer ships
zero integration coverage of the one feature (velocity/position coordinate
mapping) that most differentiates `load_gk_distf` from a bare file read.
Non-blocking (justified, and above the 85% floor at the module level: 90%),
but worth flagging for whoever stages a fixture set with real coordinate-map
metadata later.

No other criticisms. The numerical core of this layer — every `fetch_*`
formula — was independently re-derived algebraically against its `src_bak`
weak-DG-kernel original (e.g. `fetch_Tpar_from_M0_M1_M2par`:
`mass*(m2par - (m1/m0)*m1)/m0` new vs. `mass*(m2par - m1²·m0⁻¹)·m0⁻¹` old —
identical; `fetch_press_from_BiMax`, `fetch_beta_from_bmag_press`,
`fetch_Tperp_from_M0_M2perp` similarly checked) and found to match in every
case, modulo the one documented, mandated representation change (weak DG
product → pointwise product of interpolated values). The registry
(`registry.py`) is a verbatim transcription of `src_bak/.../registry.py`
(same sources, same fetch-function assignments, same labels/flags, diffed
side by side). `discovery.py`'s `find_output_stems` is byte-for-byte
identical logic to `src_bak/postgkyl/loader.py`'s. `GkQuantity`'s frame/combo
resolution logic (`_avail_combo_frames`, `get_avail_source`) is line-for-line
equivalent to `src_bak/.../gkquantity.py`, with one defensive improvement
(passing `None` instead of the literal string `"None"` for a geo-only nested
quantity's frame argument — the old code's `str(frame)` would have raised
`ValueError: invalid literal for int() with base 10: 'None'` if that branch
were ever exercised with a non-geo consumer of a geo source; it never is, in
either version, so this is a latent-bug fix with no observable behavior
change today, not a functional divergence).

## Coverage

Measured directly (`pytest --cov` crashes sandbox-wide on this environment —
`ImportError: cannot load module more than once per process`, the same known
issue documented in the 05-core/08-ops-physics/10-diagnostics/11-api
reviews); worked around with `coverage run` on the plain suite, then filtered
the report:

```
PYTHONPATH=src python -m coverage run -m pytest tests/ -q
# 1219 passed, 3 skipped in 66.64s
PYTHONPATH=src python -m coverage report -m --include="*/postgkyl/diagnostics/*"
```

```
Name                                                     Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------------------
src/postgkyl/diagnostics/__init__.py                         2      0   100%
src/postgkyl/diagnostics/discovery.py                       27      0   100%
src/postgkyl/diagnostics/five_moment.py                    116      0   100%
src/postgkyl/diagnostics/gyrokinetics/__init__.py             6      0   100%
src/postgkyl/diagnostics/gyrokinetics/distf.py               69      7    90%   166-167, 170-171, 173-174, 177
src/postgkyl/diagnostics/gyrokinetics/load_quantity.py       29      0   100%
src/postgkyl/diagnostics/gyrokinetics/quantities.py         159      0   100%
src/postgkyl/diagnostics/gyrokinetics/quantity.py           115      0   100%
src/postgkyl/diagnostics/gyrokinetics/registry.py            52      0   100%
src/postgkyl/diagnostics/gyrokinetics/utils.py               65      2    97%   43, 95
src/postgkyl/diagnostics/kinetic.py                          46      0   100%
src/postgkyl/diagnostics/mhd.py                              79      0   100%
src/postgkyl/diagnostics/multispecies.py                     41      0   100%
src/postgkyl/diagnostics/pkpm.py                             43      0   100%
src/postgkyl/diagnostics/plasma.py                           95      0   100%
src/postgkyl/diagnostics/rotations.py                        26      0   100%
src/postgkyl/diagnostics/ten_moment.py                      178      0   100%
--------------------------------------------------------------------------------------
TOTAL                                                      1148      9    99%
```

New-module-only breakdown (this layer's actual deliverable): `discovery.py`
100%, `gyrokinetics/{__init__,load_quantity,quantities,quantity,registry}.py`
100%, `gyrokinetics/distf.py` 90%, `gyrokinetics/utils.py` 97%, `pkpm.py`
(with `load_pkpm` added) 100%. All comfortably clear the layer's 85% floor;
the layer-10 quantity modules (`five_moment`, `ten_moment`, `mhd`, `plasma`,
`multispecies`, `rotations`, `kinetic`) are untouched by this layer's diff and
stay at 100%, so the "layer-10 modules stay at 100%" Definition-of-Done
condition holds.

Justification check on the two non-100% files:
- `distf.py:166-177` (mc2nu/mapc2p branches) — justified (**C4** above): no
  staged fixture exercises `ops.map`'s metadata requirement through this
  path; `ops.map` itself is covered elsewhere. Holds up, but is a real gap
  worth eventually closing with a proper fixture.
- `utils.py:43,95` (`isinstance(grid, np.ndarray)` branches in `read_gfile`/
  `read_interp_gfile`) — justified: `GDataState._grid` is always a `list`
  (never a bare `np.ndarray`) in this codebase's container contract
  (`core/state.py:36`, `io.read`'s documented return type), so this branch,
  inherited verbatim from `src_bak` (where a 1-D grid *could* come back as a
  bare array under the old data model), is genuinely unreachable dead code
  under the new architecture. Holds up as a "defensive unreachable branch"
  per PYTHON_PRINCIPLES rule 17's carve-out, though it was not explicitly
  called out as such anywhere in-tree (ties back to **C2**).

Full-suite pytest summary: **1219 passed, 3 skipped** (all three skips are
gated `needs_gkeyll`-style/explicitly-justified: the registry-quantity smoke
test skips `"distf"` with a stated reason, plus two pre-existing skips
unrelated to this layer). Architecture tests: `tests/test_postgkyl.py`, 32
passed, including the extended `_ALLOWED` edges.

## Verdict

**PASS WITH FIXES.** The physics is the hard part of this layer, and it is
right: every `fetch_*` formula was independently re-derived against its
`src_bak` weak-DG-kernel original and matches exactly (modulo the documented,
mandated interpolate-first representation change), the registry and
discovery logic are faithful transcriptions, no `loaders/` package leaked
back in, the import-contract edges match the instruction file precisely, and
coverage is 99% overall / ≥90% on every new module. The one concrete defect
(**C1**, `load_gk_distf`'s missing keyword-only `*`) is a real
PYTHON_PRINCIPLES rule-7 / doctrine-IV violation with no live symptom today
but a clear latent-footgun risk for the next caller, and should be fixed
before this is called done; **C3** is a one-line unused-import cleanup. **C2**
and **C4** are informational/non-blocking and do not by themselves justify a
fixer pass, but should be picked up while a fixer is in there for C1/C3.
