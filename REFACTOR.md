# Postgkyl Refactor — Finishing the `ops/` Migration

> **Status.** The big refactor (the `ops/` seam, fluent `GData`, `DatasetGroup`, `pg.load`)
> already landed — 768 tests, 26 verbs ported. The remaining debt is concentrated in four
> places: `commands/load.py`, the coordinate-mapping logic, the `gk_*` mini-applications,
> and leftover dead code. `commands/` is still ~6,000 lines across 54 files while `ops/` is
> ~1,600 across 23 — that asymmetry is where the work is.
>
> A companion document, `src/postgkyl/README.md`, describes the **current** folder layout
> and layering. This file describes the **target** and the steps to get there.

---

## Architecture recap

Postgkyl is one library with two front-ends, layered so each layer depends only on those
above it:

```
L0  tools/      pure NumPy functions, no GData            (numerics)
L1  data/       GData master class + readers + DG interp  (I/O & storage)
    modalDG/    generated DG kernel tables
L2  ops/        one function per verb                     ← the single seam
    output/     rendering backends
    utils/      shared, cross-cutting helpers
L3  GData / DatasetGroup / loader / group   fluent script API
L4  apps/       composed diagnostics & workflows          (script-callable)
L5  commands/   Click CLI shells                          (thin: argv → ops / apps)
```

Guiding rule for every change below: **`commands/` should hold no numerics and no
file-naming/grid logic** — only argv translation. `ops/` is the single source of truth;
`tools/` is the bottom of the stack and depends on nothing in Postgkyl.

---

## 1. Refactor the mapping out of `load`

### Problem
The c2p coordinate mapping is split across two places, and both are awkward:

- **Which mapping file to use** is resolved in `commands/load.py` by ~50 lines of
  copy-pasted global-vs-local `if/elif/elif` chains (one block each for `c2p`, `c2p_vel`,
  `varname`, plus the six `z` cuts via `_pick_cut`). This is pure CLI option plumbing living
  inside a "command."
- **What the mapping does** (build the grid from a separate mapc2p file) is embedded
  directly in `gkyl_reader.load()` as three inline branches — `c2p` / `c2p_vel` / uniform
  (`gkyl_reader.py:495-548`) — and duplicated in `gkyl_adios_reader.py`.

### Proposal
- **`data/map.py` (new).** A small `GridMap` value object
  (`mapc2p_name`, `mapc2p_vel_name`, `comp_grid`) and a single
  `build_grid(reader_ctx, mapping) -> grid` function. Both readers call it instead of
  carrying their own c2p branches. "uniform vs c2p vs c2p_vel" becomes one tested function,
  not three copies. The reader stops knowing about mapping precedence.
- **`commands/_load_opts.py` (new).** Pull the global-vs-local resolution out of `load.py`
  into `resolve_load_options(ctx, kwargs) -> LoadOptions` (a dataclass). The `_pick_cut`
  pattern collapses to one loop over a field list. `load.py` drops from 155 lines to a thin
  shell matching every other command.

### Result
The reader no longer knows CLI precedence rules; `load.py` no longer knows grid
construction. Both pieces become independently testable.

---

## 2. Relocate the commands that don't fit the `ops/` shape

Three distinct kinds are currently lumped into `commands/`:

### 2a. Loader-workflows → the `pg.load` namespace
`gk_distf`, `gkyl_pkpm` (`pkpm`), `gk_load_quantity` *load by naming convention +
interpolate/transform + return ready data*. They belong on the loader, exactly as
`gk_distf` already does (`pg.load.gk_distf(...)`).

- Add `pg.load.pkpm(...)` and `pg.load.gk_quantity(...)` to `loader.py`.
- The Click commands become thin shells over those loader methods.
- This naturally relocates the gyrokinetics domain knowledge currently buried in `utils/`
  (`utils/gk_quantities/`, `utils/gk_utils.py`) into a coherent **`gk/` subpackage**.

### 2b. Mini-applications → a new `apps/` package
`gk_energy_balance`, `gk_particle_balance`, `gk_nodes`, `trajectory` load many files,
compute, and render a complete figure. They are programs, not pipeline verbs.

