# Layer 05 — core (the container): DatasetGroup

## Mission

Port the old `DatasetGroup` into `core/group.py` as a verb-less container,
consistent with how `GDataState` relates to `GData`.

## Read first

1. `.claude/DOCTRINE.md` (esp. I — data is inert), `.claude/migration/PYTHON_PRINCIPLES.md`
2. `src/postgkyl/core/{state.py,collection.py}` — the house style for a
   verb-less container; `flatten_datasets` already came from the old group
   module.
3. Source: `src_bak/postgkyl/group.py` (`DatasetGroup`, `_flatten`).
4. Old tests: `tests_bak/test_group.py` (18 tests) — the behavioral contract.

## The port

- `src/postgkyl/core/group.py` — `class DatasetGroup`: holds an ordered
  collection of `GDataState` (or subclass) items; indexing, iteration, `len`,
  labels/tags lookup, `__repr__` — every **state-reading** member of the old
  class.
- **Verb-shaped members stay behind.** If the old class has methods that
  compute or plot (anything that would call an `ops` verb or matplotlib),
  do NOT port them here — they belong to the api layer (layer 10 adds a
  fluent group that maps verbs over members). List every deferred method by
  name in your report so layer 10 has an exact worklist.
- Reuse `flatten_datasets` from `core/collection.py` — do not create a second
  flatten (doctrine V: one home per fact). If the old `_flatten` differs from
  `flatten_datasets`, reconcile: extend the one in `collection.py` and note
  the difference.
- Imports: `core` may import `io`, `ffi`, `numerics` only (check `_ALLOWED`).
  A group of datasets should need nothing beyond typing and `collection`.
- Export from `core/__init__.py`.

## Tests

`tests/test_core_group.py` — port all 18 `tests_bak/test_group.py` tests that
concern state (construction, indexing, iteration, flatten of nested inputs,
labels, repr), adapting imports and dropping the ones that exercise deferred
verb methods (list those in the report as layer-10 test debt). Add: empty
group behavior, heterogeneous member types (GDataState + GData subclass),
group of one.

## Definition of done

1. Full suite green; architecture tests pass.
2. `--cov=postgkyl.core` ≥ 95%.
3. Report: deferred verb-method worklist for layer 10, any `_flatten` vs
   `flatten_datasets` reconciliation, coverage, pytest summary.
