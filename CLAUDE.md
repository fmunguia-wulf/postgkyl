# Coding Doctrine

**0. Locality of reasoning.** Every principle below is a projection of
one axiom: a reader must be able to understand a fragment without the
whole program. Whatever keeps a local conclusion sound — a frozen
record, an honest signature, a stated law — is doctrine. Whatever
forces a global search — ambient state, a leaky layer, a second copy
of a fact — is the enemy.

*Data — what it does, and what it may say*

**I. Data is inert. Functions transform.** No objects that know
things and do things. Data is a frozen record. Behavior is a function
that takes data in and returns data out. If you're reaching for
inheritance, you've taken a wrong turn.

**II. Make illegal states unrepresentable.** The shape of a datum is
its strongest invariant. Constructors refuse invalid states; a checked
fact becomes a type; downstream never re-proves what upstream
established. Parse, don't validate.

*Functions — one idea, honestly declared*

**III. A function is one idea.** It takes exactly what it needs and
returns exactly what it computes. If the signature has two concepts in
it, you have two functions.

**IV. The signature tells the whole truth.** Inward: if something
needs a value, it receives it as a parameter — no spooky action at a
distance, no stringly-typed interfaces, no implicit state. Outward:
same inputs, same outputs; effects and failure appear in the type, not
in the fine print. Pure core, effects at the edges.

*Knowledge — one home per fact*

**V. Every fact has one home.** One authoritative representation of
each decision and each piece of knowledge; everything else inherits or
is derived mechanically — never maintained by hand in parallel.
Configuration is decided once, at the highest level, and threaded
down; no module ever decides its own context. If the design and the
implementation can disagree, you have two sources of truth and zero.

*Layers — what above, how below*

**VI. Separate what from how.** Logic and machinery are different
concerns with a hard boundary. The layer that says *what* to compute
should be readable by someone who has never seen the machinery
underneath. The layer that says *how* lives below, stays below, and
nothing leaks up from it.

**VII. Notation is execution; lowering is transliteration.** Looking
up: the spec layer reads like the math or logic it implements — when
notation *is* the executable object, not a comment beside it, bugs
have nowhere to hide. Looking down: the layer that executes the spec
reproduces it exactly — nothing added, nothing dropped, nothing
reinterpreted; no opinions, no defaults, no helpful conversions. If
the lowering changes anything, the spec is a lie.

*Abstraction — earned, and binding*

**VIII. Earn your abstractions.** No abstraction before the second
use. Three similar lines is better than a premature helper. The right
amount of complexity is the minimum the current task demands — not the
current task plus three hypothetical future ones.

**IX. An abstraction is a contract.** It is defined by what it
guarantees, not what it hides. If you can't state what is always true
of it — properties a client may rely on without reading the
implementation — it isn't an abstraction, it's indirection. Two
implementations that honor the contract must be interchangeable; and
its outputs stay in its vocabulary, so uses compose.

*Verification — formal first*

**X. Trust the most formal thing first.** Types over tests, tests
over docs, docs over comments. Invest in whichever layer catches the
bug earliest with the least ongoing maintenance cost.

## Commands

```bash
# Install for development (editable) + test deps
pip install -e .[test]

# Run the tests
pytest tests/
# Without an install, point Python at the src layout:
PYTHONPATH=src python -m pytest tests/

# Run the CLI (chained pipeline; mirrors the fluent script API)
pgkyl file.gkyl interpolate select --z0 0 plot
pgkyl file.gkyl info

# A diagnostics chain (equation-specific physics; see diagnostics/)
# (diagnostics take NumPy-backed data, so interpolate always runs first)
pgkyl euler_5m_0.gkyl interpolate euler -v pressure --num-moms 5 plot

# An RPN chain over the working set (see operations/evaluate.py)
pgkyl a.gkyl b.gkyl evaluate "f0 f1 +" interpolate plot

# `pgkyl --help` lists every registered command, grouped by section
# (Verbs / Diagnostics / Render / Utility).
pgkyl --help
pgkyl --version
```

## Architecture — a strict, one-way layered DAG

Every folder has **one job**, and imports point in **one direction only** (leaves at the
bottom). There is **no import cycle** — this is enforced by a
test (see "Import contract"). Arrow = "may import":

