# Layer 11 — api (the fluent surface)

## Mission

Give every **core verb** from layers 07–09 a fluent method on `api.GData`,
add the fluent group container, and true up the facade.

Boundary (layer 10 restructure): the equation-specific functions now live in
`diagnostics/`, which sits ABOVE `api` — they are deliberately NOT fluent
methods and must not appear on `GData`. The fluent surface is equation-blind.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. `CLAUDE.md` — "api" section and "the trick that removes the cycle"
3. `src/postgkyl/api/{gdata.py,load.py}` — the existing pattern: every method
   is a one-line delegation `def interp(self, **kw): return ops.interpolate(self, **kw)`
4. Layer 05's report — the deferred DatasetGroup verb-method worklist
5. `ops/__init__.py` — the full verb inventory you must surface

## The work

1. **`api/gdata.py`** — one method per verb, one line each, keyword pass-
   through, names matching the CLI vocabulary: `fft, magsq, relchange, mask,
   collect (classmethod or module fn — see below), grid, val2coord,
   extract_input, fit, growth, differentiate, ev (module-level, multi-dataset),
   map, animate (if layer 09 added the verb)`. No physics methods: `euler`,
   `tenmoment`, `agyro`, `energetics`, etc. moved to `diagnostics/` in layer
   10 and are called as free functions there. Multi-dataset verbs (`collect`,
   `ev`, `relchange`) are module-level functions in `api/` (they don't have a
   single self) — put them in `api/verbs.py`, re-export from `api/__init__.py`.
2. **`api/group.py`** — fluent group over `core.DatasetGroup`: applying a verb
   method maps it over members and returns a new fluent group (layer 05's
   deferred worklist tells you which methods the old class had). Implement it
   WITHOUT copying method bodies: a small `__getattr__`-based delegation that
   forwards to the members' fluent methods is acceptable here IF you document
   its contract (every GData verb is available; returns group; terminal verbs
   return a list) — otherwise write the one-liners explicitly. Choose one and
   justify in the report.
3. **Facade** (`src/postgkyl/__init__.py`) — re-export any new public names
   (`load`, `GData`, group, module-level verbs, `plot`, `write`, `info`, …).
   Pure re-export — the AST test enforces it.

## Tests

`tests/test_api_fluent.py`:
- Every fluent method exists and returns the caller's class (subclass
  propagation: define `class MyData(GData)` in the test, verify chains stay
  `MyData` — the `_result` contract).
- One end-to-end chain per verb family on real test data:
  `pg.load(...).interp().magsq().plot()` etc. (Agg backend).
- Group chains: load several generated frames → group → `.interp().sel(...)`
  maps over members; terminal verbs behave per the documented contract.
- Facade: `import postgkyl as pg`; every documented name resolves;
  `pg.__all__` (if present) is consistent.
- Keyword pass-through: a kwarg given to the fluent method reaches the verb
  (spot-check 3 verbs with distinctive kwargs).

## Definition of done

1. Full suite green; architecture tests pass (api sits above ops/render — no
   new edges needed).
2. `--cov=postgkyl.api` ≥ 95%.
3. Report: method inventory (verb → fluent spelling), the group delegation
   decision and its contract, facade additions, coverage, pytest summary.
