# Layer 10 — diagnostics restructure (models + physics verbs → one equation layer)

## Mission

**This is a restructure of already-migrated code, not a src_bak port.**
Create `src/postgkyl/diagnostics/` — the equation-specific layer, one module
per equation model — by folding together `models/` (layer 06) and the seven
physics verbs in `ops/` (layer 08). When you are done, `models/` no longer
exists, `ops/` contains only equation-blind core verbs on a single
`GDataState`, and every equation-specific function lives in `diagnostics/`
with a GData-facing signature.

Why (decision record): `models/` had exactly one consumer — the ops physics
verbs — so the models/ops split was an unearned abstraction (doctrine VIII),
and it forced a stringly-typed dispatch (`euler(d, variable="pressure")`)
that doctrine IV forbids. The physics functions are compositions (multi-
dataset, equation-aware: `energetics(elc, ion, field)`,
`agyro(pressure, bfield)`), so they belong in the COMPOSITION tier, above
`api`, not below `ops`. See CLAUDE.md's diagnostics section.

## Scope authorization

This layer explicitly authorizes what implementer rule 1 normally forbids:
**moving and deleting files that layers 06 and 08 created** — everything
under `src/postgkyl/models/`, the seven physics-verb modules in
`src/postgkyl/ops/`, `ops/_guards.py`, their re-exports, their tests, and
the `_ALLOWED` map in `tests/test_postgkyl.py` (edits specified below).
Still off-limits: `src_bak/`, `tests_bak/`, C sources, `gkeyll/`, and every
other layer's files.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. `CLAUDE.md` — the diagnostics section (the layer contract you are building)
3. The code you are moving, in full: `src/postgkyl/models/*.py`,
   `src/postgkyl/ops/{moments,agyro,current,energetics,rotate,transform_frame,laguerre,_guards}.py`
4. `.claude/migration/reviews/{06-models-review.md,08-ops-physics-review.md}`
   — known preserved bugs (frame.py c_dim, laguerre broadcast axis) stay
   preserved; do not "fix" them while moving.
5. An exemplar core verb for the contract shape: `src/postgkyl/ops/magsq.py`

## Target layout (one module per equation model)

| New module | Absorbs | Public functions (GData in → GData out) |
|---|---|---|
| `diagnostics/five_moment.py` | `models/five_moment.py` + the euler table and `velocity` from `ops/moments.py` | `density, xvel, yvel, zvel, vel, pressure, ke, temp, sound, mach, velocity` |
| `diagnostics/ten_moment.py` | `models/ten_moment.py` + the tenmoment table from `ops/moments.py` + `ops/agyro.py` | the five_moment set plus `pxx, pxy, pxz, pyy, pyz, pzz, pressure_tensor, p_par, p_perp, agyro, mom_agyro` |
| `diagnostics/mhd.py` | `models/mhd.py` + the mhd table from `ops/moments.py` | `density, xvel, yvel, zvel, vel, bx, by, bz, bi, mag_pressure, pressure, temp, sound, mach` |
| `diagnostics/plasma.py` | `models/plasma_params.py` | `magB, vt, vA, omegaC, omegaP, d, lambdaD, rho, beta` — these never had verbs; give each a GData-facing wrapper (species/field datasets in, GData out) over the moved array math |
| `diagnostics/multispecies.py` | `models/energetics.py` + `ops/energetics.py` + `ops/current.py` | `energetics(elc, ion, field, ...)`, `accumulate_current(...)` |
| `diagnostics/rotations.py` | `models/rotations.py` + `ops/rotate.py` | `parrotate, perprotate` |
| `diagnostics/kinetic.py` | `models/frame.py` + `ops/transform_frame.py` | `transform_frame` |
| `diagnostics/pkpm.py` | `models/laguerre.py` + `ops/laguerre.py` | `laguerre_compose` |

`diagnostics/__init__.py` re-exports the modules (`from . import five_moment,
ten_moment, ...`); no defs. Layers 12 and 13 will later extend this package
with the equation-internal loaders (`gyrokinetics/`, `discovery.py`,
`pkpm.load_pkpm`) and the program diagnostics (`trajectory.py`,
`enstrophy.py`, `ke_dke.py`) — there is no separate `loaders/` package.

## The function contract