> **Keeping the picture honest:** the two diagrams below and the prose after them are a
> mirror of `tests/test_postgkyl.py::_ALLOWED` — that dict (and the AST walk that checks
> every real import against it) is the enforced source of truth; this file is only a
> readable projection of it. The two *can* drift (they already had: `operations/_materialize.py`,
> `operations/animate.py`, `operations/average.py`, `operations/eval_at_coord_proj.py`, `operations/local_poly.py`,
> `core/guards.py`, `api/group.py`, and `api/verbs.py` existed in the tree before they
> were added here). Whenever you add a new top-level module file or a new allowed import
> edge, update `_ALLOWED` and this section in the same commit — don't let the picture
> outlive the code it describes.

```
src/postgkyl/
│
├─ __init__.py          facade · `import postgkyl as pg`              [SURFACE]
│
├─ cli/                 Thin Click shells: argv → api / diagnostics   [SURFACE]
│   ├─ app.py
│   └─ commands/        All the callable commands from the command line
│
├─ diagnostics/        equation-specific physics · one module        [COMPOSITION]
│                      per equation model
│
├─ api/                ★ THE FLUENT SURFACE  (sits ABOVE operations)  [FLUENT API]
│   ├─ gdata.py          class GData(GDataState) + .interpolate()/.plot()
│   ├─ group.py          fluent DatasetGroup: broadcasts verbs over its members
│   ├─ verbs.py          module-level fluent verbs with no single `self`
│   │                    (collect/evaluate/relchange/animate) — one-line
│   │                    delegations to `operations`, shared by GData and DatasetGroup
│   └─ load.py           pg.load(...) → returns a GData
│
├─ operations/         one function per verb · the single seam        [VERBS]
│   ├─ interpolate.py    interpolate(d: GDataState) -> GDataState      (core verbs
│   ├─ select.py                                                       only —
│   ├─ plot.py                                                         equation-blind)
│   ├─ animate.py        terminal: sequence of datasets → render's animation engine
│   ├─ average.py        terminal-adjacent: weighted average over a dim subset,
│   │                    stays modal/gkyl-native (composes with further verbs)
│   ├─ eval_at_coord_proj.py  terminal-adjacent: eval at coords, project to the
│   │                    lower-dim basis for survivors, stays modal/gkyl-native
│   ├─ local_poly.py     modal coefficients → discontinuity-preserving plot mesh
│   └─ _materialize.py   shared modal → NumPy-shadow bridge used by plot/animate
│
├─ render/             matplotlib · plotly · pyvista → core/numerics  [BACKEND]
│                      (below operations, which delegates plot() to it)
│
├─ core/               ★ THE CONTAINER  (state only, NO verbs)        [CONTAINER]
│   ├─ state.py          class GDataState: grid·values·ctx·_result·dunders
│   ├─ group.py          DatasetGroup
│   └─ guards.py         shared field-domain guard (backend=="gkyl" -> raise);
│                        one home for the ".interpolate() first" check reused
│                        across operations/diagnostics instead of retyped per verb
│
├─ numerics/           pure NumPy math · 0 internal imports           [LEAF]
├─ dg/                 interpolation bridge + modal ops → gpython     [ENGINE]
├─ io/                 readers (C-native first) + writer → gpython    [ENGINE]
└─ gpython/            ★ THE FOREIGN FLOOR · compiled shim            [FLOOR]
    ├─ csrc/             _gpythonmodule.c — CPython extension over gkyl_gpython.h
    │                    (the shim itself lives in gkeyll/core/zero/)
    ├─ _gpython.so       built extension (scripts/build_gpython.sh)
    ├─ _lib.py           loads _gpython · GPYTHON_API_VERSION handshake
    ├─ array.py          GkylArray — capsule owner of a gkyl_array
    ├─ basis.py          basis cache + interpolation matrices via the shim
    ├─ rio.py            file loading via gkyl_array_rio
    └─ kernels.py        weak mul/div/inv · lincomb · reduce · integrate
```

