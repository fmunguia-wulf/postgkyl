# Migration plan — `src_bak/` → `src/` (layer by layer)

Goal: port every still-relevant capability of the old codebase
(`src_bak/postgkyl/`) into the new layered architecture (`src/postgkyl/`,
described in `CLAUDE.md`), bottom-up, one layer at a time, with comprehensive
unit tests and a doctrine review after each layer.

Governing documents (every agent reads all three before touching code):
- `/home/maxwell-rosen/postgkyl/.claude/DOCTRINE.md` — the coding doctrine
- `/home/maxwell-rosen/postgkyl/.claude/migration/PYTHON_PRINCIPLES.md` — Python rules
- `/home/maxwell-rosen/postgkyl/CLAUDE.md` — the architecture (layer DAG, domains)

Key facts every agent must know:
- `src_bak/` top-level imports spell `postgkeyll` (double-e) — a package that
  does not exist. The old tree cannot be imported; it is a read-only quarry.
  Rewrite every import when copying.
- The old CLI is Typer; the new one is Click. Typer never appears in `src/`.
- The old ctypes path (`tools/gkeyll_dg_ops.py`, `_gkylsoft_path.py`), the
  sympy matrix generators (`data/computeInterpolationMatrices.py`,
  `computeDerivativeMatrices.py`), and `modalDG/` are **superseded by `ffi/`**
  (compiled shim). Re-provide capabilities, never copy that code.
- The compiled shim is built (`src/postgkyl/ffi/_g0py.so`) and
  `ffi.available()` is True on this machine — modal-domain tests run for real.
- Baseline: `PYTHONPATH=src python -m pytest tests/ -q` → 26 passed.

## Per-layer process (three agents, strictly sequential)

For each layer `XX-<name>`:

1. **Implementer** — follows `.claude/migration/layers/XX-<name>.md`. Ports
   code + writes `tests/test_<name>_*.py`. Ends with the full suite green and
   a coverage report for the layer's modules.
2. **Reviewer** — reads the layer diff; writes
   `.claude/migration/reviews/XX-<name>-review.md`: doctrine adherence
   (principle by principle, 0–X), concrete criticisms ranked by severity with
   `file:line`, coverage gaps, and behavioral divergence from `src_bak/`.
   The reviewer changes no code.
3. **Fixer** — addresses every criticism in the review doc (fix it, or append
   a written justification for not fixing under a `## Resolutions` heading in
   the same doc). Ends with the full suite green.

Then the **orchestrator checkpoint** (see below) runs before the next layer
starts. Each layer is committed after its checkpoint passes.

## Layers, in order

