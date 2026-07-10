# Layer 04 — io — review

Scope: the working-tree diff at the time of review — new files
`src/postgkyl/io/{gkyl_adios_reader.py,gkyl_h5_reader.py,flash_h5_reader.py}`
and `tests/test_io_{adios,h5,mapping,writer}.py`; modified
`src/postgkyl/io/{__init__.py,mapping.py,writer.py}` and
`tests/test_postgkyl.py` (`_ALLOWED` edge). `gkyl_reader.py`/`gkyl_c_reader.py`
are untouched and out of scope.

## Doctrine adherence

- **0. Locality of reasoning** — Adheres. Each reader is self-contained; a
  reader can be read and understood without the other four.
- **I. Data is inert. Functions transform.** — Adheres, with a caveat carried
  from earlier layers, not introduced here: the reader classes
  (`GkylAdiosReader`, `GkylH5Reader`, `FlashH5Reader`) are stateful objects
  with `is_compatible()`/`preload()`/`load()` mutating `self.lower`/`self.cells`/
  etc. This mirrors the pre-existing `GkylReader`/`GkylCReader` contract
  (`src/postgkyl/io/gkyl_reader.py`, `gkyl_c_reader.py`, not part of this
  diff) exactly — a new reader breaking that pattern would itself be a
  layer-DAG/consistency violation. Judged against the established registry
  contract, this is faithful reuse, not a new I-violation.
- **II. Illegal states unrepresentable** — Adheres. `ctx` stays a plain dict
  (grandfathered, PYTHON_PRINCIPLES §12); readers raise (`ValueError`,
  `TypeError`) rather than returning sentinel/partial states — e.g.
  `flash_h5_reader.py:111-115` refuses to `load()` without `var_name`.
- **III. A function is one idea** — Mostly adheres. One violation:
  `writer.py:23-25` — `write()`'s `var_name` parameter is accepted but never
  used by any branch (bp/adios writing, the one format that used it, was not
  ported); see C2.
- **IV. The signature tells the whole truth** — Same caveat as III: `var_name`
  is present in the signature but inert, so the signature overstates what the
  function needs (see C2). Everything else is honest: `is_compatible()`
  never raises on a bad path (`gkyl_adios_reader.py:97-98`,
  `gkyl_h5_reader.py:40-41`, `flash_h5_reader.py:54-55` all narrow their
  `except` to the specific I/O exceptions, replacing `src_bak`'s bare
  `except:`).
- **V. Every fact has one home** — Adheres. Uniform-grid construction lives
  only in `mapping.uniform_grid`/`adjust_for_ghost_cells`, reused by all three
  new readers instead of re-typing `linspace` (`gkyl_h5_reader.py:105-106`,
  `flash_h5_reader.py:124-125`, `gkyl_adios_reader.py:210`). `idx_parser` is
  reused from `numerics` rather than re-implemented in `io` — the one new
  cross-layer edge is deliberate and recorded once, in
  `tests/test_postgkyl.py:391-397`.
- **VI. Separate what from how** — Adheres. Readers only produce
  `(grid, values)` + `ctx`; no `core`/`ops` import anywhere in the new files
  (checked by grep and by the passing `test_import_contract_no_violations`).
- **VII. Notation is execution; lowering is transliteration** — Not
  applicable; this layer is byte-level I/O plumbing, not a spec/execution
  pair.
- **VIII. Earn your abstractions** — Adheres. The five-reader registry with a
  shared `is_compatible/preload/load` shape is justified by five real usages;
  reusing `numerics.idx_parser` for the second real caller ADIOS partial-load
  is the "earn it at the second use" case textbook.
- **IX. An abstraction is a contract** — Adheres. Every reader honors the same
  `ctx` vocabulary contract for the keys it can supply (`cells`/`lower`/
  `upper`/`num_comps`/`grid_type`, plus `poly_order`/`basis_type`/`is_modal`
  where applicable); `core/state.py` consumes `ctx.get("representation",
  "modal")` with a default, so the legacy field-only readers correctly never
  need to set it.
- **X. Trust the most formal thing first** — Adheres for what can be typed;
  the bulk of the correctness burden here is genuinely only testable (byte
  layout, HDF5 dataset paths), and the test suite exercises reader and
  round-trip behavior directly rather than relying on comments.

## Principles adherence (PYTHON_PRINCIPLES.md)

- §1 absolute imports — Adheres (`from postgkyl.numerics import idx_parser`,
  `from . import mapping`; no `postgkeyll`).