```
╔══════════════════════════════════════════════════════════════════════════════╗
║ SURFACES        __init__.py  (pg facade)        cli/  (argv → verbs)         ║
║                                                 gui/  (argv → graphics)      ║
╚════════════════════════════╦══════════════════════════════╦══════════════════╝
                             │ imports                      │ imports
                             ▼                              ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║ COMPOSITION                                                                  ║
║   diagnostics/   ★ EQUATION-SPECIFIC PHYSICS · one module per equation model ║
║      five_moment.py  density(d), pressure(d, gas_gamma=…), mach(d) …         ║
║      ten_moment.py   p_par(d, field), agyro(species, field) …                ║
║      mhd.py · plasma.py · multispecies.py · rotations.py · kinetic.py        ║
║      pkpm.py         laguerre_compose(…) + load_pkpm(…)                      ║
║      gyrokinetics/   load_gk_distf · load_gk_quantity + quantity registry    ║
║                      (Tpar, beta, ExB_vel, …) · energy_balance → Figure …    ║
║      discovery.py    shared naming-convention stem/frame discovery           ║
╚════════════════════════════╦═════════════════════════════════════════════════╝
                             │ imports
                             ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║ FLUENT API   ★ the fluent surface lives HERE, above operations               ║
║                                                                              ║
║   api/load.py    pg.load(path) ───────────────────────► returns api.GData    ║
║   api/gdata.py   class GData(GDataState):                                    ║
║                   def interpolate(self): return operations.interpolate(self) ║
║                      def plot(self):   return operations.plot(self)          ║
║   api/group.py   class DatasetGroup(core.DatasetGroup): broadcasts any verb  ║
║                  over its members via __getattr__ — no verb body duplicated  ║
║   api/verbs.py   module-level verbs with no single `self` (collect/evaluate/ ║
║                  relchange/animate) — one-line delegations to operations,    ║
║                  shared by GData and DatasetGroup so spellings can't drift   ║
╚════════════════════════════╦═══════════════════════════════════╦═════════════╝
                             │ imports                           │ extends
                             ▼                                   │ (subclass)
╔══════════════════════════════════════════════════════════════════════════════╗
║ VERBS · basic data operations                                                ║
║   operations/interpolate.py   def interpolate(d: GDataState) -> GDataState   ║
║   operations/select.py                                                       ║
║   operations/plot.py          delegates the actual draw call to render       ║
╚════════════════════════════╦═══════════════════════════════════╩═════════════╝
                             │ imports                            │
                             ▼                                    │
╔══════════════════════════════════════════════════════════════════════════════╗
║ BACKEND                                                                      ║
║   render/ (mpl · plotly · pyvista) — imports only core + numerics; reached   ║
║   from operations/plot.py, and pre-authorized from diagnostics/ (program-    ║
║   scale figures) and the facade (`pg.plot` ← render)                         ║
╚════════════════════════════╦════════════════════════════════════╦════════════╝
                             │ imports                            │
                             ▼                                    ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║ CONTAINER                                                                    ║
║   core/state.py   class GDataState:  grid · values · ctx · _result · dunders ║
║   core/group.py   DatasetGroup                                               ║
║   core/guards.py  shared field-domain guard: backend=="gkyl" -> raise with   ║
║                   the ".interpolate() first" message — one home for a check  ║
║                   operations/diagnostics verbs used to retype independently  ║
╚════════════════════════════╦═════════════════════════════════════════════════╝
                             │ imports
                             ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║ ENGINE / LEAVES                                                              ║
║   numerics/ (pure math · imports nothing)                                    ║
║   dg/ (interpolation bridge + modal ops)   io/ (readers · writer)            ║
╚═════════════╦══════════════════════════════════════╦═════════════════════════╝
              │ imports                              │ imports
              ▼                                      ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║ FOREIGN FLOOR   gpython/  — the compiled gpython bridge (GKEYLL_C_SHIM.md)   ║
║   GkylArray (capsule RAII) · basis cache · rio · kernels                     ║
║                     ▼ import _gpython  (extension over gkyl_gpython.h only)  ║
║   gkeyll/core/zero/{gkyl_gpython.h, gpython.c} — the shim, compiled by       ║
║   Gkeyll's own make core INTO:      ▼ linked -lg0core                        ║
║   libg0core.so  (gkeyll/ submodule · built by scripts/build_gkeyll.sh)       ║
╚══════════════════════════════════════════════════════════════════════════════╝

```

### The two-domain lifecycle (REFACTOR_GKEYLL_FFI.md)

Every dataset lives in one of two backends, discriminated by
`GDataState.backend`:

- **`"gkyl"` (modal domain)** — DG coefficients as a native `gkyl_array`
  (`gpython.GkylArray`). Loading lands here. All math runs inside Gkeyll:
  `*`/`/` → weak kernels (`gkyl_dg_mul_op`/`div_op`), `+`/`-` → coefficient
  lin-combs (`gkyl_array_accumulate`), scalars → `scale`/mean-shift, integer
  powers → repeated weak multiply, `.integrate()` → `gkyl_array_integrate`.
  `values` is a read-only view; `np.asarray`/ufuncs/`select` refuse with
  ".interpolate() first".
