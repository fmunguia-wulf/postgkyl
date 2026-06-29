# Postgkyl source layout

Postgkyl is **one library, two front-ends**: a Python script API (`import postgkyl as pg`)
and a CLI (`pgkyl`). Both drive the *same* verb implementations so they cannot drift.

This document is the **idealized layering** — the gold standard the codebase organizes
toward. Each layer may depend only on the layers above it (lower numbers); nothing ever
reaches downward. `REFACTOR.md` tracks where the current tree still deviates and how it
migrates here.

```
L0  tools/      pure NumPy functions, no GData            (numerics)
L1  data/       GData master class + readers + DG interp  (I/O & storage)
    modalDG/    generated DG kernel tables
L2  ops/        one function per verb                     ← the single seam
    output/     rendering backends
    utils/      generic, cross-cutting support
    gk/         gyrokinetics domain reference             (constants, enums, quantity registry)
L3  GData / DatasetGroup / loader / group                 fluent script API
    loaders/    data-returning compositions               (loader-workflows)
L4  apps/       figure/analysis-returning compositions    (composed diagnostics)
L5  commands/   Click CLI shells                          (thin: argv → ops / loaders / apps)
```

The two front-ends enter at different heights, and that is the whole point of the ordering:

- **The script API is L3.** A user writing Python composes verbs directly:
  `pg.load('f.gkyl').interp().sel(z0=0.0).plot()`.
- **Apps (L4) are built _on_ the script API**, not beside it. An app is a normal Python
  function that orchestrates several L0–L3 calls into a higher-level diagnostic or workflow
  — and is therefore itself callable from a script.
- **The CLI (L5) is the topmost, thinnest layer.** A command translates `argv` into one
  `ops` verb (most commands) or one `apps` function (the mini-applications). Nothing in the
  library imports `commands/`.

---

## L0 — `tools/`, pure numerics

Stateless NumPy functions that operate on plain arrays and know **nothing** about `GData`,
files, or plotting (`calculus.py`, `fft.py`, `prim_vars.py`, `pressure_diagnostics.py`,
`rotation_matrix.py`, `energetics.py`, …). This is the bottom of the stack: everything else
may call `tools/`, but `tools/` calls nothing in Postgkyl. Add a new numerical kernel here
and wrap it with an `ops/` verb.

---

## L1 — I/O & storage