- §2 layer DAG — Adheres. The new `io -> numerics` edge is added
  deliberately with a comment in `tests/test_postgkyl.py:394-397`, and is
  provably safe: `numerics/__init__.py` imports only `numpy`/`scipy` (zero
  internal edges), so `io -> numerics` cannot create a cycle.
- §3 optional deps guarded once at module top — Adheres:
  `gkyl_adios_reader.py:17-21`.
- §4 no typer/ctypes — Adheres: `cli_mode`/`typer.prompt` from
  `src_bak`'s `_load_frame` were dropped, matching the "effects at the edges"
  rule (the picker/prompt belongs to a future CLI layer, not the reader).
- §5 `__init__.py` re-exports, does not define — `io/__init__.py` still
  defines `read()` inline; **pre-existing**, not introduced by this diff
  (confirmed via `git show HEAD~1:src/postgkyl/io/__init__.py`, `read()` was
  already there before this layer). Not counted against this layer.
- §6/7/8 type hints, keyword-only options, no mutable defaults — Adheres.
  `GkylAdiosReader`'s `axes` default is a tuple (immutable), not a list/dict.
- §9 pure math takes arrays — N/A for readers/writer (I/O, not math), but
  `writer.py` correctly calls `numerics.nodal_to_cell_centered_grid` on plain
  arrays, never on a `GData`.
- §10 raise, don't print — Adheres; §11 effects at the edges — Adheres (file
  I/O only, no plotting/printing in these modules).
- §12 frozen records / grandfathered ctx — Adheres.
- §14 NumPy discipline — Adheres; `np.testing.assert_allclose` used
  throughout the new tests, no float `==`.
- §17 ~100% coverage, justified misses listed — Mostly adheres (99% overall,
  ≥90% required); **one misses is not actually justified** — see C1 and the
  Coverage section.
- §18 tests assert values — Adheres:
  `test_io_mapping.py::test_c2p_grid_splits_packed_node_axis_by_hand` is a
  hand-computed case, `test_io_h5.py` builds byte-exact fixtures and checks
  values, not just shapes.
- §21 copy liberally, never change numerics silently — Mostly adheres; one
  undocumented option drop, see C3.
- §22/23/24 — Adhere: no obsolete modules ported, `src_bak`/`tests_bak`
  untouched, full suite green (574 passed).

## Criticisms

**C1 (moderate — test-coverage gap on a reachable path, not a bug).**
`src/postgkyl/io/gkyl_adios_reader.py:118` and `:129-133` — the
`else: raise TypeError(...)` branches in `_create_offset_count` are reachable,
not defensive-unreachable: `numerics.idx_parser` can return a *tuple* for a
comma-separated selector (`idx_parser("1,2,3", arr)` → `(1, 2, 3)`, verified
interactively), which is neither `int` nor `slice`, so passing e.g.
`axes=("1,2,3", None, ...)` to `GkylAdiosReader` hits this raise today,
untested. This is the same behavior `src_bak` had (not a regression), but
`PYTHON_PRINCIPLES` §17's "justified miss" carve-out is for genuinely
unreachable defensive branches — this one is reachable by a plausible (if
unusual) partial-load selector. Fix: add
`pytest.raises(TypeError)` tests driving a comma-list `axes`/`comp` value
through `GkylAdiosReader.load()`, or reject tuple-returning selectors with a
clearer message one level up before they reach `_create_offset_count`.

