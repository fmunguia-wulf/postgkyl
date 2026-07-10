# Layer 01 — ffi (the foreign floor): implement the comprehensive floor + unit tests

## Mission

Implement a **comprehensive FFI** for this project. The code currently in
`src/postgkyl/ffi/` and the pg0 shim (`gkeyll/core/zero/{gkyl_pg0.h, pg0.c}`)
are **a working example of the pattern**, not the finished floor: they
demonstrate the opaque-handle shim → CPython extension → thin-Python-wrapper
architecture on a starter set of capabilities. Your job is to grow that set
until it is complete.

**The completeness criterion:** every capability that any higher layer
(`dg/`, `io/`, `ops/`, `models/`, and the diagnostics they serve) needs from
Gkeyll's compiled code must be wrapped **here, now** — so that no later layer
ever has to come back down and extend the ffi, re-declare C knowledge, or
work around a missing kernel with a slow Python reimplementation. When in
doubt whether a capability belongs in the floor, ask: "would a higher layer
otherwise need struct knowledge, a C kernel, or bit-consistency with the
simulation?" If yes, wrap it.

Alongside the implementation: audit what exists, fix defects, and write a
comprehensive unit-test suite (near-100% line coverage of `ffi/*.py`).

## Read first (in this order)

1. `/home/maxwell-rosen/postgkyl/.claude/DOCTRINE.md`
2. `/home/maxwell-rosen/postgkyl/.claude/migration/PYTHON_PRINCIPLES.md`
3. `/home/maxwell-rosen/postgkyl/CLAUDE.md` — sections "ffi" and "two-domain lifecycle"
4. `/home/maxwell-rosen/postgkyl/GKEYLL_C_SHIM.md` — **the design contract;
   every extension you make must follow its rules exactly** (see "Design
   rules" below)
5. The example floor: `src/postgkyl/ffi/{__init__.py,_lib.py,array.py,basis.py,kernels.py,rio.py,rep.py}`
   and `gkeyll/core/zero/{gkyl_pg0.h, pg0.c}`, `src/postgkyl/ffi/csrc/_g0pymodule.c`
6. The demand side — what the floor must serve:
   - the other layer files `.claude/migration/layers/02-*.md` … `14-*.md`
     (each names the verbs and machinery its layer implements),
   - `src_bak/postgkyl/` (read-only) — the old implementation's full feature
     surface: everything it computed over DG data is a capability candidate,
   - Gkeyll's own `gkeyll/core/zero/gkyl_*.h` headers — the supply side;
     confirm each candidate against what the library actually provides.
7. The existing ffi-touching tests in `tests/test_postgkyl.py` (the
   `ffi.available()` skip pattern and the modal-domain tests) — do not
   duplicate them; go deeper.

## Step 1 — capability survey (do this before writing any code)

Derive the full capability list from the demand side (item 6 above). Produce
a table: capability → which higher layer(s) need it → the Gkeyll function(s)
that provide it → already wrapped / to wrap / deliberately excluded (with
reason). Include this table in your final report.

Starting candidates to investigate (verify each against the gkeyll headers —
this list is a seed, not the answer):

- **Writing** gkyl-format files through Gkeyll's rio (so `io.write("gkyl")`
  round-trips bit-exactly through the same code that wrote the input).
- **Dynvector / time-series reads** (currently only the pure-Python fallback
  handles them).
- **Partial / sub-range reads** of large fields.
- **Array averaging** over directions (`array_average.c`).
- **Cell-wise DG reductions** (`array_dg_reduce.c`) — min/max/sum of the
  *field*, not the coefficients.
- **Remaining array ops** in `array_ops.c` that higher layers' arithmetic
  needs (copy/accumulate over ranges, component-wise ops, …).
- Anything `src_bak` computed with hand-rolled interpolation-matrix math that
  Gkeyll has a compiled kernel for.

Excluding a candidate is fine — but it must be a decision recorded in the
table (e.g. "pure math, no C knowledge needed, belongs in `numerics/`"),
never an omission.

## Design rules (from GKEYLL_C_SHIM.md — non-negotiable)

- The contract is stated **once, in C**: all struct access, by-value calls,
  and function-pointer dispatch live in `pg0.c`, compiled by Gkeyll's own
  `make core` into `libg0core.so`.
- `gkyl_pg0.h` carries **opaque handles and scalars only** — no gkyl types,
  no layouts, ever.
- `_g0pymodule.c` includes only `gkyl_pg0.h`; Python holds capsules with RAII
  destructors; NumPy views pin their owning capsule via the `base` chain.
- No `ctypes`, no struct mirrors, no magic offsets anywhere in Python
  (a repo test enforces this).
- One `pg0_*` function per capability; field loops run in C; status codes
  `0 = ok` with `pg0_status_msg`.
- Capability guards (which bases/orders a kernel supports) stay in Python and
  raise friendly errors before a C `assert` could fire.
- **Bump `PG0_API_VERSION`** whenever `gkyl_pg0.h` changes shape; the
  handshake in `_lib.py` must match.

## Scope — files you may touch

- EDIT/EXTEND: `src/postgkyl/ffi/*.py`, `src/postgkyl/ffi/csrc/_g0pymodule.c`,
  `gkeyll/core/zero/gkyl_pg0.h`, `gkeyll/core/zero/pg0.c`.