Each public function keeps the verb contract exactly:
`fn(data: GDataState, ..., *, <physical scalars>, inplace=False, tag=None,
label=None) -> GDataState`, funneling through `_result`. Multi-dataset
functions take each dataset as an explicit positional/keyword parameter.
The array-level math from `models/` moves in **verbatim** as module-private
helpers (`_get_density(grid, values)` — keep the bodies byte-identical;
renaming `get_x` → `_get_x` and rewiring imports is the only allowed change),
or is inlined where the helper would have exactly one two-line caller.

**The string dispatch dies as a public surface.** `euler(d,
variable="pressure")` becomes `five_moment.pressure(d)`. But the CLI (layer
14) needs the old quantity-name vocabulary (`"density"`, `"pressure"`, …)
byte-compatible, so each equation module keeps ONE home for it:

```python
VARIABLES: dict[str, Callable[..., GDataState]] = {"density": density, ...}
```

— the old option strings from `ops/moments.py`'s tables, mapped to the new
public functions. Nothing in `diagnostics/` dispatches through it; it exists
for surfaces above.

## The guard moves to core

`ops/_guards.py::require_field_domain` enforces a state invariant ("gkyl-
backed modal coefficients refuse pointwise use"), and after this layer it has
users in two packages (`ops/_materialize.py` and the diagnostics modules).
Its one home becomes `core/guards.py` (same function, same docstring, public
name). Update `ops/_materialize.py` to import it from there; delete
`ops/_guards.py`. This is a state-invariant helper, not a verb — `core`
stays verb-less.

## ops/ cleanup

- Delete `ops/{moments,agyro,current,energetics,rotate,transform_frame,laguerre}.py`.
- `ops/__init__.py`: drop their imports and `__all__` entries; rewrite the
  docstring paragraph that says physics verbs delegate to `models` (ops is
  now the equation-blind core-verb library; equation physics lives in
  `diagnostics/`).
- `ops/map.py` and every field verb stay untouched.
- Delete `src/postgkyl/models/` entirely.

## Import contract (`tests/test_postgkyl.py::_ALLOWED`)

- Remove the `"models"` entry and remove `"models"` from the `"ops"` edge set.
- Add, with a comment naming this file:
  `"diagnostics": {"core", "ops", "numerics"}` — equation-specific
  compositions wrap core verbs and state; layer 12 will extend this with
  `api` (equation-internal loaders) and layer 13 with `render` (program
  diagnostics). No `"loaders"` layer will ever exist.
- No other edge changes. The facade does NOT gain diagnostics names in this
  layer (that is layer 12/13/15 work); `import postgkyl.diagnostics as ...`
  is the spelling until then.

## Tests

Pure relocation plus respelling — **the numerical assertions are the parity
baseline and must not change**:

- `tests/test_models_<m>.py` → `tests/test_diagnostics_<m>.py` (new module
  names: `five_moment, ten_moment, mhd, plasma, multispecies, rotations,
  kinetic, pkpm`). Array-math tests now target the private helpers'
  public wrappers; where a test called `models.get_x(grid, values)` directly,
  re-point it at the diagnostics function on a constructed `GDataState` OR
  keep it on the private helper — prefer the public surface, keep the
  asserted numbers identical.
- `tests/test_ops_moments.py` + `tests/test_ops_physics.py` →
  `tests/test_diagnostics_verbs.py` (or fold into the per-module files):
  same fixtures, same assertions, new spellings
  (`ops.euler(d, variable="pressure")` → `diagnostics.five_moment.pressure(d)`).
- Add: each `VARIABLES` table maps every old option string of the
  corresponding old ops table to a callable that equals the module's public
  function (pin the vocabulary).
- Guards: the moved `require_field_domain` tests re-point to `core.guards`;
  every diagnostics function still refuses modal data with the standard
  message.

## Definition of done

1. Full suite green; the four architecture tests pass with the edited
   `_ALLOWED`; `git grep -l "postgkyl.models\|from postgkyl import models" src/ tests/`
   returns nothing; `src/postgkyl/models/` does not exist.
2. Coverage: `--cov=postgkyl.diagnostics` 100%; `--cov=postgkyl.ops` stays
   100% (justified misses inherited from 06/08 — frame.py's structurally-
   unreachable preserved bug — carry over with the same justification).
3. **Numerical parity is against git HEAD, not src_bak**: the relocated tests
   pass with unchanged asserted values. Zero behavior change is the bar;
   the only public-surface change is the spelling of the entry points.
4. Report: move map (old path → new path, per function), the `VARIABLES`
   vocabulary per module (old string → new function), any inlined helpers,
   `_ALLOWED` diff, coverage, pytest summary.