| # | Layer | Instruction file | Source material (src_bak) → target (src) |
|---|-------|-----------------|------------------------------------------|
| 01 | ffi | `layers/01-ffi.md` | Audit + test the existing floor: `ffi/{_lib,array,basis,kernels,rio,rep}.py`. No new features; near-100% coverage of the Python half. |
| 02 | numerics | `layers/02-numerics.md` | `tools/{calculus,mag_sq,rel_change,rotation_matrix,fft,init_polar,polar_isotropic,fit,growth,filters}.py`, `tools/ev_ops.py` (math only), `utils/{nodal_to_cell_centered_grid,downsample}.py` → `numerics/`. Pure arrays in/out. |
| 03 | dg | `layers/03-dg.md` | Move `ffi/rep.py` → `dg/rep.py` (reconcile CLAUDE.md drift); add `dg/map.py` per `MAPPING.md`; investigate + document a differentiation strategy on `ffi.basis`. |
| 04 | io | `layers/04-io.md` | `data/{gkyl_adios_reader,gkyl_h5_reader,flash_h5_reader}.py` → `io/` reader registry; `data/mapping.py::c2p_grid`; `data/write.py` VTK + series → `io/writer.py`. |
| 05 | core | `layers/05-core.md` | `group.py::DatasetGroup` → `core/group.py` (verb-less, per doctrine). |
| 06 | models | `layers/06-models.md` | `tools/{prim_vars,pressure_diagnostics,params,energetics,accumulate_current,parrotate,perprotate,transform_frame,laguerre_compose}.py` → new `models/` (euler, tenmoment, mhd, gk). Constants from `scipy.constants`. *(Superseded by layer 10: `models/` was folded into `diagnostics/`.)* |
| 07 | ops-field | `layers/07-ops-field.md` | Field-domain verbs: `ops/{fft,magsq,relchange,mask,collect,grid,val2coord,extract_input,fit,growth,differentiate,ev}.py` → new `ops/` modules on the new verb contract. |
| 08 | ops-physics | `layers/08-ops-physics.md` | Physics verbs: `ops/{moments,agyro,current,energetics,rotate,transform_frame,laguerre,map}.py` → new `ops/` modules delegating to `models/` and `dg/map.py`. *(Superseded by layer 10: the physics verbs moved to `diagnostics/`; `map` and the select guard stay in `ops/`.)* |
| 09 | render | `layers/09-render.md` | `output/{plot,plotly,pyvista}.py` full feature set (animate, movie, multi-panel, colorbar, styles) + `utils/{axis_and_grid_prep,load_plot_data,latex_conversion,load_style}.py` → `render/`. |
| 10 | diagnostics (restructure) | `layers/10-diagnostics.md` | **No src_bak porting.** Fold `models/` + the seven `ops/` physics verbs into a new `diagnostics/` package, one module per equation model (`five_moment, ten_moment, mhd, plasma, multispecies, rotations, kinetic, pkpm`); delete `models/`; move the field-domain guard to `core/guards.py`; zero numerical change (parity vs git HEAD). |
| 11 | api | `layers/11-api.md` | Fluent methods on `api/gdata.py` for every core verb (no physics methods — diagnostics sits above api); facade re-exports in `__init__.py`. |
| 12 | diagnostics loaders | `layers/12-diagnostics-loaders.md` | **No top-level `loaders/`.** `loader.py::find_output_stems` → `diagnostics/discovery.py`; `loaders/{gk_distf,gk_quantity}.py` + `gk/gk_quantities/*` (registry + fetch physics rewired from ctypes to the new surface) + `gk/gk_utils.py` → `diagnostics/gyrokinetics/`; `loaders/pkpm.py` → `diagnostics/pkpm.py`. Each equation model owns its loading internally. |
| 13 | diagnostics programs | `layers/13-diagnostics-programs.md` | `apps/{gk_energy_balance,gk_particle_balance,gk_nodes,trajectory}.py`, `tools/{calc_enstrophy,calc_ke_dke}.py` → `diagnostics/gyrokinetics/` + `diagnostics/{trajectory,enstrophy,ke_dke}.py` (Typer shed; file resolution through `diagnostics.discovery`). |
| 14 | cli | `layers/14-cli.md` | All remaining `commands/*` → thin Click shells in `cli/commands/`; physics commands shell `pg.diagnostics.<module>`; infra (`verb_print`, `set_frame`, style/config/status/listoutputs). |
| 15 | facade & docs | `layers/15-facade.md` | Final facade sync, CLAUDE.md verb-list update, full-tree coverage report, end-to-end benchmarks. |

Detailed instruction files are written just before each layer launches, so
layer N's instructions reflect what layers < N actually built. The scope
column above is fixed; only the "how" is deferred.

### Amendment (2026-07-10, after layer 09) — models → diagnostics

The `models/` layer was misplaced. Evidence from the landed code: every
`models/` function has exactly one consumer (the layer-08 ops physics verbs)
— an unearned abstraction (doctrine VIII) — and the split forced a
stringly-typed dispatch (`euler(d, variable="pressure")`), which doctrine IV
forbids. The physics functions are compositions, not machinery: multi-dataset
and equation-aware (`energetics(elc, ion, field)`, `agyro(pressure, bfield)`,
all of `plasma_params`). They belong in the COMPOSITION tier, above `api`.

Resolution: layers were renumbered after 09. A new layer 10 (restructure, no
src_bak porting) folds `models/` + the ops physics verbs into
`diagnostics/`, organized one module per equation model; the old layer 12
(apps → figures) became layer 13 and lands its programs inside the same
package. `ops/` is now the equation-blind core-verb library; `diagnostics/`
functions are free functions (never `GData` methods — the layer sits above
`api`). CLAUDE.md's architecture section is the authoritative statement of
the new shape. Historical documents (CHECKPOINTS rows ≤ 09, reviews ≤ 09, and layer files
≤ 09, whose cross-references like "layer 10"/"layer 12" use the old
numbering) are left untouched; they describe what was true when written.
Layer files ≥ 10 use the new numbering.

