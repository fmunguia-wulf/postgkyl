# Layer 05 — core (DatasetGroup) — review

Scope reviewed: the working-tree diff at review time —
`src/postgkyl/core/group.py` (new), `tests/test_core_group.py` (new),
`src/postgkyl/core/__init__.py` (export added), `src/postgkyl/core/collection.py`
(`flatten_datasets` generalized to accept any iterable, with a `str`/`bytes`
guard) — against `src_bak/postgkyl/group.py` and `tests_bak/test_group.py`.

## Doctrine adherence

- **0. Locality of reasoning.** Mostly adheres. One local friction: `group.py`
  imports its sibling core modules with absolute paths
  (`core/group.py:16-17`, `from postgkyl.core.collection import flatten_datasets`
  / `from postgkyl.core.state import GDataState`) while `collection.py` imports
  its sibling with a relative import (`from .state import GDataState`,
  `core/collection.py:11`). A reader has to notice two import conventions
  coexisting in the same package with no stated reason (see C2).
- **I. Data is inert. Functions transform.** Adheres. `DatasetGroup` follows
  the same precedent as `GDataState`: a state-holding class with no verb
  methods. `with_`/`__and__` return new groups rather than mutating (verified
  by `test_with_does_not_mutate`, `tests/test_core_group.py:98-101`).
- **II. Make illegal states unrepresentable.** Adheres. The constructor
  flattens then rejects any non-`GDataState` member with `TypeError`
  (`core/group.py:43-47`), checked by `test_rejects_non_gdata`.
- **III. A function is one idea.** Adheres. Each method (`__iter__`, `__len__`,
  `__getitem__`, `with_`, `__repr__`) does exactly one thing.
- **IV. The signature tells the whole truth.** Mostly adheres — the `Raises`
  and `Args` docstrings are honest — but weakened by missing type annotations
  (see C1): the truth lives in prose, not in the signature, for `__init__` and
  `__getitem__`.
- **V. Every fact has one home.** Adheres, and this is the layer's best-kept
  discipline. `group.py` reuses `flatten_datasets` rather than re-implementing
  `_flatten` (`core/group.py:16`, `core/group.py:42`); the reconciliation
  between `src_bak`'s `_flatten` and `flatten_datasets` is done *in*
  `collection.py` (generalizing the recursion to any iterable, adding a
  `str`/`bytes` guard) and documented there instead of being silently
  duplicated.
- **VI. Separate what from how.** Adheres. `group.py` imports nothing beyond
  `core.collection`/`core.state`; every verb-shaped member of the old class
  (`__getattr__` broadcasting, `plot`, `info`, `animate`, `plotly_animate`,
  `collect`, `ev`) is left out and named explicitly in the new test file's
  module docstring (`tests/test_core_group.py:1-9`) as layer-10 debt.
- **VII. Notation is execution; lowering is transliteration.** Not applicable
  — no spec/math layer involved in this layer.
- **VIII. Earn your abstractions.** Adheres. This is a straight, non-premature
  port of an abstraction already used upstream (`GData.with_` in `src_bak`
  already depended on it); no new complexity added beyond what `src_bak`
  had.
- **IX. An abstraction is a contract.** Adheres. The class docstring
  (`core/group.py:20-27`) states the guarantees a client may rely on: ordering
  preserved, members keep their own identity, flattening semantics, and the
  `TypeError` contract on construction — matched by tests.
- **X. Trust the most formal thing first.** Partial. Tests are thorough
  (100% line coverage, see below), but the most formal layer available here —
  type hints — is incomplete on two public methods (C1), so the tests are
  carrying weight the type checker could have carried more cheaply.

## Principles adherence

- **1. Absolute imports spelled `postgkyl`.** Adheres on content (no
  `postgkeyll` leftovers), but see C2 for the relative-vs-absolute style
  inconsistency within the same package that principle 1 calls out as
  "preferred."
- **2. Respect the layer DAG.** Adheres. `core`'s `_ALLOWED` edges
  (`{"io", "ffi"}`) are untouched; `group.py` needs neither and imports
  neither. Verified: `test_import_contract_no_violations`,
  `test_import_graph_is_acyclic` pass.
- **5. `__init__.py` re-exports only.** Adheres — `core/__init__.py` only adds
  `from .group import DatasetGroup` to `__all__`.
- **6. Type-annotate every public function.** Violates — see C1
  (`core/group.py:29`, `core/group.py:58`).
- **8. No mutable default arguments.** Adheres — `datasets=()` defaults to an
  immutable tuple.
- **10. Raise, don't print-and-continue.** Adheres — `TypeError` with the
  offending value's type in the message (`core/group.py:45-46`).
- **11. Pure core, effects at the edges.** Adheres — no I/O, no matplotlib,
  no printing in `group.py`.
- **14. NumPy/collection discipline; document intentional copies.** Adheres —
  `datasets` property is documented as a deliberate shallow defensive copy
  (`core/group.py:78-83`), verified by `test_datasets_is_defensive_copy`.
- **15. Docstrings.** Adheres — Args/Returns/Raises present and match house
  style.
- **16. Comments state constraints, not narration.** Adheres — no changelog
  comments found in the diff.
- **17. One test file per module, ~100% coverage.** Adheres —
  `tests/test_core_group.py`; measured 100% on `core/group.py` (below).
- **18. Tests assert values, not just shapes.** Adheres for this
  non-numerical layer — assertions check identity (`g[0] is a`), membership
  count, and exact `repr` strings, which is the appropriate granularity here.