- **`"numpy"` (field domain)** — post-`interpolate()` values as a plain ndarray;
  the unchanged NumPy stack (`select`, `plot`, ufuncs, arithmetic).

`interpolate()` is the **one-way bridge**: matrix from Gkeyll's basis functions,
applied per cell with NumPy `tensordot`, returning a *new, by-value* array.

Within the native domain a dataset has one of three **representations**
(`ctx["representation"]`): `modal` coefficients, `nodal` values at the basis
`node_list` points, or `quad` values at Gauss–Legendre points. **The capability
boundary is modal vs point-values, not gkyl vs NumPy:**

- **modal** — only Gkeyll's DG operations: weak `* /`, coefficient `+ -`/scalar
  kernels, `.integrate()`, `.interpolate()`. Ufuncs/`np.asarray`/`plot` refuse.
- **nodal / quad** — the values ARE the field at points, so *every* pointwise
  NumPy operation is exact and allowed (ufuncs, `* / **`, `np.asarray`) —
  computed on the views, wrapped back native, **staying in-representation** —
  and they `plot()` directly at their true point locations (non-tensor node
  sets, e.g. serendipity p2 in 2-D, plot via `.to_quad()`).

Conversions are **never implicit** — only `.to_modal()/.to_nodal()/.to_quad()`
change representation (nodal↔modal exact; quad round-trip exact for degree
≤ 2·num_quad−1); `.apply(fn, num_quad=…)` is the one-shot modal → quad → fn →
project-back spelling (≡ `fn(d.to_quad()).to_modal()`). Datasets combine only
within one representation. See REFACTOR_GKEYLL_FFI.md §3b.

### `core/` — the container (`core/state.py`)
`GDataState` holds one dataset: a nodal `grid` (list of 1-D edge arrays), values in
one of the two backends (`gpython.GkylArray` or `np.ndarray`), and metadata in `ctx`.
It is **verb-less** and imports only downward (`io` to construct itself, `gpython` for
the backend type). It owns:
- shape properties (`num_dims`/`num_comps`/`num_cells`/`bounds`), `grid`/`values`,
- `backend` (`"gkyl"`/`"numpy"`) and `native` (the raw `GkylArray` for the kernels),
- `push`, `clone` (backend-aware deep copy via `type(self)`), and **`_result(...)`** —
  the one "mutate-self vs. emit-new" decision point every verb funnels through,
- pure state readers only: `__array__` (refuses on gkyl-backed data),
  `__repr__`/`__str__`, `info`, `is_interpolated`.
`core/collection.py` has `flatten_datasets` (shared by the multi-dataset entry points).
`core/guards.py` centralizes the field-domain check (`backend == "gkyl"` → raise with
the standard ".interpolate() first" message) that several `operations`/`diagnostics` verbs
need but that isn't itself a verb, so it lives here rather than in `operations`.

### `api/` — the fluent surface (`api/gdata.py`, `api/load.py`)
`class GData(GDataState)` adds the **fluent verb methods** (`.interpolate()`, `.select()`,
`.plot()`, `.save()`, `.info` inherited) and the **computing operators**
(`+ - * / **`, reflected, `__neg__`/`__abs__`, `__array_ufunc__`). Because it lives
*above* `operations`, these are plain top-level delegations — no lazy imports. `pg.load(...)`
returns a `GData`.

`api/group.py` mirrors the same move one level up: `class DatasetGroup(core.DatasetGroup)`
adds broadcasting — any attribute not defined on the class is resolved by `__getattr__`,
looked up on every member, so a verb call broadcasts across the whole group without a
single verb body being duplicated. `api/verbs.py` holds the handful of verbs that
combine *several* datasets and so have no single `self` to hang off of a class —
`collect`, `evaluate`, `relchange`, `animate` — each a one-line delegation to the
matching `operations` function; `GData` and `DatasetGroup` both call through these same
module-level functions for their own methods, so the functional and fluent spellings
of a multi-dataset verb can never drift apart.

**The trick that removes the cycle:** `operations` verbs are typed on `GDataState` but *return*
the caller's concrete class, because `_result` builds `type(self)()`. So `operations` never needs
to import `api`, yet the whole fluent chain stays `GData`. See `HIERARCHY_2.md`.

