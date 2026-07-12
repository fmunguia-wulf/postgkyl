# Layer 13 — diagnostics programs — review

Scope reviewed (the diff between `b704725` and `40ac353`, the commit that
landed this layer): `src/postgkyl/diagnostics/gyrokinetics/{energy_balance,
particle_balance,nodes}.py`, `src/postgkyl/diagnostics/{trajectory,enstrophy,
ke_dke}.py`, the `diagnostics/__init__.py` and `diagnostics/gyrokinetics/
__init__.py` re-export additions, the `_ALLOWED` edge-map change in
`tests/test_postgkyl.py`, and the six new test modules
(`tests/test_diagnostics_programs_{energy_balance,particle_balance,nodes,
trajectory,enstrophy,ke_dke}.py`). Every new/changed file was read in full
and diffed line-by-line against its `src_bak` original
(`src_bak/postgkyl/apps/{gk_energy_balance,gk_particle_balance,gk_nodes,
trajectory}.py`, `src_bak/postgkyl/tools/{calc_enstrophy,calc_ke_dke}.py`).
No implementer report file exists on disk for this layer (checked
`.claude/migration/notes/`); the two out-of-scope claims this review was
asked to verify were relayed via the task prompt and independently
reproduced/verified below rather than trusted.

## Doctrine adherence

- **0. Locality of reasoning.** Adheres. Every non-obvious divergence from
  `src_bak` is explained exactly where it lives: the enstrophy/ke_dke bug
  fixes are justified in their own module docstrings (`enstrophy.py:10-20`,
  `ke_dke.py:9-28`), the dynvector-grid convention `trajectory.py` depends on
  is explained in its own docstring (lines 11-15) and re-justified in the
  test module's docstring, and the `fixaspect` API mismatch between old
  Typer's `plt.setp(ax, aspect=1.0)` and the new `Axes3D.set_box_aspect` is
  explained inline (`trajectory.py:150-153`).
- **I. Data is inert. Functions transform.** Adheres. `EnergyBalanceTraces`,
  `ParticleBalanceTraces`, `EnstrophyTraces`, `KineticEnergyTraces` are all
  frozen dataclasses; every diagnostic is a free function taking data +
  keyword options and returning a `(Figure, Traces)` tuple or a bare
  `Figure`/`FuncAnimation` — no class with behavior anywhere in this layer.
- **II. Make illegal states unrepresentable.** Adheres. Missing required
  files raise `FileNotFoundError` naming the missing path
  (`energy_balance.py:222,239`; `particle_balance.py:184`); `trajectory()`
  raises `ValueError` on an empty dataset list (`trajectory.py:131`) instead
  of failing later with an obscure index error.
- **III. A function is one idea.** Mostly adheres — `_enstrophy_terms`/
  `_kinetic_energy`/`_dissipation_rate`/`nodes_to_RZ`/`is_geo_mapc2p` are each
  one formula. See **C2** for one place a signature conflates two facts that
  should be resolved once, not twice, in the same program.
- **IV. The signature tells the whole truth.** Adheres for keyword-only
  discipline: `gk_energy_balance`, `gk_particle_balance`, `gk_nodes`,
  `trajectory`, `enstrophy`, `ke_dke` all put `*` before every option: none of
  the six new public entry points accept a boolean or optional file-override
  positionally. Violates in effect (not in the type signature) at
  **C1** — `gk_energy_balance`'s `relative_error=True` branch silently reads
  a *different* boolean (`has_apar_dot`, set in an earlier loop and out of
  scope by the time it's read) than the one the branch's own loop just
  computed (`has_apar`), so the function's true behavior depends on state the
  signature and the local code both obscure.
- **V. Every fact has one home.** Violates at **C2** —
  `_read_trace`/its docstring is duplicated verbatim between
  `energy_balance.py:115-125` and `particle_balance.py:88-98` instead of
  living once in `gyrokinetics/utils.py` beside
  `read_gfile_if_present`/`read_gfile`, which it wraps. `GKYL_GEOMETRY_ID`
  (`nodes.py:21-27`) is a second, hand-typed home for the same Gkeyll
  enum ordering `src_bak/postgkyl/gk/gkeyll_enums.py` held in one place —
  acceptable under PYTHON_PRINCIPLES rule 13 (single module, comment naming
  the exact header, pinned by a test at
  `tests/test_diagnostics_programs_nodes.py:39`), so not counted as a
  violation, but it is the second Gkeyll-enum transcription in this codebase
  (the first — the geometry table's own sibling enums,
  `gkyl_basis_type`/etc. — were never ported at all per the layer-12 review)
  and there is still no single shared `gyrokinetics/enums.py` home for
  Gkeyll-enum mirrors as a class of fact.
- **VI. Separate what from how.** Adheres. All CLI/Typer/`ctx.obj.data`
  machinery is gone; `set_tick_font_size`'s matplotlib-only helper is
  correctly re-implemented locally per module rather than resurrected from
  `gk_utils.py` as a shared "loader" concern (each module's own
  `_set_tick_font_size` is a private, three-line helper — arguably a case of
  earning a *third* copy rather than factoring one out, see **C4**).
- **VII. Notation is execution; lowering is transliteration.** Adheres for
  the physics: `energy_balance_error`/`particle_balance_error` are direct,
  named transliterations of the residual formulas stated in their own
  docstrings and in the module docstrings, verified algebraically identical
  to `src_bak`'s inline versions (`fdot - field_dot [- apar_dot]`, etc. —
  see Criticisms for the one place the *inputs* to that formula, not the
  formula itself, diverge).