- REBUILD: yes — after editing the shim, rebuild `libg0core.so`
  (`scripts/build_gkeyll.sh`, or `make core` in the gkeyll build tree) and
  then the extension (`scripts/build_pg0.sh`). The build must stay green at
  every step; a compile error in `pg0.c` is the firewall working — fix the
  shim, never weaken it.
- CREATE: `tests/test_ffi_array.py`, `tests/test_ffi_basis.py`,
  `tests/test_ffi_kernels.py`, `tests/test_ffi_rio.py`, `tests/test_ffi_lib.py`
  (merge into fewer files if a module needs only a handful of tests; add
  files for new capability modules as needed).
- DO NOT touch: anything else under `gkeyll/` (only the two pg0 files),
  `ffi/rep.py`'s location (layer 03 moves it — you may still extend and TEST
  it where it is), any other layer's source, `src_bak/` (read-only),
  `tests_bak/`.

## What to test (minimum corpus)

Gate every test that needs the compiled library with the same
`pytest.mark.skipif(not ffi.available(), ...)` pattern used in
`tests/test_postgkyl.py`. On this machine they will actually run.

**Every NEW capability you wrap** gets the same treatment as the corpus
below: a correctness test against an independent oracle (analytic value,
NumPy recomputation on the coefficient view, or cross-check against the
pure-Python reader/`src_bak` behavior), a round-trip test where one exists
(e.g. write→read), and its error paths.

**`_lib.py`** — `available()` returns True; the `PG0_API_VERSION` handshake
value matches the extension's; behavior when the extension is absent
(monkeypatch the import or the module attribute to simulate a no-library
install → `available()` False and a clear error from anything that needs it).

**`array.py` (`GkylArray`)** — construction from shape/dtype; zero-copy
construction pins the NumPy buffer (create → drop the Python reference →
`gc.collect()` → the view still reads correctly; there is already one such
regression test — extend it to the other construction paths); `view()` ties
`base` chain to the capsule; releasing the last reference does not leak or
crash (create/destroy many in a loop); invalid constructions (wrong dtype,
non-contiguous input, zero-size) refuse with clear errors.

**`basis.py`** — for every supported (basis_type, ndim, poly_order) that the
cache exposes: `num_basis` matches the analytic count (serendipity and tensor
formulas — compute the expected value independently in the test);
`eval_matrix` at the cell center reproduces the constant mode; `eval_matrix`
on a degree-≤p polynomial's modal coefficients reproduces the polynomial
exactly at arbitrary points (build coefficients via the nodal_to_modal
matrix); `nodal_to_modal @ modal_to_nodal == I` to machine precision;
modal↔quad round trip exact for polynomials of degree ≤ 2·num_quad−1; the
cache returns the same object for repeated requests; unsupported combinations
raise (not segfault) — probe boundaries carefully (e.g. dim 7, poly_order 0
or 4+) and only assert on ones that raise cleanly from Python.

**`kernels.py`** — weak multiply/divide identity `((a*b)/b == a)` on random
smooth fields (seeded RNG) for 1-D and 2-D, p1 and p2; `lincomb` matches
NumPy coefficient arithmetic; `reduce`/`integrate` of a constant field equals
constant × domain volume; scalar `scale` and mean-shift match NumPy on the
coefficient view; error paths: mismatched shapes/bases refuse.

**`rio.py`** — load each of the four `tests/test_data/rt_gk_tcv_iwl_1x2v_p1-*.gkyl`
files and the generated files under `tests/test_data/generated/`; grid,
cells, and coefficient values must agree with the pure-Python
`io.gkyl_reader.GkylReader` reading the same file (that cross-check is the
strongest test in this layer — do it for every file the C reader accepts);
a nonexistent path and a non-gkyl file refuse cleanly. If you add a write
capability: write→read round trip is bit-exact.

**`rep.py`** — modal→nodal→modal and modal→quad→modal round trips exact for
in-basis polynomials; `apply_pointwise` on `lambda x: x` is the identity.

## Audit checklist (report findings; fix while you're here)

- Does every public function have an honest signature and docstring (Args /
  Returns / Raises)? Add what's missing.
- Any struct layout, ctypes, or magic constant in Python that GKEYLL_C_SHIM.md
  says must live in C? Move it behind the shim.
- Any silent `except` or print-instead-of-raise? Fix.
- Dead code / unused imports? Remove.

## Definition of done

1. The capability table from Step 1 shows every higher-layer need as either
   **wrapped** or **deliberately excluded with a recorded reason** — nothing
   left "for later".
2. Shim, extension, and library rebuild cleanly; `PG0_API_VERSION` bumped if
   the header changed; the handshake passes.
3. `PYTHONPATH=src python -m pytest tests/ -q` → all green (baseline 26 + yours).
4. `PYTHONPATH=src python -m pytest tests/ -q --cov=postgkyl.ffi --cov-report=term-missing`
   ≥ 95% lines for `ffi/*.py` (excluding csrc). List every uncovered line and
   why in your report.
5. The four architecture tests in tests/test_postgkyl.py still pass.
6. No edits outside the Scope list.

## Final report (your last message — it is the only thing the orchestrator sees)

Sections: (1) the capability table (need → provider → wrapped/excluded),
(2) what you implemented per module — shim functions added, extension entry
points, Python wrappers, (3) what you tested per module, (4) audit findings +
which you fixed, (5) coverage numbers per file + justified misses,
(6) anything surprising about the shim's behavior or Gkeyll's kernels that
later layers should know, (7) exact pytest summary line.
