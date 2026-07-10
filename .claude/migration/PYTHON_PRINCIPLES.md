# Good Python — writing principles for this migration

These are the concrete Python-level rules every migration agent follows. They
are the doctrine (`.claude/DOCTRINE.md`) projected onto Python. When a rule here
and the doctrine seem to conflict, the doctrine wins.

## Modules and imports

1. **Absolute imports within the package, spelled `postgkyl`.** The old tree
   imports from `postgkeyll` (double-e) — that package does not exist. Every
   line copied from `src_bak/` must have its imports rewritten. Relative
   imports (`from ..ffi import basis`) are fine and preferred inside the
   package.
2. **Respect the layer DAG.** Before adding any import, check the `_ALLOWED`
   edge map in `tests/test_postgkyl.py` (`test_import_contract_no_violations`).
   If your layer needs a new edge, that is a design decision — stop and record
   it in your report; do not silently add it to `_ALLOWED` unless your layer
   instruction file explicitly authorizes that edge.
3. **Optional dependencies are guarded at import time, once, at module top.**
   Pattern:
   ```python
   try:
       import adios2
   except ImportError:
       adios2 = None
   ```
   and the entry point raises a clear `ImportError("pip install postgkyl[adios]")`
   when used without it. Hard deps (numpy, scipy, matplotlib, msgpack, tables,
   plotly, pyvista, click) need no guard — see `pyproject.toml`.
4. **No `typer`, anywhere.** The new CLI is Click. No `ctypes`, anywhere — the
   only foreign doorway is `ffi/` (a test enforces both).
5. **`__init__.py` files re-export; they do not define.** Functions and classes
   live in named modules.

## Functions and signatures

6. **Type-annotate every public function** — parameters and return. Use modern
   syntax: `list[np.ndarray]`, `str | None`, `from __future__ import
   annotations` at module top.
7. **Keyword-only options.** Everything after the data arguments is
   keyword-only: `def fft(data, *, psd=False, iso=False)`. Booleans are never
   positional.
8. **No mutable default arguments.** Default to `None`, resolve inside.
9. **Take arrays, return arrays** in `numerics/` and pure helpers — never a
   `GData`. Verbs in `ops/` take `GDataState` and funnel results through
   `_result(...)`. Do not port the old dual-input `input_parser` pattern
   (functions that accept "GData OR tuple") — that is two functions wearing one
   signature; the GData unwrapping happens in the `ops/` verb, the math takes
   arrays.
10. **Raise, don't print-and-continue.** Errors are `raise ValueError(...)` /
    `TypeError(...)` with a message that names the offending value and the fix
    (follow the existing ".interp() first" style). Never `typer.secho` + return
    None; never bare `except:`.
11. **Pure core, effects at the edges.** File reads, matplotlib, and printing
    happen only in the layers that own them (io, render, cli). A math function
    that today pops up an interactive matplotlib picker gets split: math stays,
    the picker moves to the layer that owns interaction.

## Data

12. **Frozen records for structured data.** Multi-field return values are
    `@dataclass(frozen=True)` or `NamedTuple`, not dicts with magic keys and
    not tuples longer than 2. Existing `ctx` dict usage in `GDataState` is
    grandfathered — do not extend it with new magic keys without noting it in
    your report.
13. **Constants have one home.** Physical constants come from
    `scipy.constants` (they are CODATA facts, not Gkeyll facts) — do not
    re-type the old `gk/gkeyll_const.py` table. Gkeyll enum orderings are
    Gkeyll facts; if you must mirror one, put it in a single module with a
    comment naming the exact Gkeyll header it mirrors, and a test.
14. **NumPy discipline:** no silent copies of large arrays (document when a
    copy is intentional); use `np.asarray` only at API boundaries; preserve
    dtype; never compare floats with `==` in tests — use
    `np.testing.assert_allclose` with an explicit tolerance.

## Docstrings and comments

15. **Every public function gets a docstring**: one summary line, then Args /
    Returns / Raises, matching the style already in `src/postgkyl/ops/`.
    Document edge cases the code handles (empty selection, 1-cell axis, ghost
    cells, non-tensor node sets).
16. **Comments state constraints, not narration.** "why", never "what". No
    changelog comments ("ported from src_bak", "fixed review issue") — git
    holds history.

## Tests

17. **One test file per module** under `tests/`, named `test_<layer>_<module>.py`.
    Port the relevant `tests_bak/` tests as a starting corpus, then add what
    they miss. Aim for ~100% line coverage of the layer's new modules
    (`pytest --cov=postgkyl.<layer> --cov-report=term-missing`); justified
    misses (defensive unreachable branches, optional-dep fallbacks that need
    an uninstalled package) are acceptable and must be listed in your report.
18. **Tests assert values, not just shapes.** For math, test against an
    analytic case (a polynomial the basis reproduces exactly, a known FFT of a
    sine, a fabricated Maxwellian). Golden numbers copied from a previous run
    are a last resort and must be labeled as such.
19. **Tests are independent and deterministic**: seed every RNG
    (`np.random.default_rng(42)`), no ordering dependence, no network, write
    only to `tmp_path`. Gate anything needing the compiled shim with the
    existing `ffi.available()` skip pattern from `tests/test_postgkyl.py`.
20. **The architecture tests are sacred.** `test_facade_is_pure_reexport`,
    `test_import_contract_no_violations`, `test_foreign_floor_confined_to_ffi`,
    `test_import_graph_is_acyclic` must pass after every layer. If one fails,
    your change is wrong — fix the change, not the test (unless your layer
    instruction file explicitly authorizes a new edge).

## Porting rules

21. **Copy liberally, then adapt.** The old code is battle-tested numerics —
    prefer copying its math verbatim over rewriting it. What you change:
    imports, layer boundaries, signatures (per rules above), error handling,
    dead branches. What you never change silently: numerical behavior. If a
    result differs from the old implementation, that is either a documented
    intentional change or a bug.
22. **Do not port the obsolete.** `computeInterpolationMatrices`,
    `computeDerivativeMatrices`, `modalDG/`, `tools/gkeyll_dg_ops.py`,
    `_gkylsoft_path.py`, and the Typer stack are superseded — their
    *capabilities* are re-provided via `ffi/`; their code is not copied.
23. **Never edit `src_bak/` or `tests_bak/`** — they are the read-only
    reference. Never stage or commit `pygkyl/` if present.
24. **Leave the tree green.** `PYTHONPATH=src python -m pytest tests/ -q` must
    pass at the end of your task. If you cannot make something work, ship the
    subset that works, delete the half-built remainder, and report exactly
    what was cut and why.