### `operations/` — the verb library (the single seam)
One module per verb, re-exported from `operations/__init__.py`. Contract:
`op(data: GDataState, *, ..., inplace=False, tag=None, label=None) -> GDataState`.
**Equation-blind core verbs only** — an op never knows which equation system
produced the file; anything that does belongs in `diagnostics/`.
Implemented: `interpolate` (the bridge verb: gkyl-backed in, numpy-backed out),
`select` (field-domain only), `plot` (delegates to `render`), `info`, `integrate`
(terminal; runs inside Gkeyll on modal data), `represent`/`apply` (the explicit
representation verbs behind `.to_modal()/.to_nodal()/.to_quad()/.apply()`),
`arithmetic` (`binary` + `apply_ufunc`), which **dispatches on `backend`**: modal
operands → `dg.modal` kernel calls; numpy operands → the NumPy path; mixed
domains or mixed representations → error, plus the field-domain analysis verbs
(`fft`, `magsq`, `relchange`, `mask`, `collect`, `grid`, `val2coord`,
`extract_input`, `fit` (its `window=True` mode covers growth-rate-style
leading-window fits), `differentiate`, `evaluate`, `map`); and the modal-native
verbs `average` (weighted average over a dimension subset via Gkeyll's
`gkyl_array_average`) and `eval_at_coord_proj` (eval at physical coordinates,
projected onto the lower-dimensional basis for the surviving directions) —
both terminal-adjacent like `represent`: they emit a new, lower-dimensional
dataset that stays modal/gkyl-native, so it composes with further
`.to_nodal()`/`.interpolate()`/`.average()`/`.eval_at_coord_proj()` calls
rather than dropping to NumPy. `local_poly` bridges modal coefficients to a
discontinuity-preserving plotting mesh, and `animate` is `plot`'s terminal
sibling for a dataset sequence — both funnel through the shared, private
`_materialize` helper that does the one "modal must `.interpolate()` first;
point-value representations plot at their true locations" check, so `plot`
and `animate` can't drift apart on that rule. Verbs wrap the layers below;
they don't reimplement.

