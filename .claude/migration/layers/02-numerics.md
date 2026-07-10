# Layer 02 — numerics (pure NumPy math, imports nothing internal)

## Mission

Port the pure-math half of the old `tools/` and `utils/` into
`src/postgkyl/numerics/`. Every function here takes plain arrays (and scalars)
and returns plain arrays — **no `GData`, no `ctx`, no file paths, no
matplotlib, no typer**. The `ops/` verbs (layers 07–08) will unwrap
`GDataState` and call these.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`, `CLAUDE.md`
2. The existing style exemplars: `src/postgkyl/numerics/{idx_parser.py,elementwise.py}`
3. Each source file below, in full, before porting it.

## Source → target map

| Source (src_bak/postgkyl/) | Target (src/postgkyl/numerics/) | Adaptation |
|---|---|---|
| `tools/calculus.py` | `calculus.py` | Keep `integrate` (trapezoidal over named axes). Port `grad`/`div`/`curl` only if they are real implementations — if they are stubs, do not port; note it. Strip the GData/`input_parser` dual-input: signature becomes `(grid: list[np.ndarray], values: np.ndarray, axis=..., ...)`. |
| `tools/mag_sq.py` | `mag_sq.py` | Arrays in/out; the comp-selection concern stays in the verb. |
| `tools/rel_change.py` | `rel_change.py` | Same. |
| `tools/rotation_matrix.py` | `rotation_matrix.py` | 1:1. |
| `tools/fft.py` + `tools/init_polar.py` + `tools/polar_isotropic.py` | `fft.py` | One module: `fft`, `psd`, polar-isotropic binning. scipy.fft is a hard dep. |
| `tools/fit.py` | `fit.py` | The whole fit library: `FIT_FUNCTIONS`, the named model functions, the RPN custom-function parser (`_rpn_make_func`, `rpn_param_names`), `fit`, `fit_evaluate`, `auto_guess`. scipy.optimize is a hard dep. |
| `tools/growth.py` | `growth.py` | `exp2`, `fit_growth`. |
| `tools/filters.py` | `filters.py` | Port `fft_filtering` and `butter_filtering` **math only**. The interactive `_click_coords` matplotlib picker is an effect at the edge — do NOT port it here; note in your report that it belongs to render/cli if anyone still wants it. |
| `tools/ev_ops.py` | `ev_ops.py` | The RPN operator table `cmds`. Strip every `typer` use → `raise ValueError(...)`. Operators that need GData semantics (grad/curl/integrate over a dataset) should be expressed over `(grid, values)` pairs; keep the table's keys and arities identical so layer 07's `ev` verb can consume it unchanged. If an operator genuinely cannot be expressed without GData, leave a documented placeholder entry raising `NotImplementedError` and list it in your report. |
| `utils/nodal_to_cell_centered_grid.py` | `grid_centering.py` | Drop the dead `postgkeyll` import; pure function. |
| `utils/downsample.py` | `downsample.py` | Pure array downsampling. |

Do NOT port: `utils/input_parser.py` (the dual-input pattern is banned — see
PYTHON_PRINCIPLES.md §9), `tools/params.py`, `tools/prim_vars.py`,
`tools/pressure_diagnostics.py`, anything else physics-flavored (layer 06),
`tools/calc_enstrophy.py` / `calc_ke_dke.py` (layer 12).

## Hard constraints

- `numerics/` imports **nothing** from postgkyl (leaf layer). numpy/scipy only.
- Re-export the public names from `numerics/__init__.py` (re-export only, no defs).
- Keep numerical behavior identical to `src_bak` — copy the math bodies, adapt
  the shells. Where old code had a bug you must fix, prove it with a test and
  document it.

## Tests

Create `tests/test_numerics_<module>.py` per module. Port the assertions from
`tests_bak/`: `test_tools_calculus.py`, `test_tools_fft.py`,
`test_tools_filters.py`, `test_tools_growth.py`, `test_tools_misc.py`
(mag_sq / rel_change / rotation_matrix / ev_ops parts), `test_fit.py` (66
tests — port them all), adapting old GData-based call sites to the new
array signatures. Then add what they miss: analytic FFT of a pure sine,
integrate of a polynomial with a hand-computed value, fit recovery of known
parameters from seeded noisy data, RPN parser edge cases (bad token, arity
mismatch, empty expression).

## Definition of done

1. Full suite green: `PYTHONPATH=src python -m pytest tests/ -q`.
2. `--cov=postgkyl.numerics --cov-report=term-missing` ≥ 95%; misses justified.
3. Architecture tests pass (numerics must stay a leaf).
4. Report: source→target table of what was ported / dropped / deferred, any
   behavioral differences from src_bak (should be none), coverage per file,
   the ev_ops entries left as placeholders (if any) for layer 07.
