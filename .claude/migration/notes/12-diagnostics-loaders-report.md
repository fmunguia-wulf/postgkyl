# Layer 12 — diagnostics loaders: implementer report (Definition of Done #3)

Written post hoc, in response to review criticism C2
(`.claude/migration/reviews/12-diagnostics-loaders-review.md`) — the
instruction file's Definition of Done item 3 asked for this report to be
collected in one place rather than left distributed across docstrings.

## `fetch_*` rewiring tally

`src_bak/postgkyl/gk/gk_quantities/fetch_funcs.py` -> `src/postgkyl/diagnostics/gyrokinetics/quantities.py`.

Every public `fetch_*` function (14) plus `load_distf` (the registry's distf
fetch function) is **ported**, none deferred:

```
fetch_Bmag_from_bmag
fetch_ExB_vel_from_bmag_Phi
fetch_M0_from_dens
fetch_Tpar_from_M0_M1_M2par
fetch_Tperp_from_M0_M2perp
fetch_beta_from_bmag_press
fetch_diamag_vel_from_bmag_press_dens
fetch_dens_from_M0
fetch_gradB_vel_from_bmag_gradbmag
fetch_press_from_BiMax
fetch_press_from_Tpar_Tperp_dens
fetch_temp_from_press_dens
fetch_upar_from_M0_M1
fetch_vth_from_temp
load_distf
```

(`diff` of the `def fetch_\w+`/`def load_distf` symbol sets between the two
files, sorted, is empty.) No `NotImplementedError` entries exist anywhere in
`diagnostics/gyrokinetics/` — every quantity the old registry exposed is
computable on the new surface.

Rewiring: every `GkeyllDGops`-mediated (ctypes) weak-DG operation was
replaced by "interpolate first, then plain NumPy" (`GData.interp()` +
elementwise `*`/`/`/`+`/`-` on the resulting field-domain arrays) — stated at
the top of `quantities.py` (module docstring, lines 1-27) since it's the one
non-local decision in this layer. Averages/integrals that used to go through
a DG integral now use the interpolated array directly (no
`.integrate()` calls were needed by any ported `fetch_*` — none of them
compute a grid integral, they combine already-loaded fields pointwise).
Physical constants (`mu_0`) come from `scipy.constants`, not a re-typed
`gk/gkeyll_const.py` table.

## Enum tables

**None ported.** `gk/gkeyll_enums.py` (`gkyl_geometry_id`, `gkyl_basis_type`,
`pgkyl_basis_type`, `enum_idx_to_key`/`enum_key_to_idx`,
`basis_type_gkyl_to_pgkyl`) is consumed, in `src_bak`, only by
`tools/gkeyll_dg_ops.py` (the dead ctypes path — rule 22, not ported),
`data/gdata.py` (the old ctypes-backed reader, superseded by `io`/`ffi`), and
`apps/gk_nodes.py` (a CLI app outside this layer's scope). None of the
in-scope sources for this layer (`loader.py`, `loaders/{gk_distf,gk_quantity,
pkpm}.py`, `gk/gk_quantities/{gkquantity,fetch_funcs,registry}.py`) import
`gkeyll_enums` at all, so there is nothing to port per the instruction file's
"only what is actually consumed" clause — confirmed by grep, zero hits for
`gkeyll_enums`/`gkyl_geometry_id`/`gkyl_basis_type` under
`src/postgkyl/diagnostics/`.

## Coverage

```
PYTHONPATH=src python -m coverage run -m pytest tests/ -q
# 1220 passed, 3 skipped in 66.61s
PYTHONPATH=src python -m coverage report -m --include="*/postgkyl/diagnostics/*"
```

```
Name                                                     Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------------------
src/postgkyl/diagnostics/__init__.py                         2      0   100%
src/postgkyl/diagnostics/discovery.py                       27      0   100%
src/postgkyl/diagnostics/five_moment.py                    116      0   100%
src/postgkyl/diagnostics/gyrokinetics/__init__.py             6      0   100%
src/postgkyl/diagnostics/gyrokinetics/distf.py               69      7    90%   166-167, 170-171, 173-174, 177
src/postgkyl/diagnostics/gyrokinetics/load_quantity.py       29      0   100%
src/postgkyl/diagnostics/gyrokinetics/quantities.py         159      0   100%
src/postgkyl/diagnostics/gyrokinetics/quantity.py           115      0   100%
src/postgkyl/diagnostics/gyrokinetics/registry.py            52      0   100%
src/postgkyl/diagnostics/gyrokinetics/utils.py               65      2    97%   43, 95
src/postgkyl/diagnostics/kinetic.py                          46      0   100%
src/postgkyl/diagnostics/mhd.py                              79      0   100%
src/postgkyl/diagnostics/multispecies.py                     41      0   100%
src/postgkyl/diagnostics/pkpm.py                             43      0   100%
src/postgkyl/diagnostics/plasma.py                          95      0   100%
src/postgkyl/diagnostics/rotations.py                        26      0   100%
src/postgkyl/diagnostics/ten_moment.py                      178      0   100%
--------------------------------------------------------------------------------------
TOTAL                                                      1148      9    99%
```

`distf.py`'s 7 missed lines (166-177) are the `use_c2p_vel`/`use_mc2nu`/
`use_mapc2p` coordinate-mapping branches; see the review's C4 and this
review's Resolutions section for why they remain uncovered (a fixture/data-
staging limitation, not a code issue). `utils.py`'s 2 missed lines (43, 95)
are a defensive `isinstance(grid, np.ndarray)` branch that is unreachable
under this codebase's container contract (`GDataState._grid` is always a
`list`).

## Pytest summary

Full suite: **1220 passed, 3 skipped** in 66.61s. Architecture tests
(`tests/test_postgkyl.py`) pass in full, including the extended
`"diagnostics" -> "api"` edge.
