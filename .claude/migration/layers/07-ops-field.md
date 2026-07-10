# Layer 07 — ops (wave A): field-domain verbs

## Mission

Port the field-domain verbs onto the new verb contract. One module per verb,
re-exported from `ops/__init__.py`.

## The verb contract (copy it from the existing exemplars)

Read `src/postgkyl/ops/{select.py,interpolate.py,integrate.py,arithmetic.py}`
first — they define the house pattern:

```python
def verb(data: GDataState, *, ..., inplace: bool = False, tag=None, label=None) -> GDataState
```

- Results funnel through `data._result(...)` so the caller's concrete class
  (GData) survives.
- Field-domain verbs refuse gkyl-backed modal data with the standard
  ".interp() first" error — copy the exact guard style from `ops/select.py`.
- Verbs unwrap (`grid`, `values`, `ctx`) and delegate math to
  `numerics/` — they do not reimplement it.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. The exemplars above; what layer 02 landed in `numerics/` (its report/tests)
3. `.claude/migration/notes/differentiate-decision.md` (written by layer 03)
4. Each old verb before porting: `src_bak/postgkyl/ops/<name>.py` — the old
   contract is nearly identical (inplace/tag/label already exist there);
   what changes is imports, math delegation, and the modal guard.

## Verb list (source → target, all in `src/postgkyl/ops/`)

| Old | New module | Notes |
|---|---|---|
| `ops/fft.py` | `fft.py` | Delegates to `numerics.fft`; psd/iso options. Grid becomes frequency axes — preserve that behavior exactly. |
| `ops/magsq.py` | `magsq.py` | → `numerics.mag_sq`. |
| `ops/relchange.py` | `relchange.py` | Two-dataset verb: `relchange(data0, data, *, comp=None, ...)`. |
| `ops/mask.py` | `mask.py` | Mask from a second dataset/file → NaN masking of values. |
| `ops/collect.py` | `collect.py` | Many datasets → one with a new leading (time/param) axis. Takes a sequence of GDataState; use `core.flatten_datasets`. |
| `ops/grid.py` | `grid.py` | Replace/scale grid arrays; validate shapes against `num_cells`. |
| `ops/val2coord.py` | `val2coord.py` | Component values become coordinates (for trajectory-style data). |
| `ops/extract_input.py` | `extract_input.py` | Base64-decode the embedded input file from ctx; returns a string — this verb is terminal (does not return GDataState); keep the old return type and document it. |
| `ops/fit.py` | `fit.py` | Delegates to `numerics.fit`; the nodal→cell-centered grid prep now comes from `numerics.grid_centering`. |
| `ops/growth.py` | `growth.py` | Delegates to `numerics.growth`; operates on dynvector-style data (time series). |
| `ops/differentiate.py` | `differentiate.py` | Follow the layer-03 decision document EXACTLY. If it says deferred/np.gradient: implement the field-domain gradient with the doc's stated caveats in the docstring. If it says `dg/deriv.py` exists: the verb wraps it (modal in, field out, like interpolate). |
| `ops/ev.py` | `ev.py` | The RPN evaluator: `ev(expr, *datasets, ...)`. Token table from `numerics.ev_ops`. Resolve any `NotImplementedError` placeholders layer 02 left IF the capability now exists in numerics/dg; otherwise keep them raising with a clear message and list them. Grammar (tokens, `f[0]`-style dataset refs) stays byte-compatible with the old CLI usage. |

Skip `dg_local_poly` (superseded; PLAN.md deferred list). `map` and the
physics verbs are layer 08.

Update `ops/__init__.py` re-exports (re-export only).

## Tests

`tests/test_ops_<verb>.py` per verb (small ones may share
`tests/test_ops_field.py`). Port the relevant cases from
`tests_bak/test_ops.py` (38 tests). Every verb gets: happy path on a real
loaded+interpolated dataset from `tests/test_data/`, the modal-refusal guard,
`inplace=True` vs new-object semantics, `tag`/`label` propagation, and the
verb's own edge cases (empty selection, single-cell axis, NaN inputs where
meaningful). `ev`: expression parity with direct verb calls
(`ev('f[0] f[1] +', a, b)` equals `a + b`).

## Definition of done

1. Full suite green; architecture tests pass.
2. `--cov` ≥ 90% for the new ops modules.
3. Report: verb inventory with old→new behavioral notes (should be "identical"
   everywhere except documented differentiate), remaining ev placeholders,
   coverage, pytest summary.