Second amendment (same date): there is no top-level `loaders/` package
either. The old GK quantity registry fused naming-convention loading with
gyrokinetic physics (`fetch_Tpar_*`, `fetch_beta_*`, drift velocities —
diagnostics in all but name), and the old apps duplicated its discovery logic
with private globbing. Both halves have one home now: each equation model
loads its own files inside its `diagnostics/` module or subpackage
(`gyrokinetics/{distf,load_quantity,quantities,registry}.py`,
`pkpm.load_pkpm`), and the equation-blind stem discovery is shared as
`diagnostics/discovery.py`. The COMPOSITION tier is the single `diagnostics/`
package. Layer 12 was renamed accordingly (`12-diagnostics-loaders.md`); no
`"loaders"` layer is ever added to `_ALLOWED`.

## Orchestrator checkpoints (run between layers, recorded in CHECKPOINTS.md)

- **C1 green tree:** `PYTHONPATH=src python -m pytest tests/ -q` — zero failures.
- **C2 architecture contract:** the four AST tests pass
  (`test_facade_is_pure_reexport`, `test_import_contract_no_violations`,
  `test_foreign_floor_confined_to_ffi`, `test_import_graph_is_acyclic`).
- **C3 coverage:** `pytest --cov=postgkyl.<layer>` 100% lines for the
  layer's modules; every miss listed and justified in the review doc.
- **C4 golden scripts:** the fluent chain
  `pg.load(...).interp().sel(...).plot()` and the CLI chain
  `pgkyl <file> interp sel --z0 0 plot --save` still work on
  `tests/test_data/` files (already encoded in `tests/test_postgkyl.py`).
- **C5 review closed:** the layer's review doc exists and every criticism has
  a fix or a written resolution.
- **C6 no regressions in old behavior:** where a `tests_bak/` test was ported,
  its numerical assertions still hold (tolerance-level agreement with the old
  implementation), unless the instruction file documents an intentional change
  (e.g. `integrate` now runs modal-side; `map` per MAPPING.md).

## End-state benchmarks (layer 14)

- Full suite green with `--cov=postgkyl` 100% overall.
- Every verb in the CLAUDE.md architecture table exists and is reachable from
  (a) `pg.load(...)` fluent chains and (b) `pgkyl` CLI chains.
- `pgkyl --help` lists all commands; every command's `--help` renders.
- A fresh `pip install -e .[test]` + `pytest` passes (packaging intact).
- `git grep -l "postgkeyll\|typer\|ctypes" src/` returns nothing.

## Deferred / known-open items (append as discovered)

- `differentiate`: exact modal derivative needs basis-gradient evaluation from
  the shim; layer 03 investigates and either implements or documents the
  fallback (post-interp `np.gradient`) — decision recorded in the layer 03
  review. **Resolved (layer 07):** `ops/differentiate.py` implements the
  field-domain `np.gradient` fallback per
  `.claude/migration/notes/differentiate-decision.md`; the exact modal
  derivative (Approach A: wrap the shim's `eval_grad_expand` as
  `pg0_basis_eval_grad`) remains permanently deferred — it requires editing
  C sources in the `gkeyll/` submodule and `gpython/csrc/`, out of every
  layer's authorized Python-only scope. Not revisited by layer 15.
- `dg_local_poly`, `dg_avg`, `dg_evproj` (old ctypes/modalDG commands):
  capabilities re-provided by `ffi.basis`/`ops.represent`; port only if a
  concrete gap remains after layer 08. **Resolved:** never ported — their
  capabilities are covered by `ops.represent`/`ops.apply`
  (`.to_modal()/.to_nodal()/.to_quad()/.apply()`), and
  `tests/test_cli_commands.py::test_config_and_dg_commands_are_not_registered`
  pins that none of `config`/`dg_local_poly`/`dg_avg`/`dg_evproj` exist as
  CLI commands.
- ADIOS reader tests require `adios2` (optional dep) — tests skip when
  absent. **Standing**, not a defect; unchanged through layer 15 (confirmed:
  `adios2` is not installed in this environment, `TestGkylAdiosReader`-style
  tests skip cleanly).

## Layer 15 (facade) status

Re-audited against the current tree (post layer-14 CLI + the "Incorporate
growth into fit" / "Rename ffi and pg0 to gpython, copy->clone, write->save"
follow-on commits): see `.claude/migration/FINAL_REPORT.md` for the full
per-layer summary, the benchmark outputs, and the "known gaps" section
(including one CLI import-contract regression discovered while running this
layer's benchmarks — `cli/commands/fit.py` imports `postgkyl.numerics`
directly, a layer-14-scope bug, not fixed here per this layer's Scope).