### `diagnostics/` — equation-specific physics (COMPOSITION, above `api`)
The layer that knows what the numbers *mean* — and the ONLY package in the
COMPOSITION tier. One module (or subpackage) per equation model:
`five_moment`, `ten_moment`, `mhd`, `plasma` (plasma parameters), `multispecies`
(`energetics`, `accumulate_current`), `rotations` (par/perp to B), `kinetic`
(frame transforms), `pkpm` (Laguerre reconstruction + `load_pkpm`),
`trajectory`, `enstrophy`, `ke_dke` (program-scale figures ported from the
old `apps/trajectory.py`/`tools/calc_*.py`), and `gyrokinetics/` (distf/
quantity loaders, the quantity registry — Tpar, beta, drift velocities — plus
its own program-scale analyses: `energy_balance`/`particle_balance`/`nodes`,
ported from the old `apps/gk_*.py`). Contract: a diagnostic takes loaded
data — one or several `GData` — plus physical scalars as keyword-only
options, and returns `GDataState` (via `_result`, same inplace/tag/label
contract as a verb) or a Figure; it is built entirely from the public
vocabulary below it (`operations`, `core`, `numerics`, `api`) and nothing below the
surfaces imports it. The `render` edge is pre-authorized for this layer (a
program diagnostic may want `render.plot()`'s generic panel layout), but as
of this writing every program module builds its own bespoke figure directly
with `matplotlib` instead.

**Each equation model owns its loading internally** — there is no `loaders/`
package. Entry points like `gyrokinetics.load_gk_quantity(...)` (naming-
convention load + registry dispatch, "physics-ready data by name") and
`pkpm.load_pkpm(...)` live beside the physics they feed, because a quantity's
ingredient files and its formula are one piece of equation knowledge. The
only shared piece is `diagnostics/discovery.py` — equation-blind
output-stem/frame discovery, the one home for Gkeyll's file-naming
convention; equation loaders and programs resolve files through it, never
with private globbing.

Functions have real names (`five_moment.pressure(d, gas_gamma=…)`), never
string dispatch; each equation module's `VARIABLES` table maps the CLI's
quantity-name vocabulary (`"density"`, `"pressure"`, …) to those functions —
the one home for that vocabulary. These are **free functions, not `GData`
methods**: the layer sits above the fluent surface. (This layer absorbed the
former `models/` package — array physics now lives as private helpers inside
the equation module that uses it.)

### Engine layers — `dg/`, `io/` (may import `gpython` only)
- **`dg/`** — Gkeyll-kernel orchestration. `dg/interpolate.py` is the one-way modal→NumPy
  bridge (matrix from `gpython.basis`, applied per cell with `tensordot`; nodal-basis
  files convert through the exact `nodal_to_modal` matrix first); `dg/modal.py`
  holds the operations that stay modal (weak algebra, `lincomb`, `shift_mean`,
  `power`, `integrate`); `dg/rep.py` holds the explicit representation changes
  (modal·nodal·quad) and `apply_pointwise` — all on native arrays.
- **`io/`** — file I/O: `read()` dispatches over a reader registry. `GkylCReader`
  (first) reads field files entirely inside Gkeyll (`gkyl_grid_array_new_from_file`)
  and returns a native `GkylArray`; the pure-Python `GkylReader` is the fallback for
  no-library installs, partial loads, and dynvectors. `save()` supports
  `gkyl`/`txt`/`npy`/`vtk`. Readers fill a plain `ctx` dict and return
  `(grid, values)` — they never import `core`.

### Leaves — `numerics/` (imports nothing), `gpython/` (the foreign floor)
- **`numerics/`** — pure NumPy: `idx_parser` (selection strings) and `elementwise`
  (`grids_compatible`). No `GData`, ever.
- **`gpython/`** — **the only doorway to the foreign world** (a test enforces this),
  and it is a *compiled* one (GKEYLL_C_SHIM.md): the gpython shim
  (`gkeyll/core/zero/{gkyl_gpython.h, gpython.c}`) lives **in the gkeyll tree** and is
  compiled by Gkeyll's own `make core` *into* `libg0core.so` — it holds every
  struct access, the by-value `struct gkyl_basis` convention, and the basis
  function-pointer dispatch, all checked by the C compiler against the headers
  in the same tree (shim and library can never drift apart).
  `csrc/_gpythonmodule.c` wraps `gkyl_gpython.h` (opaque handles + scalars + buffers
  only) into the `_gpython` extension, built by `scripts/build_gpython.sh` against
  the submodule's `libg0core.so` (linked + rpath-bound, not dlopened).
  `_lib.py` imports the extension and performs the `GPYTHON_API_VERSION`
  handshake. `array.py`'s
  `GkylArray` holds the owning capsule (its destructor releases the C array;
  zero-copy constructions pin their NumPy buffer in the capsule, and `view()`
  ties the ndarray's `base` chain to the capsule so views outlive their dataset
  — never hand out C memory without that pin). `basis.py` builds every matrix
  by evaluating Gkeyll's own basis through the shim: `eval_matrix(points)`,
  nodal↔modal, modal↔quad (+ Gauss rules). No struct layout, signature, or
  ctypes declaration exists in Python. `gpython.available()` is the single
  capability switch.

### `render/` — visualization backend (`render/matplotlib.py`)
`plot(*datasets, ...)` — 1-D lines / 2-D pcolormesh, one panel per component, multi-dataset
overlay. Imports `core`/`numerics` only; requires interpolated data.

### `__init__.py` — the facade (pure re-export)
Gathers the public names from the layer that owns each: `load`/`GData` ← `api`,
`plot` ← `render`, `info` ← `operations`, `save` ← `io`, `load_gk_quantity`/
`load_gk_distf`/`available_gk_quantities` ← `diagnostics.gyrokinetics`. **It
contains no function or class definitions** (a test enforces this).

### `cli/` — the CLI (chained pipeline on pure Click)
`cli/app.py` defines `PgkylGroup(click.Group)` with `chain=True`; the chaining loop and
callback-before-dispatch are **native to Click**. The custom code is a small
`get_command` override for command-name **abbreviation** (e.g. `interp`→`interpolate`,
`sel`→`select`) and **bare-filename-as-`load`**, plus a `format_commands` override
that groups `pgkyl --help`'s listing under section headers (`COMMAND_SECTIONS` in
`cli/commands/__init__.py`: Verbs / Diagnostics / Render / Utility) —
presentation only; every command stays a flat, chainable top-level `click.Command`
regardless of its section. Each verb is a thin module under `cli/commands/` (40+
commands: the equation-blind `operations` verbs (including `load`), one per `diagnostics`
equation model (including the gyrokinetic/pkpm loaders), the `render` backends,
and session utilities — `status`/`print`/`listoutputs`/`save`) that uses
**only the public API** (`pg.load`/`pg.plot` and `GData` methods) — so `cli`
depends on the facade alone.
`--version` (via `postgkyl.__version__`) and `--help` are wired through Click's
own `version_option`/group help. The console entry point object is
`postgkyl.cli.app:cli`.

> Chaining is a Click feature; Typer deliberately single-dispatches and cannot do it
> without re-implementing the loop. See `CLI_PLAN.md` for that decision.