- **19. Tests independent/deterministic.** Adheres — no RNG, no network, no
  ordering dependence.
- **20. Architecture tests sacred.** Adheres — all four pass (see Coverage
  section for the run).
- **21. Copy liberally, then adapt.** Adheres, with one improvement worth
  crediting: `src_bak`'s `_flatten` recurses into *any* `hasattr(x,
  "__iter__")` object with no string guard, which means passing a plain
  string into `_flatten` would recurse into `_flatten("a")` and loop forever
  (a single-character string re-iterates to itself). The new
  `flatten_datasets` fixes this latent bug with an explicit `str`/`bytes`
  passthrough (`core/collection.py:30-31`) — a corrected, not silently
  changed, numerical/structural behavior, and it is documented in the
  docstring.
- **23. Never edit `src_bak`/`tests_bak`.** Adheres — confirmed unmodified.
- **24. Leave the tree green.** Adheres — 601 passed (below).

## Criticisms

**C1 (minor — consistency / principle 6 violation).**
`src/postgkyl/core/group.py:29` (`def __init__(self, datasets=()):`) and
`src/postgkyl/core/group.py:58` (`def __getitem__(self, index):`) have no
type annotations on their parameters, unlike every other constructor and
dunder in this layer and its neighbors (`core/state.py:34`
`def __init__(self, file_name: str = "", *, ctx: dict | None = None, ...)`,
and every reader `__init__` under `io/`). A future maintainer or a type
checker gets no signal from the signature about what `datasets`/`index` may
be; the only source of truth is the docstring prose, which can drift from the
implementation without anything catching it (doctrine V: two sources, zero of
truth). Fix: annotate as
`def __init__(self, datasets: "GDataState | Iterable" = ()) -> None:` and
`def __getitem__(self, index: int | slice) -> "GDataState | DatasetGroup":`,
matching the pattern already used for `with_`'s return type on the same
class.

**C2 (minor — style inconsistency).**
`src/postgkyl/core/group.py:16-17` imports its sibling core modules
absolutely (`from postgkyl.core.collection import flatten_datasets`,
`from postgkyl.core.state import GDataState`), while
`src/postgkyl/core/collection.py:11` imports its sibling relatively
(`from .state import GDataState`). `PYTHON_PRINCIPLES.md` §1 states relative
imports are "fine and preferred inside the package." Cost: a reader
skimming `core/` sees two conventions and has no way to know locally which
one is canonical for new code in this package. Fix: change `group.py`'s two
imports to `from .collection import flatten_datasets` /
`from .state import GDataState`.

Both criticisms are cosmetic; neither affects correctness, coverage, or the
architecture tests. No behavioral divergence from `src_bak`'s state-reading
surface was found; the one intentional behavior change (generalizing
`_flatten`'s recursion and guarding strings) is a documented bug fix, not a
silent change.

## Coverage

Measured with `coverage run` (pytest-cov's `--cov` flag crashes on this repo
with `ImportError: cannot load module more than once per process`, the same
compiled-extension re-import issue noted in the 04-io review; worked around by
driving `coverage` directly):

```
PYTHONPATH=src python -m coverage run -m pytest tests/ -q
........................................................................ [ 11%]
........................................................................ [ 23%]
........................................................................ [ 35%]
........................................................................ [ 47%]
........................................................................ [ 59%]
........................................................................ [ 71%]
........................................................................ [ 83%]
.........................                                                [100%]
601 passed in 4.21s

PYTHONPATH=src python -m coverage report --include="*/postgkyl/core/*" -m
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
src/postgkyl/core/__init__.py         4      0   100%
src/postgkyl/core/collection.py      13      0   100%
src/postgkyl/core/group.py           25      0   100%
src/postgkyl/core/state.py          202      0   100%
---------------------------------------------------------------
TOTAL                               244      0   100%
```

100% line coverage on every module in `core/`, well above the layer's 95%
floor; no uncovered regions, so there are no coverage-gap justifications to
adjudicate. The one line-level nuance — `collection.py`'s `isinstance(it,
(str, bytes))` check is exercised only by a string ("x", in
`tests/test_coverage_container.py:189`, a pre-existing test carried over from
the io layer's coverage push), not a `bytes` value — is immaterial: it is a
single combined `isinstance` check, so the `bytes` half of the tuple adds no
additional line or branch that coverage tooling here would flag, and `pytest`
is not run with `--cov-branch`.

Architecture tests, run separately to confirm they still hold under this
layer's new export and import:

```
PYTHONPATH=src python -m pytest tests/test_postgkyl.py -k "import_contract or acyclic or foreign_floor or facade" -q
.....                                                                    [100%]
5 passed, 27 deselected in 2.71s
```

## Verdict

**PASS (fixer optional).** The layer does exactly what its instruction file
asked: `DatasetGroup` is ported as a verb-less container reusing
`flatten_datasets` (no second flatten implementation), every verb-shaped
member of the old class is correctly left out and enumerated for layer 10
(`__getattr__` broadcasting, `plot`, `info`, `animate`, `plotly_animate`,
`collect`, `ev`), the required additional tests (empty group, group of one,
heterogeneous member types, non-mutating `with_`) are present, the full suite
is green (601 passed), coverage on `core/` is 100%, and all four sacred
architecture tests pass with no new DAG edge needed. The only findings are
two cosmetic consistency nits (C1: two untyped signatures on an otherwise
fully-typed class; C2: absolute imports where a relative import would match
the sibling module's style) — a fixer pass is welcome to tidy them but not
required to accept this layer.
