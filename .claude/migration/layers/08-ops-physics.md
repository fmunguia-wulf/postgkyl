# Layer 08 — ops (wave B): physics verbs + map

## Mission

Port the physics verbs (delegating to layer 06's `models/`) and the `map`
verb (delegating to layer 03's `dg/map.py`). Same verb contract as layer 07 —
read its instruction file's contract section and the same exemplars.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. `.claude/migration/layers/07-ops-field.md` (contract section) + the
   exemplar verbs in `src/postgkyl/ops/`
3. `MAPPING.md` — the VERB row and the select-guard row of its layer table
4. What layers 03 and 06 actually landed (`dg/map.py`, `models/*` — read
   their reports in `.claude/migration/reviews/` and the modules themselves)
5. Each old verb: `src_bak/postgkyl/ops/{moments,agyro,current,energetics,rotate,transform_frame,laguerre,map}.py`

## Verb list (source → target, all in `src/postgkyl/ops/`)

| Old | New module | Delegates to |
|---|---|---|
| `ops/moments.py` (`euler`, `tenmoment`, `mhd`, `velocity`) | `moments.py` | `models.five_moment` / `ten_moment` / `mhd`. Keep the old quantity-name option strings (`"density"`, `"pressure"`, …) exactly — the CLI exposes them. |
| `ops/agyro.py` (`agyro`, `mom_agyro`) | `agyro.py` | `models.ten_moment`. |
| `ops/current.py` | `current.py` | `models.energetics.accumulate_current`. |
| `ops/energetics.py` | `energetics.py` | `models.energetics`. Multi-dataset verb (elc, ion, field). |
| `ops/rotate.py` (`parrotate`, `perprotate`) | `rotate.py` | `models.rotations`. |
| `ops/transform_frame.py` | `transform_frame.py` | `models.frame`. |
| `ops/laguerre.py` (`laguerre_compose`) | `laguerre.py` | `models.laguerre`. |
| `ops/map.py` | `map.py` | **Not the old algorithm.** Implement MAPPING.md's VERB row: `map(data, mapping: str | GDataState, *, space="conf", inplace=False, tag=None, label=None)`; a path loads via `core.GDataState(path)` (ops may import core, never io/api); validate `mapping.num_comps == m × num_basis`; splice new grid arrays from `dg.map_grid` into a copy of the grid; result carries `ctx["grid_type"] = "mapped"`; target must be field-domain; the mapping itself is never interp-ed. |

Also per MAPPING.md: add the guard in `ops/select.py` — coordinate-`sel`
along an axis whose grid array is multi-dimensional (curvilinear) refuses
with a clear error; index-`sel` and 1-D mapped axes keep working.

All field-domain physics verbs refuse modal data with the standard guard.
Update `ops/__init__.py` re-exports.

## Tests

- `tests/test_ops_moments.py` — port `tests_bak/test_ops_wave4.py` and
  `test_ops_wave5.py` verb-level assertions. The old fixtures
  (`hll-euler.gkyl`, `shock-f-*.gkyl`) live only in `tests_bak/test_data/` —
  COPY the ones you need into `tests/test_data/` (copying binary fixtures is
  allowed; note each copy in your report).
- `tests/test_ops_physics.py` — agyro/current/energetics/rotate/
  transform_frame/laguerre: analytic cases via `models` parity (verb result ==
  model function applied to the unwrapped arrays), guards, inplace semantics.
- `tests/test_ops_map.py` — MAPPING.md's test list at verb level: identity
  map leaves grid unchanged; `space="conf"` vs `"vel"` axis offsets; shape
  preservation; modal-target refusal; num_comps validation error; the
  select-guard on a curvilinear axis. Use
  `tests/test_data/rt_gk_tcv_iwl_1x2v_p1-elc_mapc2p_vel.gkyl` (+ `-elc_250.gkyl`)
  for a real vel-space mapping integration test, and the
  `generated/2d_c2p_*` fixtures for conf-space. Gate on `ffi.available()`.

## Definition of done

1. Full suite green; architecture tests pass.
2. `--cov` ≥ 90% for the new modules.
3. Report: verb inventory, fixture files copied, any divergence between old
   moments outputs and new (must be none — same math through models),
   MAPPING.md deviations if any, coverage, pytest summary.
