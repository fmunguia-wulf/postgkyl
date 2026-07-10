# Layer 06 — models (equation-system physics, plug-in per model)

## Mission

Create `src/postgkyl/models/` and port the physics: primitive variables,
pressure diagnostics, plasma parameters, energetics, frame transforms,
rotations, Laguerre composition. Same rule as numerics: functions take arrays
(grid list + values ndarray + physical scalars) and return arrays. The verbs
(layer 08) unwrap `GDataState` and call these. NO GData, NO input_parser
dual-input, NO typer/matplotlib.

## Read first

1. `.claude/DOCTRINE.md` (esp. VII — notation is execution: these functions
   should read like the physics formulas they implement),
   `.claude/migration/PYTHON_PRINCIPLES.md`
2. Sources, in full: `src_bak/postgkyl/tools/{prim_vars.py,pressure_diagnostics.py,params.py,energetics.py,accumulate_current.py,parrotate.py,perprotate.py,transform_frame.py,laguerre_compose.py}`
3. What layer 02 built in `numerics/` (`rotation_matrix` lives there — import
   it, don't duplicate it) — check `_ALLOWED` allows `models → numerics`; if
   not, that edge is authorized by this file: add it with a comment.

## Layout (one module per equation system / concern)

| Target module | Sources | Contents |
|---|---|---|
| `models/five_moment.py` | `prim_vars.py` (euler parts) | density, velocity, pressure, temperature, sound speed, Mach — the 5-moment/euler `get_*` family. |
| `models/ten_moment.py` | `prim_vars.py` (10-moment parts) + `pressure_diagnostics.py` | pressure tensor, `p_par`/`p_perp`, agyrotropy measures. |
| `models/mhd.py` | `prim_vars.py` (MHD parts) | MHD B/p/temperature family. |
| `models/plasma_params.py` | `params.py` | `magB, vt, vA, omegaC, omegaP, d, lambdaD, rho, beta`. Physical constants from `scipy.constants` — never re-type the old `gk/gkeyll_const.py` values. Where old and CODATA constants differ in trailing digits, use scipy and note the delta in your report. |
| `models/energetics.py` | `energetics.py`, `accumulate_current.py` | energy balance terms, current accumulation. |
| `models/rotations.py` | `parrotate.py`, `perprotate.py` | vector rotation par/perp to B; uses `numerics.rotation_matrix`. |
| `models/frame.py` | `transform_frame.py` | distribution-function frame transform. |
| `models/laguerre.py` | `laguerre_compose.py` | distf reconstruction from Laguerre moments. |

`models/__init__.py` re-exports; no defs.

Naming: keep the old public function names (`get_density`, `get_p_par`, …)
so ported tests and the layer-08 verbs map 1:1. Signatures change only as the
principles require (arrays in, keyword-only options, no dual input).

## Porting discipline

Copy the math verbatim. These are the most numerics-dense files in the old
tree, with `tests_bak` corpora totaling ~120 tests — the tests are your
safety net; port them FIRST per module (red), then port the module (green).

## Tests

`tests/test_models_<module>.py` — port `tests_bak/test_tools_prim_vars.py`
(78), `test_tools_pressure_diagnostics.py` (28), `test_tools_params.py` (17),
and the moments-relevant assertions from `test_ops_wave4.py`/`test_ops_wave5.py`
(the array-level parts; the verb-level parts wait for layer 08). Add analytic
cases: a fabricated Maxwellian's moments recover its n/u/T, agyrotropy of an
isotropic tensor is 0, plasma params for hydrogen at textbook n/T match
handbook values to the constant's precision.

## Definition of done

1. Full suite green; architecture tests pass (`models` imports at most
   `core`/`numerics` — with this file authorizing the numerics edge; ideally
   arrays-only modules import numerics/numpy/scipy only).
2. `--cov=postgkyl.models` ≥ 95%.
3. Report: function inventory per module (old name → new home), constant
   deltas vs old gkeyll_const, ported-test tally, coverage, pytest summary.
