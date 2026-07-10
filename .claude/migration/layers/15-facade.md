# Layer 15 — facade, docs, and final benchmarks

## Mission

Close the migration: true up the facade and docs, sweep for leftovers, and
run the end-state benchmarks from PLAN.md. This layer writes the final
migration report.

## The work

1. **Facade audit** — `src/postgkyl/__init__.py` re-exports every public name
   from the layer that owns it (api, render, ops, io, and the `diagnostics`
   subpackage, including `load_gk_quantity` etc.); still pure re-export;
   `__version__` present (pyproject reads it). Neither `models` nor `loaders`
   may appear anywhere (removed by layers 10 and 12).
2. **Docs sync** — CLAUDE.md: the architecture tree, the verb list, and the
   layer descriptions must match what now exists (rep location, diagnostics/
   per-equation modules + equation-internal loaders + programs, new ops
   modules, render backends, CLI command list). MAPPING.md §"Where it lives": mark rows implemented. Update the
   stale docstring MAPPING.md calls out in `io/mapping.py`. Refresh the
   commands in CLAUDE.md's "Commands" section if the CLI surface grew.
   PLAN.md's deferred list: check each item's final status.
3. **Leftover sweep** —
   `git grep -nE "postgkeyll|typer|ctypes" src/` → must be empty;
   `git grep -n "src_bak" src/ tests/` → must be empty;
   no `src/postgkyl/commands/` directory;
   `pyproject.toml` package-data paths point at real files
   (`postgkyl.output` key must be gone/renamed if styles moved to render).
4. **Benchmarks** (record outputs verbatim in the final report):
   - `PYTHONPATH=src python -m pytest tests/ -q` — full green.
   - `PYTHONPATH=src python -m pytest tests/ -q --cov=postgkyl --cov-report=term-missing`
     — overall ≥ 85%; attach the per-file table.
   - Fresh-install check: `pip install -e .[test]` in the current env
     succeeds; `pgkyl --version` and `pgkyl --help` work; `pytest tests/ -q`
     passes WITHOUT `PYTHONPATH` (i.e. against the installed package).
   - Golden chains (fluent):
     `pg.load("tests/test_data/rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl").interp().sel(z0=0).plot()`
     and a modal-domain chain (`a*b/b == a`, `.integrate()`), and a
     generated-data chain per dimension (1d/2d/3d).
   - Golden chains (CLI): `pgkyl <file> interp sel --z0 0 plot --save`,
     `pgkyl <file> info`, one moments chain, one ev chain.
   - Wall-clock: time the full suite; flag any single test > 30 s.
5. **Final report** — `.claude/migration/FINAL_REPORT.md`: per-layer summary
   (from the review docs), the complete deferred/dropped inventory with
   reasons, coverage table, benchmark outputs, and a "known gaps" section a
   future contributor can pick up.

## Definition of done

Every benchmark above passes (or its failure is explained and accepted in
FINAL_REPORT.md with the orchestrator's sign-off). CHECKPOINTS.md has a row
for every layer. The tree is committed layer-by-layer with clean messages.