### `data/` — the core data layer
Owns reading files and holding the result.
- **`gdata.py`** — `GData`, the **master class**: a single dataset (a grid = list of 1-D
  arrays, plus an (N+1)-D values array) with all metadata in `ctx`. It is the fluent
  subject of every verb (1-line methods delegating to `ops/`), and provides the
  Python-native surface (`__repr__`, arithmetic dunders, `__array__`/`__array_ufunc__`),
  the `_result(...)` helper (the one place that decides "mutate in place" vs "emit a new
  tagged `GData`"), and `.copy()`.
- **Readers** — `gkyl_reader.py` (`.gkyl` binary, 3 sub-types), `gkyl_adios_reader.py`
  (`.bp`, optional `adios2`), `gkyl_h5_reader.py` / `flash_h5_reader.py` (`.h5`). The
  constructor auto-selects one by extension.
- **`dg.py`** — `GInterpModal` / `GInterpNodal`, DG-coefficient → nodal-value interpolation;
  auto-detects `poly_order`/`basis_type` from `ctx`.
- **`mapping.py`** — coordinate-mapping (`c2p` / `c2p_vel` / uniform) grid construction,
  called by the readers so the "which grid" decision lives in one tested place.
- **`select.py`**, **`write.py`** — array slicing and on-disk output primitives.
- **`compute*Matrices.py`** — precomputed interpolation/derivative matrices used by `dg.py`.

### `modalDG/` — generated DG kernels
`kernels/expand[1-6]d.py` — auto-generated per-dimension modal-DG basis expansion tables,
plus `interpolate.py`. Treat as generated data, not hand-edited source. Used by `data/dg.py`.

---

## L2 — verbs, rendering, and shared helpers

### `ops/` — the verb library (single source of truth)
One module per verb, re-exported from `ops/__init__.py`. Every verb obeys one contract:

```python
op(data: GData, *, ..., inplace=False, tag=None, label=None) -> GData
```

Returns a new `GData` by default; `inplace=True` mutates the input (for large data).
Results always flow through `GData._result`. **Verbs wrap; they never reimplement** — they
call `tools/`, `data/`, and `output/`. The fluent `GData` method, the `DatasetGroup`
method, and the CLI command for a verb all call the same `ops` function. To add a verb:
implement it here once, add a 1-line `GData` method (broadcast over groups comes free), and
add a thin CLI shell.

### `output/` — rendering backends
Terminal/visual layer. `plot.py` (matplotlib) also hosts **`plot_datasets(list, **kw)`** and
`animate(...)`, the multi-dataset figure/subplot/legend/global-range loop shared by both
`pg.plot` and the CLI `plot` command. `plotly.py` (interactive 3D) and `pyvista.py`
(scientific 3D) are the other backends.

### `utils/` — shared, cross-cutting helpers
Pure support code consumed across layers, no `GData` orchestration of its own:
- **Plotting/IO support** used by `output/` and commands: `axis_and_grid_prep.py`,
  `load_plot_data.py`, `downsample.py`, `latex_conversion.py`, `load_style.py`,
  `verb_print.py`, `nodal_to_cell_centered_grid.py`, `input_parser.py`, `set_frame.py`.
- **Gkeyll/gyrokinetics domain reference** (`gk/`: the `gk_quantities/` registry of ~50
  pre-named GK quantities, `gkeyll_const.py`, `gkeyll_enums.py`, `gk_utils.py`). This is
  reference data — naming conventions and physical constants — *consulted* by L3 loaders and
  L4 apps. It imports from `data/` only and **never orchestrates `ops`**; the gyrokinetic
  *workflows* that do (build a distribution function, compose a named quantity) are
  compositions and live in L3 `loaders/`, not here.

---

## L3 — fluent script API

The Python-facing surface, built directly on `ops/`. These are top-level modules rather than
a folder:
- **`__init__.py`** — the package surface: re-exports `GData`, `GInterp*`, `DatasetGroup`,
  `load`, the L4 `apps` namespace, and the varargs helpers `pg.plot` / `pg.animate` /
  `pg.info` / `pg.pr`.
- **`GData`** (defined in `data/gdata.py`) is the per-dataset half of this layer: its fluent
  methods are 1-line delegations to `ops/`.
- **`group.py`** — `DatasetGroup`: an ordered set of `GData`; non-terminal verbs broadcast,
  terminal verbs (`plot`, `animate`, `collect`, …) act on all members. Backs `.with_()`/`&`.
- **`loader.py`** — `pg.load`: a callable singleton and the public *face* of every
  *loader-workflow* (read-by-naming-convention → interpolate/transform → return ready data):
  `pg.load(...)`, `.many()`, `.gk_distf()`, `.pkpm()`, `.gk_quantity()`, `.outputs()`. The
  bare-file readers (`__call__`, `many`) live here; the multi-file workflow *bodies* are thin
  delegations down into `loaders/`.
- **`loaders/`** — the implementation home for loader-workflows: `gk_distf.py`, `pkpm.py`,
  `gk_quantity.py`. Each loads files by Gkeyll's naming conventions, runs them through `ops`
  verbs, and returns a ready `GData`/`DatasetGroup`. Because they *compose* `ops` (rather
  than merely being consulted like the `gk/` reference data), they sit at L3, above the verb
  seam — which is why a loader importing `ops` is ordinary, not a smell. Both front-ends point
  *down* here: `pg.load.<workflow>` (script) and the matching CLI command each delegate to one
  `loaders/` function. They are the data-returning sibling of L4 `apps/` (figure-returning).
- **`_gkylsoft_path.py`** — locates the `gkylsoft` installation.

---

## L4 — `apps/`, composed diagnostics

Higher-level programs assembled **from** the script API. An app loads (often many) files,
computes, and produces a finished diagnostic — typically a figure or an analysis result.
Each app is a plain, importable function (e.g. `pg.apps.energy_balance(...)`), so the same
code that powers a CLI command is usable in a script or notebook.

The rule that keeps this layer honest: an app may call L0–L3 freely but **must not** import
`commands/`, and its compute logic is kept separate from any CLI/argv glue. Today's
mini-applications belong here: `energy_balance`, `particle_balance`, `nodes`, `trajectory`.

`apps/` and L3 `loaders/` are the two composition layers above the verb primitives, split by
**what they return**: a loader-workflow returns ready `GData` for further composition, so it
sits at L3 where the script API can chain off it; an app returns a finished figure/analysis,
the end of the pipeline, so it sits at L4. Both were once trapped inside `commands/` as
CLI-only code — `apps/` rescued the figure-returning half, `loaders/` the data-returning
half. Giving each its own layer between the script API and the CLI is what makes them
reusable from a script or notebook.

---

## L5 — `commands/`, the CLI

The topmost, thinnest layer. Click chained-command shells
(`pgkyl file.gkyl interp sel --z0 0 plot`); each command translates `argv` into exactly one
L2 verb or one L4 app. Most are ~3-line shells calling an `ops` verb through **`_apply.py`**
(the tag-or-overwrite middleware). Also here:
- **`data_space.py`** — `DataSpace`, the CLI's tagged dataset stack and iterators.
- **CLI-only state commands** — `status.py` (`activate`/`deactivate`), `style.py`
  (matplotlib rcParams), `config.py` (one-time `gkylsoft` path), `load.py` (the CLI loader;
  `pg.load` is the script equivalent). These manage REPL/figure state, not numerics, so they
  have no `ops` verb.
- **`ev.py`** — the CLI shell for the RPN expression evaluator (`pgkyl ... ev 'f g -'`).
  It keeps only the DataSpace-specific token resolution (tag selection, push-back); the
  numeric operator registry lives in `tools/ev_ops.py` (L0) and the stack machine plus the
  script-facing `ev()` live in `ops/ev.py` (L2).

The CLI entry point itself is **`pgkyl.py`**: `PgkylCommandGroup` (chaining, command
abbreviation, aliases, bare-filename-as-`load`) and all `cli.add_command(...)` wiring.