- **VIII. Earn your abstractions.** Adheres overall — no premature
  factoring, `_accumulate`/`_resolve`/`_block_prefix` used many times each
  before being extracted. See **C2**/**C4** for two small under-factorings
  (duplication left unfactored past its second use, the opposite failure
  mode).
- **IX. An abstraction is a contract.** Adheres. `EnstrophyTraces`/
  `KineticEnergyTraces` state exactly what each field means and its shape
  relationship to the others (documented shape mismatch: `dke` is one
  shorter than `ke`).
- **X. Trust the most formal thing first.** Adheres — every public function
  is type-annotated, and the highest-risk numerics (the three fixed
  `src_bak` bugs, the two residual formulas, `nodes_to_RZ`) are pinned by
  analytic tests with hand-derived expected values, not just shape
  assertions.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **1 (absolute imports).** Adheres — no `postgkeyll` imports; the doubled-e
  name only appears in docstrings explaining what was ported from.
- **2 (respect the layer DAG).** Partially adheres. The `diagnostics ->
  render` edge was added to `_ALLOWED` exactly as the instruction file
  authorizes, but **no file in this layer's diff imports
  `postgkyl.render`** — every figure is built with raw
  `matplotlib.pyplot`/`matplotlib.animation`/`matplotlib.collections`
  directly (confirmed by grep across all six new modules). The edge is
  authorized by the instruction file so this is not a silent rule-2
  violation, but the comment added to `tests/test_postgkyl.py` ("program
  diagnostics compose figures directly with matplotlib/render helpers")
  overstates what the code does — see **C5**.
- **4 (no typer/ctypes).** Adheres — grepped the whole layer, no hits
  outside docstrings describing what was removed.
- **6/7 (type-annotate; keyword-only options).** Adheres across all six
  public entry points (see Doctrine IV above).
- **8 (no mutable default arguments).** Adheres — every default is `None`,
  a string/float/bool literal, or `"-10"`.
- **10 (raise, don't print-and-continue).** Adheres — `FileNotFoundError`/
  `ValueError`/`NameError` (via `utils.get_block_indices`, layer 12)
  throughout; no `print`+`None`.
- **12 (frozen records).** Adheres — all four new dataclasses are
  `@dataclass(frozen=True)`, and each is pinned by an explicit
  "is frozen" test (`TestKineticEnergyTracesIsFrozen`,
  `TestEnstrophyTracesIsFrozen`).
- **17 (one test file per module; coverage).** Adheres to the layer's own
  override (six `test_diagnostics_programs_*.py` files, one per new module).
  Coverage measured directly (see below): every new module is ≥87%, above
  the layer's 80% floor.
- **18 (assert values, not shapes).** Adheres, and is a strength of this
  layer: `TestEnstrophyTermsAnalytic`/`TestKineticEnergyAnalytic` use
  hand-derivable linear velocity fields so the curl and gradient-invariant
  integrals are exact by construction, not golden numbers.
- **19 (independent, deterministic tests).** Adheres — `tmp_path` +
  `monkeypatch` throughout, RNGs seeded where used
  (`_make_trajectory(seed=...)`), no network, Agg backend declared at each
  test module's top.
- **21 (copy liberally, fix documented bugs).** Adheres, and is this layer's
  strongest point for `enstrophy.py`/`ke_dke.py`: three distinct `src_bak`
  bugs (an aliased-array bug in each of enstrophy/ke_dke, an f-string typo,
  and an off-by-one loop bound) are each independently re-derived,
  confirmed genuinely unreachable-as-intended in the old code (see the
  Criticisms discussion for full verification), and documented in the
  module docstring rather than silently ported forward or silently
  "improved" without a trace. See **C1**, however, for one *undocumented*,
  untested behavioral divergence this review found that was not caught or
  disclosed by the implementer.
- **23 (never edit src_bak).** Adheres — `git diff b704725 40ac353` touches
  nothing under `src_bak/`.
- **24 (leave the tree green).** Adheres — `PYTHONPATH=src python -m pytest
  tests/ -q` passes in full (1293 passed, 6 skipped; see Coverage below).

## Out-of-scope claim 1 — the GkylCReader multi-component bug

**Confirmed, reproduces exactly as described.** Independent repro:

```python
d = GDataState(); d.push([grid_of_5_edges], values_shape_(4,2))
io.write(d, out_name=".../test2comp.gkyl", extension="gkyl")
GData(out)   # -> OSError: '...' pg0_read_field failed
```

Root cause, traced to source: **`src/postgkyl/io/writer.py`'s `_write_gkyl`**
(around the `# asize` line). The on-disk `.gkyl` format's "array size" field
is documented (and consumed) elsewhere in the codebase as the **cell
count**, not the total scalar count — confirmed by reading the pure-Python
fallback reader, `src/postgkyl/io/gkyl_reader.py:374`:
`self._get_data(self.asize*self.num_comps)` (it multiplies `asize` by
`num_comps` itself to get the total scalar count, meaning `asize` alone must
be the cell count). But the writer emits
`np.array([np.size(values)], ...)  # asize` — `np.size(values)` is
`num_cells_product * num_comps`, already including the component
multiplication. For `num_comps == 1` the two are numerically identical
(masking the bug), so every single-component round trip "round-trips fine";
for `num_comps >= 2` the file's declared array size is wrong by exactly a
factor of `num_comps`, and Gkeyll's own C reader
(`gkyl_grid_array_new_from_file`, called by `ffi/rio.py::read_field`, which
`GkylCReader` tries first) — correctly rejects the malformed file with
`pg0_read_field failed`.

**Whose bug, and does it block layer 13:** this is a pre-existing bug in
`io/writer.py`, introduced when `_write_gkyl` was first written (traced with
`git log -p` to migration layer `1ece639`/`4e216e1`, "04-io"/metadata layers
— several layers below `diagnostics/`, and outside a diagnostics-programs
layer's authorized scope to touch). It is **not** a bug in `ffi/rio.py` or
in `GkylCReader` itself — both are faithfully executing Gkeyll's own C file
reader against a file `postgkyl`'s own writer built incorrectly; blaming the
reader would be blaming the messenger.

**Does it mask real coverage gaps in this layer's own tests:** checked every
skip/workaround in the six new test modules individually. **It does not.**
- `energy_balance.py`/`particle_balance.py`/`enstrophy.py`/`ke_dke.py`'s full
  test suites monkeypatch `GData` (or `utils.GData`) directly and never call
  `io.write` at all — their "loud skips" (the `TestGk*RealFixtures` classes)
  are skipped because `tests/test_data` ships no multi-file gyrokinetic
  energy/particle-balance file family, a fixture-staging gap wholly
  unrelated to the write/read round-trip bug.
- `nodes.py`'s one loud skip (`TestGkNodesPsiOverlayRealFixtures`) is skipped
  because the one shipped p2-tensor fixture is 9-component and `gk_nodes`
  hands the whole interpolated array straight to `pcolormesh`/`contour`
  without selecting a component (a real, but separately-documented and
  `src_bak`-inherited, usability gap — `src_bak/postgkyl/apps/gk_nodes.py`
  has the identical unconditional-transpose-and-plot pattern, so this is not
  a new bug either) — again unrelated to the writer bug.
- `trajectory.py`'s test suite is the *only* one that actually exercises
  `io.write`, and it does so **honestly**: the docstring
  (`tests/test_diagnostics_programs_trajectory.py:154-171`) states plainly
  that only the single-component case is exercised via real I/O and why,
  and the multi-component/real-3-vector trajectory case is instead exercised
  directly against a hand-built `GDataState` (no disk I/O) in
  `TestTrajectorySynthetic`, so no assertion is silently skipped — the
  coverage that would have come from the disk round trip is provided by a
  different, still-real, test.

**Verdict on claim 1:** confirmed and correctly out of scope. The
implementer's diagnosis is accurate down to the exact field; this review
additionally pins the root cause to a specific line
(`src/postgkyl/io/writer.py`, `_write_gkyl`'s `asize` field) that the
implementer's summary did not name. Recommend a follow-up fix in `io/`
(`asize` should be `int(np.prod(num_cells))`, not `np.size(values)`) tracked
separately from this layer — it is a real, reproducible defect, but touching
`io/writer.py` is not authorized by this layer's instruction file and does
not block this layer's own definition of done.

## Out-of-scope claim 2 — dead code in gyrokinetics/utils.py

**Confirmed dead, but the workaround introduces a new doctrine-V violation
of its own.**

Verified `GDataState.grid`'s actual implementation
(`src/postgkyl/core/state.py:36,117-126`): `self._grid: list | None = None`,
set only via `set_grid(grid: list)`, and every reader's `read()` return path
was checked (`io/gkyl_reader.py:492,498,504`: `grid = [time]` or
`grid = mapping.uniform_grid(...)`, both lists) — `GDataState.grid` never
returns a bare `np.ndarray` anywhere in this codebase's container contract.
So yes: the `isinstance(grid, np.ndarray)` branches in
`gyrokinetics/utils.py:42-46` (`read_gfile`) and `:94-98`
(`read_interp_gfile`) are genuinely unreachable dead code inherited verbatim
from `src_bak`, exactly as the 12-diagnostics-loaders review already found
and accepted as a justified "defensive unreachable branch" (PYTHON_PRINCIPLES
rule 17's carve-out).

Where this review disagrees with "no action needed": layer 13 did not
*just* leave the dead branch alone (a defensible, low-cost choice on its
own) — it **added a second, independent function that re-derives the same
"grid is always a list" fact from scratch, in two places**:
`energy_balance.py:115-125`'s `_read_trace` and
`particle_balance.py:88-98`'s `_read_trace` are byte-for-byte identical
(same body, same docstring), each locally re-asserting via comment that
`utils.read_gfile_if_present` always returns a list, then unwrapping
`grid[0]`. That is doctrine V's exact failure mode: the same fact ("this
grid is always a length-1 list; take its one entry") now has *three* homes
in the tree — the dead, unreached `isinstance` branch in `utils.py` that
implies the opposite is possible, and two copy-pasted private functions in
sibling modules that assert it can't happen. The clean fix was to add one
function to `gyrokinetics/utils.py` (e.g. `read_time_trace_if_present`)
that both programs import, which would have been the natural moment to
also either delete the dead branches or leave a single comment there
instead of two. Layer 13 was not *obligated* to fix layer 12's dead code —
but it was already touching this exact fact (grid-unwrapping for time
traces) twice in its own diff, which is precisely the "earn it on the
second use" trigger PYTHON_PRINCIPLES/doctrine VIII describes, and it built
two private copies instead of one shared one. See **C2**.

**Verdict on claim 2:** the dead-code claim is confirmed and, taken alone,
non-blocking (same as the 12-diagnostics-loaders review's disposition).
But the workaround chosen compounds it into a live, in-layer doctrine-V
duplication that this review must flag as its own criticism (**C2**) —
distinct from, and more actionable than, the pre-existing dead branch.

## Criticisms

**C1 — `gk_energy_balance`'s relative-error/electromagnetic path reads the wrong boolean and can crash on a real (if unusual) input** (`src/postgkyl/diagnostics/gyrokinetics/energy_balance.py:349-366`).
In the `relative_error=True` branch, `has_apar` (set from the *energy* file,
`apar_energy.gkyl`, read inside this branch's own per-block loop at line
338) correctly gates whether `apar` gets accumulated at all (line 350-352:
`if has_apar: apar = _accumulate(apar, apar_pb)`). But three lines later,
the slicing and the residual/denominator computation switch to gating on
`has_apar_dot` instead — a *different* flag, set from the *rate-of-change*
file (`apar_energy_dot.gkyl`) in an earlier, unrelated loop (line 228,
outside this branch):
```python
field, field_dot = field[1:], field_dot[1:]
if has_apar_dot:                              # <- wrong flag
  apar, apar_dot = apar[1:], apar_dot[1:]
...
mom_err = energy_balance_error(fdot, src, bflux_tot, field_dot,
    apar_dot if has_apar_dot else None)
denom = (distf - field - apar) if has_apar_dot else (distf - field)
```
If a simulation's output has an `apar_energy_dot.gkyl` file but is missing
(or the caller omits) the corresponding `apar_energy.gkyl` file — an
inconsistent but entirely plausible input (e.g. a user overrides
`apar_dot_file` explicitly but not `apar_file`, or the two are produced by
different diagnostics passes) — `apar` is still `None` at this point
(never accumulated, since `has_apar` was `False`), and
`apar, apar_dot = apar[1:], apar_dot[1:]` raises
`TypeError: 'NoneType' object is not subscriptable`. `src_bak`'s original
(`src_bak/postgkyl/apps/gk_energy_balance.py:455-469`) does not have this
divergence: it consistently reads and branches on the *single* `has_apar`
flag defined in that same relative-error block for every apar-dependent
line (slicing, residual, denominator) — the rate-of-change loop's
`has_apar_dot` is a separate, unrelated name in the old code and is never
reused here. This is a real, untested code path: no test in
`tests/test_diagnostics_programs_energy_balance.py` builds a fixture where
`apar_dot` and `apar` (energy) disagree on presence — every `with_apar=True`
test (`test_electromagnetic_branch`,
`test_relative_error_electromagnetic_absy_and_saveas`) stages both files
together, and the `with_apar=False` default omits both. Fix: replace
`has_apar_dot` with `has_apar` at every reference inside the `else:`
(`relative_error`) branch (the slicing, `energy_balance_error(...)` call,
and `denom` computation), matching `src_bak`'s single-flag discipline; add a
regression test that stages `apar_energy_dot.gkyl` without
`apar_energy.gkyl` under `relative_error=True` and asserts either a clear
error or the correct (has_apar-gated) fallback rather than a `TypeError`.

**C2 — `_read_trace` is copy-pasted verbatim between `energy_balance.py` and `particle_balance.py` instead of living once in `gyrokinetics/utils.py`** (`src/postgkyl/diagnostics/gyrokinetics/energy_balance.py:115-125`, `src/postgkyl/diagnostics/gyrokinetics/particle_balance.py:88-98`).
Identical function body, identical docstring (down to the wording
explaining that `GDataState.grid` never returns a bare `ndarray`), defined
twice. A future change to the underlying "grid is always a list of one for
1-D traces" assumption (or a bugfix to how `found=False` is represented)
has to be made in two places and will silently drift if only one copy is
updated — precisely doctrine V's "everything else inherits or is derived
mechanically, never maintained by hand in parallel." Fix: move
`_read_trace` into `gyrokinetics/utils.py` as a new public
`read_time_trace_if_present(file_name)`, imported by both
`energy_balance.py` and `particle_balance.py`; delete both private copies.
While there, either delete the now-doubly-redundant dead `isinstance(grid,
np.ndarray)` branches in `read_gfile`/`read_interp_gfile` or add one
comment at their definition site instead of the two comments this layer
added at the call sites (see "Out-of-scope claim 2" above).

**C3 — No on-disk implementer report for this layer** (Definition-of-Done item 3).
The instruction file's Definition of Done asks for "Report: per-diagnostic
parameter surface (old CLI options → new kwargs), fixtures missing that
forced skips, coverage, pytest summary." No file exists under
`.claude/migration/notes/` for layer 13 (only `09-render-parity.md` and
`12-diagnostics-loaders-report.md` are present, both predating this layer's
commit). The substance is present, just distributed across each new test
module's own docstring (each explains its missing fixtures and its
coverage-relevant design choices individually) rather than collected in one
place — the same gap flagged as informational/non-blocking in the
12-diagnostics-loaders review. Non-blocking for the same reason: this
review independently reconstructed the equivalent content (see Coverage
below) and it checks out.

**C4 — `_set_tick_font_size` is a private near-identical three-line helper duplicated across `energy_balance.py`, `particle_balance.py`, and `nodes.py`** (each module, e.g. `nodes.py:101-102`).
Minor. Three call sites of the same three-line body
(`ax.tick_params(...)` + offset-text sizing) is right at PYTHON_PRINCIPLES'
"three similar lines is better than a premature helper" threshold — earning
a shared helper (e.g. in `gyrokinetics/utils.py`, alongside where **C2**'s
fix would land `read_time_trace_if_present`) would remove the third
independent place someone has to update tick-font sizing, but this is
lower-severity than **C2** because there is no formula/behavior encoded
here that could silently drift, only a font-size call. Non-blocking.

**C5 — The `_ALLOWED["diagnostics"]` comment claims a `render` import that does not exist** (`tests/test_postgkyl.py`, the `"render"` entry's comment on the `diagnostics` edge).
The comment added by this layer reads "the program-scale diagnostics
(gk_nodes, trajectory) build figures directly with matplotlib/render
helpers" — but grepping every file in this layer's diff shows zero imports
of `postgkyl.render` anywhere; all six modules use
`matplotlib.pyplot`/`matplotlib.animation`/`matplotlib.collections`
directly instead (a defensible choice — `render.plot()`'s generic
one-panel-per-component contract doesn't fit these bespoke, multi-trace/
multi-block figures — but the comment overstates what the code does).
Because the layer instruction file explicitly pre-authorizes the edge
regardless of whether it ends up used, this is not a rule-2 violation, and
the unused edge creates no cycle risk. But it is a small, checkable
inaccuracy in the one file (`tests/test_postgkyl.py`) whose comments are
supposed to be the load-bearing record of *why* each edge exists. Fix:
either import `postgkyl.render` somewhere it is genuinely useful (unlikely
to be worth forcing), or reword the comment to say the edge is
pre-authorized for future program diagnostics rather than describing
current, nonexistent usage.

No other criticisms. Every one of the five source→target ports
(`gk_energy_balance`, `gk_particle_balance`, `gk_nodes`, `trajectory`,
`calc_enstrophy`→`enstrophy`, `calc_ke_dke`→`ke_dke`) was diffed line by
line against its `src_bak` original; apart from **C1** (found by this
review, not disclosed by the implementer) and the three enstrophy/ke_dke
bug fixes (found by the implementer and independently reverified here as
genuine, unambiguous bugs — see the walk-through under Doctrine-adherence
rule 21), no other numerical divergence was found. The `GKYL_GEOMETRY_ID`
enum transcription in `nodes.py` matches
`gkeyll/core/zero/gkyl_eqn_type.h`'s `enum gkyl_geometry_id` exactly and is
pinned by a test.

## Coverage

```
PYTHONPATH=src python -m coverage run -m pytest tests/ -q
# 1293 passed, 6 skipped in ~65s
PYTHONPATH=src python -m coverage report -m --include="*/postgkyl/diagnostics/*"
```

```
Name                                                        Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------
src/postgkyl/diagnostics/__init__.py                            2      0   100%
src/postgkyl/diagnostics/discovery.py                          27      0   100%
src/postgkyl/diagnostics/enstrophy.py                          45      0   100%
src/postgkyl/diagnostics/five_moment.py                       116      0   100%
src/postgkyl/diagnostics/gyrokinetics/__init__.py               9      0   100%
src/postgkyl/diagnostics/gyrokinetics/distf.py                 69      7    90%   166-167, 170-171, 173-174, 177
src/postgkyl/diagnostics/gyrokinetics/energy_balance.py       182      1    99%   392
src/postgkyl/diagnostics/gyrokinetics/load_quantity.py         29      0   100%
src/postgkyl/diagnostics/gyrokinetics/nodes.py                115     15    87%   225-245, 270
src/postgkyl/diagnostics/gyrokinetics/particle_balance.py     132      3    98%   275, 285, 288
src/postgkyl/diagnostics/gyrokinetics/quantities.py           159      0   100%
src/postgkyl/diagnostics/gyrokinetics/quantity.py             115      0   100%
src/postgkyl/diagnostics/gyrokinetics/registry.py              52      0   100%
src/postgkyl/diagnostics/gyrokinetics/utils.py                 65      2    97%   43, 95
src/postgkyl/diagnostics/ke_dke.py                             32      0   100%
src/postgkyl/diagnostics/kinetic.py                            46      0   100%
src/postgkyl/diagnostics/mhd.py                                79      0   100%
src/postgkyl/diagnostics/multispecies.py                       41      0   100%
src/postgkyl/diagnostics/pkpm.py                               43      0   100%
src/postgkyl/diagnostics/plasma.py                             95      0   100%
src/postgkyl/diagnostics/rotations.py                          26      0   100%
src/postgkyl/diagnostics/ten_moment.py                        178      0   100%
src/postgkyl/diagnostics/trajectory.py                         58      0   100%
-----------------------------------------------------------------------------------------
TOTAL                                                        1715     28    98%
```

New-module breakdown (this layer's actual deliverable): `enstrophy.py`
100%, `ke_dke.py` 100%, `trajectory.py` 100%, `gyrokinetics/energy_balance.py`
99%, `gyrokinetics/particle_balance.py` 98%, `gyrokinetics/nodes.py` 87%. All
clear the layer's 80% floor by a wide margin; `distf.py`/`utils.py` are
layer-12 files untouched by this diff and unchanged from the 12-review's
numbers (90%/97%).

Justification check on every non-100% new-module line:
- `energy_balance.py:392` — the `if show: plt.show()` interactive-display
  line. Justified: no test can assert anything about an interactive
  `plt.show()` block; every other line in the function is exercised.
- `particle_balance.py:275,285,288` — `absy`-with-truthy-`ylabel_string` in
  the relative-error branch, `saveas`, and `if show: plt.show()`. The
  `saveas`/`show` gaps are the same category as `energy_balance.py:392`;
  the `absy` line is a real, if minor, miss (see below — not independently
  flagged as a numbered criticism since it is a one-line str-formatting
  branch with no numerical content, but noted here since the coverage table
  surfaces it).
- `nodes.py:225-245,270` — the `psi_file` overlay's colormesh/contour/
  colorbar block and its trailing `if show: plt.show()`. Justified and
  independently reverified: the repo's one shipped p2-tensor-basis 2-D
  fixture (`tests/test_data/generated/2d_mt_p2.gkyl`) is 9-component, and
  `gk_nodes` (both old and new) feeds the whole interpolated array straight
  to `pcolormesh`/`contour` without a component selector, so this fixture
  cannot exercise that branch meaningfully — confirmed by reading both the
  old and new source (identical unconditional-transpose-and-plot pattern),
  not a new gap this layer introduced.
- `utils.py:43,95` — the dead `isinstance(grid, np.ndarray)` branches,
  re-verified genuinely unreachable in this review's own investigation of
  "Out-of-scope claim 2" above. Holds up as a justified miss, but see
  **C2** for why the way this layer worked around it (rather than just
  leaving it) creates a new, avoidable duplication.

Full-suite pytest summary: **1293 passed, 6 skipped**. Architecture tests
(`tests/test_postgkyl.py`, including the extended `_ALLOWED` edges): 32
passed.

## Verdict

**PASS WITH FIXES.** The three inherited `src_bak` bugs this layer fixes
(enstrophy's aliased result array, ke_dke's aliased result array *and*
its literal-string file-name typo *and* its off-by-one difference loop) are
each real, each independently re-verified as unambiguous bugs by this
review, and each is documented and tested to the standard doctrine 21
demands — this is the layer's strongest work. Both out-of-scope claims the
implementer flagged are confirmed genuine and correctly judged out of this
layer's authorized scope (the `io/writer.py` `asize` bug is several layers
below `diagnostics/` and does not block or mask this layer's own test
coverage; the `utils.py` dead-code branches are genuinely unreachable under
this codebase's container contract). What keeps this from a clean PASS is
**C1** — a real, untested, undocumented behavioral divergence this review
found in `gk_energy_balance`'s relative-error/electromagnetic path (reading
`has_apar_dot` where `has_apar` is required, which can raise `TypeError` on
a plausible mismatched-file input) — together with **C2**, a live
doctrine-V duplication this layer introduced (not merely inherited) while
working around the layer-12 dead code. Both are narrowly scoped, mechanical
fixes (swap one flag name; hoist one duplicated function into
`gyrokinetics/utils.py`) that a fixer pass can close without touching the
five other diagnostics or their tests.

## Path

`.claude/migration/reviews/13-diagnostics-programs-review.md`

## Resolutions

C1: FIXED — `gk_energy_balance`'s `relative_error=True` branch
(`src/postgkyl/diagnostics/gyrokinetics/energy_balance.py`) gated the
`[1:]` slicing of `apar`/`apar_dot`, the `energy_balance_error(...)` call's
`apar_dot` argument, and the `denom` computation on `has_apar_dot` (the flag
from the earlier, unrelated per-block loop reading `apar_energy_dot.gkyl`)
instead of `has_apar` (the flag from this branch's own loop reading
`apar_energy.gkyl`). Replaced `has_apar_dot` with `has_apar` at all three
sites, now `energy_balance.py:338,344-346`, matching
`src_bak/postgkyl/apps/gk_energy_balance.py:455-469`'s single-flag
discipline. Added a regression test,
`tests/test_diagnostics_programs_energy_balance.py::TestGkEnergyBalanceSynthetic::test_relative_error_apar_dot_present_without_apar_energy`,
which stages `apar_energy_dot.gkyl` without `apar_energy.gkyl` under
`relative_error=True`; verified it reproduces `TypeError: 'NoneType' object
is not subscriptable` against the pre-fix code and passes against the fix.

C2: FIXED — Removed the duplicated `_read_trace` from both
`src/postgkyl/diagnostics/gyrokinetics/energy_balance.py` and
`src/postgkyl/diagnostics/gyrokinetics/particle_balance.py`; both now call a
single new `read_time_trace_if_present(file_name)` added to
`src/postgkyl/diagnostics/gyrokinetics/utils.py:53-67`. While there, also
removed the dead `isinstance(grid, np.ndarray)` branches from
`read_gfile`/`read_interp_gfile` in `utils.py` (now unconditional
list-comprehension squeezing, `utils.py:28-45,86-107`) since
`GDataState.grid` never returns a bare `ndarray` — confirmed no test in
`tests/test_diagnostics_gk_load.py` targeted that branch specifically
(`test_read_gfile*`/`test_read_interp_gfile*` only exercise the list path),
so nothing needed updating there. `utils.py` coverage moved from 97% to
100% as a direct result (the two removed lines were exactly the review's
two justified-miss lines, `utils.py:43,95` in the original numbering).

C3: DECLINED — Per the review's own disposition ("non-blocking... this
review independently reconstructed the equivalent content... and it
checks out") and the task instructions for this fixer pass, which
explicitly permit skipping C3 since it was marked non-blocking/
informational. The Definition-of-Done report's substance already lives,
one fact in one place, distributed across each new test module's own
docstring (missing fixtures, coverage-relevant design choices); writing a
separate `.claude/migration/notes/13-*.md` file now would duplicate those
facts in a second location — the opposite of doctrine V — rather than add
new information. This report's own Coverage section below supersedes what
such a note would contain.

C4: FIXED — Consolidated the three near-identical copies of
`_set_tick_font_size` (`energy_balance.py`, `particle_balance.py`,
`nodes.py`) into one `set_tick_font_size(ax, size)` in
`src/postgkyl/diagnostics/gyrokinetics/utils.py:109-113`; all three modules
now call `utils.set_tick_font_size(...)` (`energy_balance.py:362`,
`particle_balance.py:258`, `nodes.py:257`) instead of defining their own
copy. This also fixed a small undocumented divergence: `nodes.py`'s private
copy had dropped the offset-text sizing lines present in
`src_bak/postgkyl/gk/gk_utils.py:26-32`'s `set_tick_font_size` (and in the
other two modules' copies) — the shared helper restores that behavior for
`gk_nodes` too, matching `src_bak`.

C5: FIXED — Reworded the `"render"` edge's comment on the `"diagnostics"`
entry in `tests/test_postgkyl.py`'s `_ALLOWED` map (around the edge's
comment block) from asserting current usage ("build figures directly with
matplotlib/render helpers") to stating the edge is pre-authorized by
`13-diagnostics-programs.md` for future program-scale diagnostics, and
naming that none of the six current program modules (`energy_balance`,
`particle_balance`, `nodes`, `trajectory`, `enstrophy`, `ke_dke`) actually
import `postgkyl.render` today. The edge itself and all four architecture
tests are unchanged.

Full suite after fixes: **1294 passed, 6 skipped** (one more passing test
than the review's baseline of 1293, from C1's new regression test).
Architecture tests (`tests/test_postgkyl.py`): 32 passed, unchanged.

Coverage after fixes (`--include="*/postgkyl/diagnostics/*"`):
`energy_balance.py` 99% (174 stmts, 1 miss — line 373, the interactive
`if show: plt.show()`, unchanged from baseline); `particle_balance.py` 98%
(124 stmts, 3 misses — `absy`/`saveas`/`show` lines, unchanged from
baseline); `nodes.py` 87% (113 stmts, 15 misses — the `psi_file` overlay
block, unchanged from baseline); `utils.py` **100%** (69 stmts, 0 misses —
up from the review's baseline of 97%, since the two dead-branch misses were
removed rather than left unreached, and `read_time_trace_if_present`/
`set_tick_font_size` are both fully exercised by the existing and new
tests). Total layer coverage: 98% (1701 stmts, 26 misses).
