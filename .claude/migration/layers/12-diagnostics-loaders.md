# Layer 12 — diagnostics loaders (equation-internal loading + the GK quantity physics)

## Mission

There is NO top-level `loaders/` package. Each equation model loads its own
files: the loading entry points live *inside* the equation's module or
subpackage in `diagnostics/`, next to the physics they feed. This layer ports
the old workflow loaders accordingly: shared output-stem discovery, the
gyrokinetic stack (distribution functions + the quantity registry, rewired
off the dead ctypes path), and the PKPM loader.

Why this shape (decision record): the old `gk_quantities` registry fused two
concerns — naming-convention file resolution (loading) and the fetch physics
(`fetch_Tpar_from_M0_M1_M2par`, `fetch_beta_from_bmag_press`, `fetch_ExB_vel`,
…), which are gyrokinetic derived quantities, i.e. diagnostics. Splitting
them across two packages would give the gyrokinetics equation model two homes
(doctrine V) and force an import edge between siblings. Instead the whole
stack — resolution, registry, physics — lives in `diagnostics/gyrokinetics/`,
and only the equation-blind stem discovery is shared, as a module of the same
package.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. `CLAUDE.md` — the diagnostics section (equation-specific compositions;
   loading is equation-internal)
3. What layer 10 landed in `diagnostics/` (module layout, `_result` contract)
4. Sources, in full: `src_bak/postgkyl/loader.py`,
   `src_bak/postgkyl/loaders/{__init__.py,gk_distf.py,gk_quantity.py,pkpm.py}`,
   `src_bak/postgkyl/gk/{gk_utils.py,gkeyll_enums.py,gk_quantities/{gkquantity.py,fetch_funcs.py,registry.py}}`
5. `tests_bak/{test_loader.py,test_load.py,test_gk_load_quantity.py}` and the
   modified copy in the worktree (`git diff tests_bak/test_gk_load_quantity.py`
   may show recent intent)
6. Test data: `tests/test_data/rt_gk_tcv_iwl_1x2v_p1-{elc_250,elc_jacobvel,elc_mapc2p_vel}.gkyl`,
   `rt_gk_tcv_iwl_1x2v_p1-geo_int_jacobtot_inv.gkyl`,
   `rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl` —
   these were staged specifically for this layer.

## Source → target map

| Source | Target | Adaptation |
|---|---|---|
| `loader.py` (`find_output_stems`, `_Loader`, `load` extras beyond api) | `diagnostics/discovery.py` | Equation-blind stem discovery by naming convention — the ONE home for "what outputs does this directory hold"; the equation loaders below and the layer-13 programs resolve files through it, never with private `glob` logic. Port the `_Loader` fluent workflow only if `api.load` doesn't already cover it — if it does, port only `find_output_stems` and say so. |
| `gk/gk_quantities/gkquantity.py` | `diagnostics/gyrokinetics/quantity.py` | `GkQuantity` (make it a frozen dataclass: name, ingredient source combos, compute fn, label, flags) + the registry class. Source-combination resolution calls `diagnostics.discovery`, not its own globbing. |
| `gk/gk_quantities/fetch_funcs.py` | `diagnostics/gyrokinetics/quantities.py` | THE HARD PART — and it is physics, not loading: `Tpar`, `Tperp`, `temp`, `press`, `beta`, `upar`, `ExB_vel`, `gradB_vel`, `diamag_vel`, … Every `fetch_*` currently computes via `GkeyllDGops` (ctypes — dead). Rewire each DG operation to the new surface: weak multiply/divide → GData arithmetic in the modal domain (`*`/`/` on gkyl-backed data), averages/integrals → `.integrate()`, evaluation → `.interp()`/representation verbs. Physical constants → `scipy.constants`. Go quantity by quantity; a quantity you cannot rewire yet becomes a registry entry that raises `NotImplementedError("needs <capability>")` — never a silent wrong answer. Tally ported vs deferred in the report. |
| `gk/gk_quantities/registry.py` | `diagnostics/gyrokinetics/registry.py` | Populate from `quantities.py`; `available_quantities()`. |
| `loaders/gk_quantity.py` | `diagnostics/gyrokinetics/load_quantity.py` | `load_gk_quantity(...)`: naming-convention load + registry dispatch — the "give me physics-ready data by name" entry point for GK. |
| `loaders/gk_distf.py` | `diagnostics/gyrokinetics/distf.py` | `load_gk_distf`, `resolve_frames`; jacobian/mapc2p handling via the staged test files. |
| `loaders/pkpm.py` | `diagnostics/pkpm.py` | `load_pkpm(...)` joins `laguerre_compose` in the module layer 10 created — the PKPM model's loader lives with the PKPM model's physics. |
| `gk/gk_utils.py` | `diagnostics/gyrokinetics/utils.py` | Port the file/geometry helpers (`read_gfile`, `parse_slice_string`, `get_block_indices`, …). Drop matplotlib bits (`set_tick_font_size` belongs to render/cli — do not port; note it). |
| `gk/gkeyll_enums.py` | only what is actually consumed | If a loader needs an enum name map (e.g. `gkyl_geometry_id`), port the minimal table into the module that uses it, with a comment naming the exact Gkeyll header it mirrors and a test pinning the values. Do not port wholesale. |

`diagnostics/gyrokinetics/__init__.py` re-exports the public entry points
(`load_gk_quantity`, `load_gk_distf`, `available_quantities`, the quantity
functions); `diagnostics/__init__.py` gains `from . import gyrokinetics,
discovery`. The facade may re-export `load_gk_quantity` etc. (pure
re-export) so `pg.load_gk_quantity(...)` keeps working.

## Import contract (`tests/test_postgkyl.py::_ALLOWED`)

Extend the `"diagnostics"` edge set (layer 10 created it as
`{"core", "ops", "numerics"}`) with `"api"` — comment: equation loaders build
on `pg.load`/`GData` modal arithmetic (authorized by this file). There is no
`"loaders"` layer; do not add one.

## Tests

`tests/test_diagnostics_discovery.py` (port `test_loader.py`'s 14),
`tests/test_diagnostics_gk_load.py` (port + extend `test_gk_load_quantity.py`
using the staged rt_gk_tcv files — cover several registry quantities end to
end; gate modal-domain math on `ffi.available()`),
`tests/test_diagnostics_pkpm.py` (build minimal synthetic pkpm-named files in
`tmp_path` if no fixture exists). Registry: unknown quantity name → clear
error listing available names; deferred quantities raise their
NotImplementedError.

## Definition of done

1. Full suite green; architecture tests pass with the extended edge; no
   `loaders` package exists anywhere under `src/postgkyl/`.
2. `--cov=postgkyl.diagnostics` ≥ 85% for the new modules; the layer-10
   quantity modules stay at 100%.
3. Report: fetch_* rewiring tally (ported / deferred+reason), enum tables
   ported and their Gkeyll header sources, coverage, pytest summary.