- Move them to `apps/`, each split into a **script-callable compute/plot function**
  plus a **thin Click shell**.
- Benefit: they become usable from scripts (today they are CLI-only), and ~1,400 lines of
  file-globbing + plotting leave `commands/`.

### 2c. The one genuine unported verb → `ops/`
`dg_local_poly` *is* a `verb(data) -> data` transform (it rewrites DG modal coefficients
into a cellwise polynomial representation with NaNs at interfaces).

- Move it to **`ops/dg_local_poly.py`** + a `GData.dg_local_poly()` method.
- The command thins to `apply(ctx, ops.dg_local_poly, ...)`.

---

## 3. Broader modernization

- **Delete dead code.** `commands/temp.py` (imported in `commands/__init__.py` but never
  registered in `pgkyl.py`), `commands/old/`, `data/old/`. Remove the stray `temp` import.
- **Decide `ev`'s home.** The 441-line RPN registry in `commands/ev_cmd.py` is the last big
  chunk of numerics under `commands/`. Move the registry into `ops/ev.py` so
  `commands/` holds no numerics.
- **Split `utils/`.** It is a grab-bag. Separate plotting/IO support
  (`axis_and_grid_prep`, `load_plot_data`, `downsample`, `latex_conversion`, `load_style`)
  from gkeyll-domain knowledge (`gkeyll_const`, `gkeyll_enums`, `gk_*`, `gk_quantities/`).
  The latter pairs with the `gk/` cluster from §2a.
- **Tidy the repo root.** `API_REDESIGN.md`, `REFACTOR_PLAN.md`, `RESEDIGN_NOTES.md` are
  design history — move to `docs/design/`. The user-facing root `README.md` still says
  "does not work with NumPy >= 2.0," which contradicts the current `numpy>=2.2.6` pin in
  `pyproject.toml` — fix that line.

---

## Target layout (after this refactor)

```
src/postgkyl/
  tools/          pure NumPy numerics (+ ev RPN registry)
  data/           GData, readers, dg.py, select/write, mapping.py (NEW)
  ops/            verb library (+ dg_local_poly)              [L2]
  output/         matplotlib / plotly / pyvista backends      [L2]
  utils/          generic plotting/IO support only            [L2]
  gk/             gyrokinetics domain reference: constants, enums, quantity registry  (NEW) [L2]
  apps/           mini-applications: energy/particle balance, nodes, trajectory  (NEW) [L4]
  commands/       thin Click shells + DataSpace + CLI-state cmds + _load_opts.py (NEW) [L5]
  modalDG/        generated DG kernels                         [L1]
  __init__.py loader.py group.py pgkyl.py _gkylsoft_path.py    [L3]
```

`apps/` is the layer the codebase currently lacks: it sits **between** the script API (L3)
and the CLI (L5). The mini-applications move there as plain, importable functions
(`pg.apps.energy_balance(...)`), so they become script-callable instead of CLI-only, and the
Click commands shrink to thin shells that call them.

---

## Suggested order (each step its own commit, suite kept green)

1. **Delete dead code** (`temp.py`, `commands/old/`, `data/old/`). Zero-risk, shrinks scope.
2. **Port `dg_local_poly` into `ops/`** + fluent method + thin command. Establishes the
   pattern with a small, well-bounded verb.
3. **Extract `data/mapping.py`** and thin the readers; then **`commands/_load_opts.py`** and
   thin `load.py`. The highest-value structural win.
4. **Loader-workflows** (`pkpm`, `gk_load_quantity`) onto `pg.load`; thin their commands.
5. **`gk/` subpackage**: move `utils/gk_quantities/` + `utils/gk_utils.py`; repoint imports.
6. **`diagnostics/` package**: move the four mini-applications, splitting compute from CLI.
7. **`ev` registry** to `tools/`; **split `utils/`**; **move design docs**; **fix the
   NumPy line** in the root README.

Steps 1–3 are the recommended first slice: lowest risk, highest structural payoff.