**C2 (minor — dead parameter).**
`src/postgkyl/io/writer.py:23-25,33` — `write()`'s `var_name: str =
"CartGridField"` parameter is accepted but exercised by no code path: the
one format that used it in `src_bak` (`extension="bp"`, ADIOS write) was not
ported, and `gkyl`/`txt`/`npy`/`vtk` never read `var_name`. The docstring is
honest ("unused placeholder kept for interface symmetry") but this still
means the signature promises something the function does not use — a minor
III/IV tension. Fix: drop the parameter (breaking `write()`'s call sites is
cheap to grep-check now) or wire it into the one place a variable name is
meaningful today (the vtk point-data array name, currently hardcoded
`"f_raw"` at `writer.py:130`).

**C3 (minor — undocumented option drop).**
`src_bak/postgkyl/data/write.py:39-40,195-198` had a `norm_axes: bool = False`
option that rescaled the vtk output's X/Y/Z to `[-1, 1]` (called out in
`src_bak` as a VR-viewer convenience). The ported `_write_vtk` in
`src/postgkyl/io/writer.py:105-132` drops it silently — the layer instruction
table only says "add vtk … port the series-file updater," so this is
plausibly in-scope-but-unmentioned rather than a mandated port, but
PYTHON_PRINCIPLES §21 requires dropped behavior to be a *documented*
intentional change, and no such note exists in the diff (no code comment, no
report file found under `.claude/migration/`). Low impact — normalization is
recoverable later as a render-layer concern — but it should be a one-line
note either in the module docstring or the layer's report.

**C4 (very minor — weaker input-validation message).**
`src_bak/postgkyl/data/write.py:58-61` rejected a non-string `out_name` with
`TypeError("'out_name' must be a string")`. The ported `write()`
(`src/postgkyl/io/writer.py:38-44`) has no such check, so a non-string
`out_name` now fails later with a bare `AttributeError` from `.split(".")`
instead of a clear message naming the offending value (PYTHON_PRINCIPLES
§10). Every current call site passes a string, so this is latent, not
exercised by any test or caller today.

No correctness or numerical-divergence issues were found: the HDF5/FLASH/
ADIOS math (block-reassembly indexing, `_create_offset_count`
offset/count arithmetic, natural-sort concatenation, ghost-cell
adjustment) is copied verbatim from `src_bak` modulo the changes explicitly
licensed by the layer instructions and PYTHON_PRINCIPLES (import rewrites,
exception narrowing, dropped `typer`/`cli_mode`, dropped "mapped" grid-type
branch — verified dead code today since no reader in the current tree ever
sets `ctx["grid_type"] = "mapped"`).

## Coverage

Measured with `coverage run` (pytest-cov's `--cov` flag reproducibly crashes
in this environment with `ImportError: cannot load module more than once per
process` inside `numpy/_core`, unrelated to this layer's code — same crash
occurs collecting `tests/test_postgkyl.py`, which imports nothing from `io`
before failing; worked around by driving `coverage` directly):

```
Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/postgkyl/io/__init__.py               19      0   100%
src/postgkyl/io/flash_h5_reader.py        54      0   100%
src/postgkyl/io/gkyl_adios_reader.py     161      8    95%   19-20, 66, 118, 129-133
src/postgkyl/io/gkyl_c_reader.py          40      0   100%
src/postgkyl/io/gkyl_h5_reader.py         53      0   100%
src/postgkyl/io/gkyl_reader.py           249      0   100%
src/postgkyl/io/mapping.py                19      0   100%
src/postgkyl/io/writer.py                112      0   100%
--------------------------------------------------------------------
TOTAL                                    707      8    99%
```

99% overall, well above the layer's ≥90% bar. Missing-line review:

- `gkyl_adios_reader.py:19-20` (the `except ImportError: adios2 = None`
  branch) and `:66` (`is_compatible()`'s `if adios2 is None: return False`) —
  **justified**: `adios2` is installed in this environment, so the
  no-adios2 fallback path is genuinely untestable here without uninstalling
  it; this is exactly the "optional-dep fallback that needs an uninstalled
  package" carve-out in PYTHON_PRINCIPLES §17.
- `gkyl_adios_reader.py:118,129-133` (the two `TypeError` raises in
  `_create_offset_count`) — **not justified**; see C1. These are reachable
  by a comma-list `axes`/`comp` selector, not defensive-unreachable code, and
  should either be tested or the justification updated to explain why that
  input is out of scope for ADIOS partial loads.

Full suite: `PYTHONPATH=src python -m pytest tests/ -q` → **574 passed**.
Architecture tests (`test_facade_is_pure_reexport`,
`test_import_contract_no_violations`, `test_foreign_floor_confined_to_ffi`,
`test_import_graph_is_acyclic`, plus the CLI/facade round-trip) pass.

## Verdict

**PASS.** The layer delivers everything the instruction file asked for — three
new readers with the same `ctx` vocabulary as the existing ones, registry
order documented with a specificity rationale in `io/__init__.py`, the
`io -> numerics` edge added deliberately and provably safe, the vtk writer +
series-file updater ported, and `c2p_grid` restored verbatim — all copied
faithfully from `src_bak` with no silent numerical divergence found on
side-by-side inspection. The suite is green (574 passed) and coverage is 99%
against a 90% bar. The four criticisms are a genuine-but-low-severity
test-coverage gap (C1) and three minor cleanliness items (C2-C4); none
change behavior for any exercised path, so a fixer pass is optional rather
than required.
