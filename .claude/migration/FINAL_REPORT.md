# FINAL_REPORT.md — migration close-out (layer 15-facade)

Written by the layer-15 (facade/docs/benchmarks) implementer. Scope was
docs + facade audit + leftover sweep + end-state benchmarks; no source
files were changed in `api/`, `ops/`, `core/`, `dg/`, `io/`, `numerics/`,
`render/`, `diagnostics/`, `gpython/`, or `cli/` — only `src/postgkyl/__init__.py`
(the facade itself, this layer's own file), `src/postgkyl/io/mapping.py`'s
stale docstring, and the untracked docs (`CLAUDE.md`, `MAPPING.md`,
`.claude/migration/PLAN.md`, `.claude/migration/CHECKPOINTS.md`, this file)
were touched.

**Note on a concurrent process.** While this layer was running, a separate
"layer-14 fixer" pass landed in the same working tree (visible as uncommitted
changes to `src/postgkyl/cli/{_apply.py,commands/{agyro,collect,energetics,
ev,fit,growth,integrate,plot,val2coord}.py}`, `tests/test_cli_{commands,
diagnostics}.py`, and `.claude/migration/reviews/14-cli-review.md`'s new
"Resolutions" section). Those files are outside this layer's scope (rule 1)
and were not touched here; they were only read, to confirm the tree they
left behind is green and to report their outcome accurately below. See
CHECKPOINTS.md's `14-cli` row.

## Per-layer summary

| Layer | Outcome |
|---|---|
| 01-ffi | Audited/tested the pre-existing floor (`ffi/{_lib,array,basis,kernels,rio}.py`, later renamed to `gpython/`). No new features. |
| 02-numerics | Ported `tools/{calculus,mag_sq,rel_change,rotation_matrix,fft,fit,filters}.py` + `ev_ops`/downsample into `numerics/`, pure arrays in/out, 100% coverage. Divergences documented (integrate colon-slice, fft 4-D guard, `init_polar` `&`-precedence bug, `ev_ops` warn→raise). |
| 03-dg | Moved `ffi/rep.py` → `dg/rep.py`; added `dg/map.py` per MAPPING.md; investigated exact modal differentiation and **deferred** it (`notes/differentiate-decision.md`) in favor of a later field-domain `np.gradient` fallback. |
| 04-io | Ported ADIOS/H5/FLASH readers + `mapping.py::c2p_grid` + VTK writer into `io/`. No numerical divergence; typer/ctypes/`norm_axes` drops licensed by doctrine. |
| 05-core | Ported `DatasetGroup` as a verb-less container (`core/group.py`); generalized `flatten_datasets`, incidentally fixing a latent infinite-recursion bug in `src_bak`'s `_flatten`. |
| 06-models | Ported `prim_vars`/`pressure_diagnostics`/`params`/`energetics`/rotation/frame/laguerre math into a (later-deleted) `models/` package; every formula diffed term-by-term vs `src_bak` and matched; two inherited `src_bak` bugs preserved and pinned by tests (`frame.py` c_dim, `laguerre.py` broadcast axis — the `frame.py` one was later fixed at `ce9d0af`). |
| 07-ops-field | Ported the 12 field-domain verbs (`fft`/`magsq`/`relchange`/`mask`/`collect`/`grid`/`val2coord`/`extract_input`/`fit`/`differentiate`/`ev`) onto the new verb contract; numerically identical to `src_bak` except two intentional, documented divergences (`differentiate`'s field-domain fallback per the layer-03 decision; a latent off-by-one grid-prep bug fixed in `fft`). |
| 08-ops-physics | Ported the 7 physics verbs (`moments`/`agyro`/`current`/`energetics`/`rotate`/`transform_frame`/`laguerre` + `map`) as thin wrappers over `models/`; fixer pass fixed a real curvilinear-select axis bug and made `current()` raise instead of silently falling back on inconsistent `qbym` args. |
| 09-render | Ported the full `output/{plot,plotly,pyvista}` feature set (animate, multi-panel, colorbar, styles) into `render/`; fixer pass restored dropped `xscale`/`yscale`/`zscale`. Documented drops: streamline/quiver/contour/lineouts, the `jet` colormap, dual GData/tuple input (`notes/09-render-parity.md`). |
| 10-diagnostics (restructure) | Folded `models/` + the 7 ops physics verbs into `diagnostics/`, one module per equation model; deleted `models/`; moved the field-domain guard to `core/guards.py`. Every moved function diffed line-by-line vs git HEAD (not `src_bak`, since this is a restructure) and numerically identical. |
| 11-api | Added a fluent `GData` method for every `ops` verb; fixed `DatasetGroup.__getattr__` to resolve non-callable member attributes as a plain list. One honest capability regression noted: `DatasetGroup.plot()` is one-figure-per-member vs `src_bak`'s shared overlay, blocked by `ops.plot`'s single-dataset signature. |
| 12-diagnostics-loaders | Ported `loader.py` → `diagnostics/discovery.py`; `loaders/{gk_distf,gk_quantity}.py` + `gk/gk_quantities/*` → `diagnostics/gyrokinetics/`; `loaders/pkpm.py` → `diagnostics/pkpm.py::load_pkpm`. Every `fetch_*` formula independently re-derived algebraically against `src_bak`'s weak-DG-kernel version and matched (modulo the documented, mandated interpolate-first rewiring — `ctypes`/`GkeyllDGops` no longer exists). Fixer pass made `load_gk_distf` keyword-only and removed an unused import. |
| 13-diagnostics-programs | Ported `apps/{gk_energy_balance,gk_particle_balance,gk_nodes,trajectory}.py` + `tools/{calc_enstrophy,calc_ke_dke}.py`. Fixed three inherited `src_bak` bugs (aliased result arrays in enstrophy/ke_dke, an f-string typo, an off-by-one loop) with regression tests. Fixer pass fixed a real, reviewer-found bug (`gk_energy_balance`'s relative-error branch read `has_apar_dot` instead of `has_apar`) and de-duplicated `_read_trace`/`_set_tick_font_size` into `gyrokinetics/utils.py`. Flagged (and separately fixed, outside this layer, at `263d4d0`) a real `io/writer.py` multi-component `asize` bug found while testing. |
| 14-cli | Ported all remaining `commands/*` into thin Click shells under `cli/commands/`; physics commands shell `pg.diagnostics.<module>`. A concurrent fixer pass (landed while this facade layer was running — see the note above) fixed `collect`/`ev`/`val2coord` silently discarding datasets outside their own pool (including `val2coord`'s silent-empty-working-set bug), made `energetics`/`agyro` deactivate every consumed input consistently, deleted dead code (`find_all_by_tag`), and made `plot --figsize` fail closed instead of raising a bare `ValueError`. Two capability swaps (`integrate`, `growth`) were documented rather than restored (restoring them means editing a closed, lower layer, out of a CLI-only fixer's scope). `fit`'s old prefix-matching (`fit lin` → `linear`) was attempted, found to require a facade export, and explicitly deferred to this layer — see "Known gaps" below. |
| 15-facade (this layer) | Facade re-export audit, `CLAUDE.md`/`MAPPING.md`/`PLAN.md`/`io/mapping.py` doc sync, leftover sweep, and the end-state benchmarks below. |

## Facade audit (item 1)

`src/postgkyl/__init__.py` re-exports: `GData`, `load`, `DatasetGroup`,
`animate`, `collect`, `ev`, `relchange` (← `api`); `apply`, `info`,
`integrate`, `interpolate`/`interp`, `represent`, `select`/`sel` (← `ops`,
by design a curated subset — the rest of the equation-blind verb inventory
is reachable via the fluent `GData` methods and `postgkyl.ops.<verb>`, not
promoted to a second top-level name, per the facade's own docstring); `plot`
(← `render`); `save` (← `io`); `load_gk_quantity`, `load_gk_distf`,
`available_gk_quantities` (← `diagnostics.gyrokinetics`). `__version__ =
"0.1.0"` is present and `pyproject.toml`'s `[tool.setuptools.dynamic]`
reads it. `test_facade_is_pure_reexport` passes (no function/class
definitions in `__init__.py`).

Grepped `src/` for `models`/`loaders` as package names: neither exists
anywhere (`models/` was deleted at layer 10; there never was a top-level
`loaders/` package — layer 12 folded equation-internal loading into
`diagnostics/`).

One stale line found and fixed: the facade's own architecture-diagram
docstring said `gpython/    ctypes -> libg0core.so` — inherited from before
the `ffi`→`gpython` rename, and doctrine-incorrect (`gpython/` is a compiled
CPython extension, not a `ctypes` binding; `ctypes` is banned everywhere in
this codebase per rule 2). Fixed to `compiled _gpython extension ->
libg0core.so`.

## Docs sync (item 2)

- **CLAUDE.md** (untracked/gitignored, a living local doc — see "Leftover
  sweep" below): fixed three drifts against the current code — `core/`'s
  bullet list said `push`, `copy` (renamed `clone` at commit `2913718`);
  `api/`'s fluent-method list said `.write()` (renamed `.save()` at the same
  commit); the facade section said `write ← io` (now `save ← io`, and added
  the `load_gk_quantity` family, which the facade re-exports but the prose
  didn't mention). Also updated `io/`'s save-format list (`gkyl`/`txt`/
  `npy`/`vtk` — `vtk` was added by layer 04 but not listed), the
  `diagnostics/` prose section (added `trajectory`/`enstrophy`/`ke_dke` and
  the gyrokinetic `energy_balance`/`particle_balance`/`nodes` programs from
  layer 13, and corrected an inaccurate claim that program diagnostics use
  `render` — none of the six currently do, they build bespoke `matplotlib`
  figures directly, per the 13-review's C5), the `cli/` section (documented
  `format_commands`'s section grouping and the 40+-command inventory added
  by layer 14), and the "Commands" section (refreshed the stale "current
  suite is a single file" claim, added a diagnostics-chain and an
  `ev`-chain example, and `pgkyl --help`/`--version`).
- **MAPPING.md**: the `map` verb's "Where it lives" table is fully
  implemented (`dg/map.py`, `ops/map.py`, `api/gdata.py::map`,
  `render/matplotlib.py`'s mapped-grid support, `ops/select.py`'s
  curvilinear guard, `cli/commands/map.py` all exist and are exercised by
  `tests/test_ops_map.py`/`tests/test_dg_map.py`) — marked every row
  ✅ implemented and closed out the "Testing" section's docs-update bullet.
- **`io/mapping.py`**: its module docstring said the `map` verb was "not yet
  implemented; `ops/map.py` is a later migration layer" — stale since layer
  08 landed it. Fixed to point at `ops/map.py`/`dg/map.py`, and corrected
  the `c2p_grid` docstring (confirmed via grep that nothing outside its own
  tests calls it — `ops/map.py` evaluates DG coefficients directly via
  `dg.map_grid` instead of splitting packed node coordinates).
- **PLAN.md**'s deferred list: all three items checked.
  - `differentiate`'s exact-modal-derivative gap: **resolved** — layer 07
    shipped the field-domain `np.gradient` fallback per the layer-03
    decision doc; the exact route (wrapping the shim's `eval_grad_expand`)
    remains permanently out of scope (requires editing C sources in the
    `gkeyll/` submodule and `gpython/csrc/`).
  - `dg_local_poly`/`dg_avg`/`dg_evproj`: **resolved, never ported** —
    confirmed by `tests/test_cli_commands.py::
    test_config_and_dg_commands_are_not_registered`; superseded by
    `ops.represent`/`ops.apply`.
  - ADIOS reader tests requiring `adios2`: **standing**, not a defect —
    `adios2` is not installed in this environment; those tests skip
    cleanly (see the skip count in every benchmark below).

## Leftover sweep (item 3)

- `git grep -nE "postgkeyll|typer|ctypes" src/` → 3 hits, all inside
  docstrings/comments explaining what was *not* carried forward (the
  facade's own architecture note, now fixed to say "compiled extension";
  `diagnostics/gyrokinetics/quantities.py`'s note about the old
  `ctypes`-based `GkeyllDGops`; `diagnostics/plasma.py`'s note about the old
  `postgkeyll.tools.params`). No live import or executable use of any of
  the three anywhere — same standard every prior layer review (04-io,
  14-cli) applied and passed under.
- `git grep -n "src_bak" src/ tests/` → many hits, all docstrings/comments
  citing the port source (`"Ported from src_bak/postgkyl/..."`) or
  regression-test explanations of a fixed `src_bak` bug — expected and
  required by doctrine 21 ("document divergence"), not a leak of the
  quarry itself (`git status` shows no changes under `src_bak/`).
- `find src/postgkyl -maxdepth 1 -type d -name commands` → empty; the only
  `commands/` directory is `cli/commands/`, as designed.
- `pyproject.toml`'s `[tool.setuptools.package-data]`: `"postgkyl.render" =
  ["*.mplstyle", "*.js"]` (files exist: `render/postgkyl.mplstyle`,
  `render/rotation_controls.js`) and `"postgkyl.gpython" = ["_gpython.so",
  "csrc/*.c"]` (files exist). The old `"postgkyl.output"` key is already
  gone — renamed to `"postgkyl.render"` when layer 09 moved the backend.

## Benchmarks (item 4)

**Full suite** (`PYTHONPATH=src python -m pytest tests/ -q`):

```
1419 passed, 6 skipped in 84.93s (0:01:24)
```

**Coverage** (`PYTHONPATH=src python -m pytest tests/ -q --cov=postgkyl
--cov-report=term-missing` — ran directly in this environment; no
`coverage run` workaround was needed for the whole-package invocation,
though `--cov=postgkyl.cli` alone reproduces the previously-documented
sandbox-wide "cannot load module more than once per process" collection
crash, worked around below by filtering the whole-package report):

```
Name                                                        Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------
src/postgkyl/__init__.py                                        9      0   100%
src/postgkyl/api/__init__.py                                    5      0   100%
src/postgkyl/api/gdata.py                                      63      0   100%
src/postgkyl/api/group.py                                      32      0   100%
src/postgkyl/api/load.py                                        4      0   100%
src/postgkyl/api/verbs.py                                      11      0   100%
src/postgkyl/cli/__init__.py                                    2      0   100%
src/postgkyl/cli/_apply.py                                     32      4    88%   44, 46, 61, 68
src/postgkyl/cli/_options.py                                   12      0   100%
src/postgkyl/cli/_variable.py                                   7      0   100%
src/postgkyl/cli/app.py                                        45      1    98%   62
src/postgkyl/cli/commands/__init__.py                           6      0   100%
src/postgkyl/cli/commands/agyro.py                             19      0   100%
src/postgkyl/cli/commands/animate.py                           22      1    95%   34
src/postgkyl/cli/commands/bparrotate.py                        18      0   100%
src/postgkyl/cli/commands/bperprotate.py                       18      0   100%
src/postgkyl/cli/commands/collect.py                           23      2    91%   33, 35
src/postgkyl/cli/commands/current.py                           28      3    89%   28, 36-37
src/postgkyl/cli/commands/differentiate.py                     12      0   100%
src/postgkyl/cli/commands/energetics.py                        23      0   100%
src/postgkyl/cli/commands/euler.py                             18      0   100%
src/postgkyl/cli/commands/ev.py                                21      2    90%   35-36
src/postgkyl/cli/commands/extractinput.py                      14      1    93%   18
src/postgkyl/cli/commands/fft.py                               13      0   100%
src/postgkyl/cli/commands/fit.py                               37      2    95%   65, 67
src/postgkyl/cli/commands/gk_distf.py                          27      0   100%
src/postgkyl/cli/commands/gk_load_quantity.py                  22      0   100%
src/postgkyl/cli/commands/gkyl_pkpm.py                         15      0   100%
src/postgkyl/cli/commands/grid.py                              12      0   100%
src/postgkyl/cli/commands/growth.py                            30      4    87%   39, 41, 47-48
src/postgkyl/cli/commands/info.py                               8      0   100%
src/postgkyl/cli/commands/integrate.py                         19      1    95%   39
src/postgkyl/cli/commands/interpolate.py                       10      0   100%
src/postgkyl/cli/commands/laguerre_compose.py                  17      0   100%
src/postgkyl/cli/commands/listoutputs.py                       14      0   100%
src/postgkyl/cli/commands/load.py                              12      0   100%
src/postgkyl/cli/commands/magsq.py                             12      0   100%
src/postgkyl/cli/commands/map.py                               13      1    92%   26
src/postgkyl/cli/commands/mask.py                              16      0   100%
src/postgkyl/cli/commands/mhd.py                               18      0   100%
src/postgkyl/cli/commands/parrotate.py                         19      0   100%
src/postgkyl/cli/commands/perprotate.py                        19      0   100%
src/postgkyl/cli/commands/plot.py                              43      0   100%
src/postgkyl/cli/commands/plotly.py                            44      5    89%   44, 55, 62-65
src/postgkyl/cli/commands/plotly_animate.py                    25      4    84%   29, 34, 38-39
src/postgkyl/cli/commands/print.py                             19      1    95%   23
src/postgkyl/cli/commands/pyvista.py                           32      3    91%   40, 42, 47
src/postgkyl/cli/commands/relchange.py                         20      1    95%   28
src/postgkyl/cli/commands/save.py                              11      0   100%
src/postgkyl/cli/commands/select.py                            14      0   100%
src/postgkyl/cli/commands/status.py                            19      0   100%
src/postgkyl/cli/commands/style.py                             18      1    94%   23
src/postgkyl/cli/commands/tenmoment.py                         17      0   100%
src/postgkyl/cli/commands/transform_frame.py                   18      0   100%
src/postgkyl/cli/commands/val2coord.py                         23      0   100%
src/postgkyl/cli/commands/velocity.py                          18      0   100%
src/postgkyl/cli/state.py                                      10      0   100%
src/postgkyl/core/__init__.py                                   4      0   100%
src/postgkyl/core/collection.py                                13      0   100%
src/postgkyl/core/group.py                                     25      0   100%
src/postgkyl/core/guards.py                                     5      0   100%
src/postgkyl/core/state.py                                    202      0   100%
src/postgkyl/dg/__init__.py                                     4      0   100%
src/postgkyl/dg/interp.py                                      39      0   100%
src/postgkyl/dg/map.py                                         43      0   100%
src/postgkyl/dg/modal.py                                       32      0   100%
src/postgkyl/dg/rep.py                                         84      0   100%
src/postgkyl/diagnostics/__init__.py                            2      0   100%
src/postgkyl/diagnostics/discovery.py                          27      0   100%
src/postgkyl/diagnostics/enstrophy.py                          45      0   100%
src/postgkyl/diagnostics/five_moment.py                       116      0   100%
src/postgkyl/diagnostics/gyrokinetics/__init__.py               9      0   100%
src/postgkyl/diagnostics/gyrokinetics/distf.py                 69      7    90%   166-167, 170-171, 173-174, 177
src/postgkyl/diagnostics/gyrokinetics/energy_balance.py       174      1    99%   373
src/postgkyl/diagnostics/gyrokinetics/load_quantity.py         29      0   100%
src/postgkyl/diagnostics/gyrokinetics/nodes.py                113     15    87%   221-241, 266
src/postgkyl/diagnostics/gyrokinetics/particle_balance.py     124      3    98%   256, 266, 269
src/postgkyl/diagnostics/gyrokinetics/quantities.py           159      0   100%
src/postgkyl/diagnostics/gyrokinetics/quantity.py             115      0   100%
src/postgkyl/diagnostics/gyrokinetics/registry.py              52      0   100%
src/postgkyl/diagnostics/gyrokinetics/utils.py                 69      0   100%
src/postgkyl/diagnostics/ke_dke.py                             32      0   100%
src/postgkyl/diagnostics/kinetic.py                            46      0   100%
src/postgkyl/diagnostics/mhd.py                                79      0   100%
src/postgkyl/diagnostics/multispecies.py                       41      0   100%
src/postgkyl/diagnostics/pkpm.py                               43      0   100%
src/postgkyl/diagnostics/plasma.py                             95      0   100%
src/postgkyl/diagnostics/rotations.py                          26      0   100%
src/postgkyl/diagnostics/ten_moment.py                        178      0   100%
src/postgkyl/diagnostics/trajectory.py                         58      0   100%
src/postgkyl/gpython/__init__.py                                4      0   100%
src/postgkyl/gpython/_lib.py                                   18      0   100%
src/postgkyl/gpython/array.py                                  36      0   100%
src/postgkyl/gpython/basis.py                                 104      0   100%
src/postgkyl/gpython/kernels.py                               128      0   100%
src/postgkyl/gpython/rio.py                                    36      0   100%
src/postgkyl/io/__init__.py                                    19      0   100%
src/postgkyl/io/flash_h5_reader.py                             54      0   100%
src/postgkyl/io/gkyl_adios_reader.py                          161      0   100%
src/postgkyl/io/gkyl_c_reader.py                               40      0   100%
src/postgkyl/io/gkyl_h5_reader.py                              53      0   100%
src/postgkyl/io/gkyl_reader.py                                249      0   100%
src/postgkyl/io/mapping.py                                     19      0   100%
src/postgkyl/io/writer.py                                     133      0   100%
src/postgkyl/numerics/__init__.py                              13      0   100%
src/postgkyl/numerics/calculus.py                              37      0   100%
src/postgkyl/numerics/downsample.py                            27      0   100%
src/postgkyl/numerics/elementwise.py                           10      0   100%
src/postgkyl/numerics/ev_ops.py                               227      0   100%
src/postgkyl/numerics/fft.py                                  119      0   100%
src/postgkyl/numerics/filters.py                               22      0   100%
src/postgkyl/numerics/fit.py                                  198      0   100%
src/postgkyl/numerics/grid_centering.py                        24      0   100%
src/postgkyl/numerics/idx_parser.py                            43      0   100%
src/postgkyl/numerics/mag_sq.py                                 7      0   100%
src/postgkyl/numerics/rel_change.py                             8      0   100%
src/postgkyl/numerics/rotation_matrix.py                       16      0   100%
src/postgkyl/ops/__init__.py                                   21      0   100%
src/postgkyl/ops/_materialize.py                               11      0   100%
src/postgkyl/ops/animate.py                                    11      0   100%
src/postgkyl/ops/arithmetic.py                                126      0   100%
src/postgkyl/ops/collect.py                                    30      0   100%
src/postgkyl/ops/differentiate.py                              12      0   100%
src/postgkyl/ops/ev.py                                        102      0   100%
src/postgkyl/ops/extract_input.py                               8      0   100%
src/postgkyl/ops/fft.py                                        12      0   100%
src/postgkyl/ops/fit.py                                        46      0   100%
src/postgkyl/ops/grid.py                                       22      0   100%
src/postgkyl/ops/info.py                                        5      0   100%
src/postgkyl/ops/integrate.py                                  16      0   100%
src/postgkyl/ops/interpolate.py                                20      0   100%
src/postgkyl/ops/magsq.py                                       8      0   100%
src/postgkyl/ops/map.py                                        33      0   100%
src/postgkyl/ops/mask.py                                       19      0   100%
src/postgkyl/ops/plot.py                                        6      0   100%
src/postgkyl/ops/relchange.py                                  11      0   100%
src/postgkyl/ops/represent.py                                  40      0   100%
src/postgkyl/ops/select.py                                     42      0   100%
src/postgkyl/ops/val2coord.py                                  38      0   100%
src/postgkyl/render/__init__.py                                 5      0   100%
src/postgkyl/render/_prep.py                                   68      0   100%
src/postgkyl/render/animate.py                                102      0   100%
src/postgkyl/render/labels.py                                  25      0   100%
src/postgkyl/render/matplotlib.py                              77      0   100%
src/postgkyl/render/plotly.py                                 332      0   100%
src/postgkyl/render/pyvista.py                                116      0   100%
src/postgkyl/render/style.py                                   11      0   100%
-----------------------------------------------------------------------------------------
TOTAL                                                        6440     63    99%
1419 passed, 6 skipped, 4 warnings in 101.54s (0:01:41)
```

**99% overall — comfortably above the ≥85% floor.** Per-package rollups
(computed from the table above): `cli` 96.2% (984/37 miss), `diagnostics`
98.5% (1701/26 miss), everything else (`api`/`core`/`dg`/`gpython`/`io`/
`numerics`/`ops`/`render`) 100%. Every non-100% miss was already reviewed
and justified line-by-line in the 12/13/14-layer review docs (interactive
`plt.show()`/`fig.show()` branches; `_apply.py`'s tag-mismatch pass-through
and `find_by_tag`'s not-found raise; the `gk_nodes` `psi_file` overlay,
which needs a component-selecting fixture the repo doesn't ship; the
`mc2nu`/`mapc2p` coordinate-map branches in `gk_distf`, which need a
fixture with `basis_type`/`poly_order` metadata the repo doesn't ship).

**Fresh-install check:**

```
$ pip install -e '.[test]'
...
Successfully installed postgkyl-0.1.0

$ pgkyl --version
pgkyl, version 0.1.0

$ pgkyl --help
Usage: pgkyl [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...
  Postprocessing and plotting tool for Gkeyll data.
Options:
  --version ...
Verbs: fft, magsq, relchange, mask, collect, grid, val2coord, extractinput,
  fit, growth, differentiate, ev, map, integrate, animate, interpolate,
  select, save
Diagnostics: euler, tenmoment, mhd, velocity, agyro, current, energetics,
  parrotate, perprotate, bparrotate, bperprotate, transform_frame,
  laguerre_compose
Render: plot, plotly, plotly_animate, pyvista, style
Loaders: load, gk_distf, gk_load_quantity, gkyl_pkpm
Utility: info, print, listoutputs, status

$ unset PYTHONPATH && python -m pytest tests/ -q
1419 passed, 6 skipped, 4 warnings in 85.86s (0:01:25)
```

Packaging is intact: the editable install succeeds, the console script
resolves, `--version`/`--help` work, and the full suite passes against the
**installed** package (no `PYTHONPATH` needed).

**Golden chains (fluent), all verified live in this session:**

```python
import postgkyl as pg
d = pg.load("tests/test_data/rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl").interp().sel(z0=0)
d.plot()                                    # -> matplotlib Figure, OK
```

Modal-domain chain (`a*b/b == a`, `.integrate()`) — built two synthetic
`serendipity p1` fields (shifted away from zero, matching
`tests/test_gpython_kernels.py`'s `_smooth_field` convention, since the
shipped `gkhybrid` gyrokinetic fixture doesn't support weak ops — Gkeyll's
weak-DG kernels are only implemented for `serendipity`/`tensor`, a
long-standing, documented limitation, not a gap in this layer):

```
a*b/b == a: True
.integrate(): 2.1064557751600224
```

Generated-data chain per dimension (1-D/2-D/3-D, `serendipity p1`,
synthetic modal coefficients):

```
1D generated-data chain OK: Figure   (matplotlib, via .interp().plot())
2D generated-data chain OK: Figure   (matplotlib, via .interp().plot())
3D interp shape: (6, 8, 10, 1)
3D generated-data chain (via sel to 2D) OK: Figure   (matplotlib needs a
    2D slice for 3D data, by design -- "use plotly()/pyvista() for 3D")
3D via pyvista OK: NoneType   (render.pyvista(d, show=False) succeeds
    off-screen; returns None when not asked to return a figure handle)
```

**Golden chains (CLI), all verified live in this session:**

```
$ pgkyl --batch-mode tests/test_data/rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl interp sel --z0 0 plot
  -> writes pgkyl.png                                              OK
$ pgkyl tests/test_data/rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl interp sel --z0 0 plot --save out.png
  -> writes out.png                                                OK
$ pgkyl tests/test_data/rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl info
  -> prints time/frame/dims/grid/DG-basis summary                  OK
$ pgkyl <synthetic 5-moment .gkyl> interp euler --variable-name density print
  -> prints one density value per cell                             OK
$ pgkyl <file> <file> interp ev "f0 f1 +" print
  -> prints the summed field                                       OK
```

(The moments/ev chains needed a hand-built synthetic `.gkyl` file — none of
the checked-in fixtures carry an exact 5- or 10-component conserved-moment
vector with `basis_type`/`poly_order` metadata; this is a fixture-staging
gap, not a code defect, matching the same "no such fixture is shipped"
disposition the 12/13-layer reviews already recorded for other coverage
gaps.)

**Wall-clock:** full suite 84.93s. Two tests exceed 30 s:
`tests/test_cli_commands.py::TestFitAndGrowth::test_fit_window_flag_precedes_argument`
(31.64s) and `::test_growth_rate` (31.39s). Root cause traced to
`numerics/fit.py::fit_best_window`, which does an exhaustive search over
every window length from `min_n` to `len(xdata)` (the `ENERGY` fixture,
`twostream-field-energy.bp`, has 15714 time samples), calling
`scipy.optimize.curve_fit` once per candidate window — an O(N) sequence of
nonlinear fits. This is the ported `src_bak` growth-rate algorithm's own
design (not a regression introduced by this or any other migration layer);
fixing it would mean changing `numerics/fit.py`'s algorithm, which belongs
to layer 07/08, out of this layer's scope. Recorded here as a benchmark
finding for a future performance-focused layer, not fixed.

## Known gaps (for a future contributor)

1. **`fit`'s CLI prefix-matching (`fit lin` → `linear`) is not restored**
   (14-cli-review C4). The old CLI resolved an unambiguous prefix of a fit
   model name; the new one requires the model name in full. Restoring it
   needs `cli/commands/fit.py` to read `numerics.FIT_FUNCTIONS`'s key list,
   but `cli` may only depend on the facade (`_ALLOWED["cli"] == {""}`), and
   the facade currently exports no math/vocabulary tables (only datasets/
   verbs/loaders). Two ways to close this, neither taken here (this layer's
   own audit deliberately kept the facade's existing, minimal shape rather
   than expanding it on a single CLI command's behalf):
   - Add a facade export for the fit-model vocabulary (parallel to how
     `pg.diagnostics.<module>.VARIABLES` already works for
     `euler`/`tenmoment`/`mhd`) and have `fit.py` use `import postgkyl as
     pg; pg.numerics.FIT_FUNCTIONS` — note `pg.numerics` is *already*
     reachable this way at runtime (confirmed: `ops/fit.py`'s legitimate
     `from postgkyl import numerics` import populates the attribute on the
     `postgkyl` module object as a side effect), so the fix may be as small
     as changing `cli/commands/fit.py`'s import statement from `from
     postgkyl import numerics` (which the AST-based `test_import_contract_
     no_violations` correctly flags as a direct `cli -> numerics` edge) to
     `import postgkyl as pg` + `pg.numerics.FIT_FUNCTIONS` (an attribute
     access the AST checker does not — and structurally cannot — see,
     exactly like every `pg.diagnostics.*`/`pg.render.*` reference already
     in `cli/commands/`). Whether that attribute-traversal pattern is a
     sanctioned exception or a blind spot in the architecture test is a
     design question for whoever picks this up, not a call this report
     makes unilaterally.
   - Or accept the current documented drop permanently (the CLI's own
     docstring now names it explicitly, and a regression test pins the
     exact-match-only behavior so it fails closed instead of silently
     drifting).
2. **`fit_best_window`'s O(N) window search is slow on long time series**
   (see Wall-clock above) — a real, pre-existing performance characteristic
   of the ported growth-rate algorithm, not a correctness bug. A future
   layer could binary-search or early-terminate on R² plateau instead of
   scanning every window length.
3. **`gk_distf`'s coordinate-mapping branches (`use_mc2nu`/`use_mapc2p`)
   remain untested end-to-end** (12-review C4) — the shipped
   `rt_gk_tcv_iwl_1x2v_p1` fixture's `mapc2p_vel`/`jacobvel` files carry no
   `basis_type`/`poly_order` metadata, so `ops.map` (itself fully tested
   elsewhere) can't be exercised through this call site without a new
   fixture generated by real Gkeyll.
4. **`gk_nodes`'s `psi_file` overlay branch is untested** (13-review) — the
   one shipped p2-tensor 2-D fixture is 9-component and `gk_nodes` (both
   old and new) feeds the whole array to `pcolormesh`/`contour` without a
   component selector.
5. **Exact modal differentiation remains unimplemented** (layer 03's
   decision, reaffirmed by PLAN.md's deferred-items update above) — would
   require wrapping the shim's `eval_grad_expand` as a new
   `pg0_basis_eval_grad`, editing C sources in the `gkeyll/` submodule and
   `gpython/csrc/`, out of every Python-only layer's scope.
6. **`DatasetGroup.plot()` is one-figure-per-member**, not `src_bak`'s
   shared overlay (11-api review) — blocked by `ops.plot`'s single-dataset
   signature; extending it to accept a `DatasetGroup` and produce one
   overlaid figure is a real, scoped follow-up for whoever owns `ops`/
   `render` next.
7. **The layer-14 fixer's changes are uncommitted** as of this report (see
   the note at the top and the CHECKPOINTS.md `14-cli` row) — the
   orchestrator should commit that fixer pass (and this layer's doc-sync
   commit) before considering the migration closed. This report does not
   commit anything itself, per this layer's rules.

## Definition of done — self-check

- Full suite green: ✅ (1419 passed, 6 skipped, 0 failed).
- Coverage ≥85% overall: ✅ (99%).
- Fresh install + `pgkyl --version`/`--help` + `pytest` without
  `PYTHONPATH`: ✅.
- Golden chains (fluent + CLI): ✅, all re-verified live this session.
- Wall-clock flagged: ✅ (two tests just over 30 s, root-caused, not fixed
  — pre-existing algorithmic cost, out of this layer's scope).
- CHECKPOINTS.md has a row for every layer: ✅ (this report added rows for
  12/13/14/15).
- "The tree is committed layer-by-layer with clean messages": **not done
  by this layer** — per this layer's explicit rule ("Do not commit"),
  committing is left to the orchestrator. The working tree is green and
  ready to commit as of this report.
