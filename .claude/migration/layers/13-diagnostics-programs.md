# Layer 13 — diagnostics programs (composed analyses → figures)

## Mission

Extend the `diagnostics/` package (created by the layer-10 restructure with
the per-equation quantity modules) with the program-scale diagnostics: port
the old `apps/` and the frame-sweeping tools into functions that compose
the equation-internal loaders + ops + render into complete analyses returning
matplotlib figures (and/or result arrays). Shed Typer entirely.

These land in the SAME package as `five_moment.py`/`ten_moment.py`/… because
they are the same kind of thing — equation-specific compositions on loaded
data — just bigger: many files in, a figure out. Keep the per-equation
organization: gyrokinetic programs go in a `gyrokinetics/` subpackage.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. `CLAUDE.md` — the diagnostics section (contract: GData + physical scalars
   in, GData or Figure out; built only from the public vocabulary below)
3. What layer 10 landed in `diagnostics/` (module layout, `_result` contract,
   `VARIABLES` tables) and what layer 12 landed in `diagnostics/discovery.py`
   + `diagnostics/gyrokinetics/` (its report) — programs resolve files through
   `discovery` and load through the equation-internal loaders
   (`gyrokinetics.load_gk_distf`, …), never with private `glob` logic (the
   old apps hand-roll globbing — do not port that; replace it).
4. Sources: `src_bak/postgkyl/apps/{gk_energy_balance.py,gk_particle_balance.py,gk_nodes.py,trajectory.py}`,
   `src_bak/postgkyl/tools/{calc_enstrophy.py,calc_ke_dke.py}`

## Source → target map

| Source | Target | Adaptation |
|---|---|---|
| `apps/gk_energy_balance.py` | `diagnostics/gyrokinetics/energy_balance.py` | Signature: explicit params in (paths, species, frame range, options), figure (+ computed arrays) out. Replace `typer` echo/options with parameters and raises; replace `utils.verb_print` with nothing (silent) or a `logging` call. |
| `apps/gk_particle_balance.py` | `diagnostics/gyrokinetics/particle_balance.py` | Same treatment. |
| `apps/gk_nodes.py` | `diagnostics/gyrokinetics/nodes.py` | Keep `is_geo_mapc2p`, `nodes_to_RZ`, multiblock suffix handling as module functions (they are testable units). |
| `apps/trajectory.py` | `diagnostics/trajectory.py` | `FuncAnimation`-based; return the animation object; saving is the caller's choice. |
| `tools/calc_enstrophy.py` | `diagnostics/enstrophy.py` | Frame sweep; drop the dead `postgkeyll` import; loads via `diagnostics.discovery` + `api`. |
| `tools/calc_ke_dke.py` | `diagnostics/ke_dke.py` | Same. |

Common shape for every program diagnostic:
`def name(..., *, show: bool = False) -> Figure | tuple[Figure, <results>]` —
no `plt.show()` unless `show=True`; everything the function needs arrives as
a parameter (doctrine IV); no reading of global state or cwd conventions
beyond the explicit path arguments.

`diagnostics/__init__.py` gains the new modules (`from . import gyrokinetics,
trajectory, enstrophy, ke_dke`); still no defs. The facade may re-export
`diagnostics` as a subpackage name (pure re-export).

## Import contract

Extend the `"diagnostics"` edge set in `tests/test_postgkyl.py::_ALLOWED`
(layer 10: `{"core", "ops", "numerics"}`; layer 12 added `"api"`) with
`"render"` — comment: program diagnostics compose figures (authorized by this
file). If the facade gains the `diagnostics` name, add `"diagnostics"` to the
facade (`""`) edge set with a comment.

## Tests

`tests/test_diagnostics_programs_*.py`. Agg backend. The GK balance
diagnostics need multi-frame GK output that the repo may not ship — structure
each test to (a) unit-test the pure helpers (`nodes_to_RZ`, balance-term
arithmetic on synthetic arrays) unconditionally, and (b) run the full figure
path against `tests/test_data/` if the needed files exist, else `pytest.skip`
with a message naming the missing fixture. Trajectory: synthesize a small
dynvector trajectory in `tmp_path` (the io writer can create it) and assert
frame count. Never let a diagnostic test silently pass without asserting —
skip loudly instead.

## Definition of done

1. Full suite green; architecture tests pass with the extended edges.
2. `--cov=postgkyl.diagnostics` ≥ 80% for the new modules (figure-layout code
   is hard to cover — pure helpers must be ~100%); the layer-10 quantity
   modules stay at 100%.
3. Report: per-diagnostic parameter surface (old CLI options → new kwargs),
   fixtures missing that forced skips, coverage, pytest summary.
