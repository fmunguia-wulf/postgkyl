# Runbook — executing the migration

Everything is on disk; no state lives in any conversation. Any orchestrator
(human or Claude session) resumes by reading this file, `PLAN.md`, and
`CHECKPOINTS.md`, then running the next incomplete layer.

## Agents

Defined in `.claude/agents/` (model: sonnet — the instruction files are
written so a weaker model succeeds; upgrade a layer's model only if it fails
twice):

- `migration-implementer` — implements one layer per its instruction file
- `migration-reviewer` — writes `.claude/migration/reviews/<layer>-review.md`
- `migration-fixer` — closes every criticism in the review

## Per-layer loop (strictly sequential; never two agents at once)

For layer `<XX-name>` (order: 01-ffi, 02-numerics, 03-dg, 04-io, 05-core,
06-models, 07-ops-field, 08-ops-physics, 09-render, 10-diagnostics,
11-api, 12-diagnostics-loaders, 13-diagnostics-programs, 14-cli, 15-facade —
renumbered after 09 per PLAN.md's models→diagnostics amendment):

1. **Pre-flight** (orchestrator): tree is clean (`git status`), suite is
   green, previous layer's CHECKPOINTS.md row is filled.
2. **Implement** — launch `migration-implementer` with the prompt:
   > Implement migration layer `<XX-name>`. Your instruction file is
   > `/home/maxwell-rosen/postgkyl/.claude/migration/layers/<XX-name>.md`.
   > Read it first and follow it exactly.
3. **Review** — launch `migration-reviewer` with:
   > Review migration layer `<XX-name>` (instruction file
   > `.claude/migration/layers/<XX-name>.md`). Write
   > `.claude/migration/reviews/<XX-name>-review.md`.
4. **Fix** — if the verdict is PASS WITH FIXES or FAIL, launch
   `migration-fixer` with:
   > Fix migration layer `<XX-name>` per
   > `.claude/migration/reviews/<XX-name>-review.md`. Append the
   > Resolutions section when done.
   On FAIL, after the fixer, re-run the reviewer once; if still FAIL,
   stop and escalate to the user.
5. **Checkpoint** (orchestrator runs, does not delegate):
   ```bash
   cd /home/maxwell-rosen/postgkyl
   PYTHONPATH=src python -m pytest tests/ -q                        # C1
   PYTHONPATH=src python -m pytest tests/ -q -k \
     "facade_is_pure_reexport or import_contract or foreign_floor or graph_is_acyclic"  # C2
   PYTHONPATH=src python -m pytest tests/ -q --cov=postgkyl.<layer> \
     --cov-report=term-missing                                      # C3 (100%, ffi/numerics/core/api 100%, render/cli 100%, diagnostics quantity modules 100%, loader/program modules ≥ 85%/80%)
   PYTHONPATH=src python -m pytest tests/test_postgkyl.py -q        # C4 golden
   test -f .claude/migration/reviews/<XX-name>-review.md            # C5 (+ Resolutions closed)
   ```
   C6 (old-parity) is judged from the review doc's divergence section.
6. **Record + commit**: fill the layer's row in `CHECKPOINTS.md`, then
   ```bash
   git add -A src tests .claude/migration pyproject.toml
   git commit -m "migrate <layer>: <one-line scope>"   # never add src_bak/, tests_bak/, pygkyl/
   ```
7. Mark the layer's task completed (tasks track layers 01–15).

## Standing decisions (do not relitigate per layer)

- `integrate` and `map` intentionally diverge from src_bak (modal-side
  integrate; MAPPING.md evaluation-based map). C6 does not apply to them.
- Obsolete list (never ported): computeInterpolationMatrices,
  computeDerivativeMatrices, modalDG/, tools/gkeyll_dg_ops.py,
  _gkylsoft_path.py, the Typer stack, utils/input_parser.py.
- Physical constants come from scipy.constants; Gkeyll enum tables are ported
  minimally, at point of use, with the source header named.
- New `_ALLOWED` import edges only where a layer file authorizes them
  (04-io: io→numerics decision; 10-diagnostics: `diagnostics → {core, ops,
  numerics}` and models/ removal; 12-diagnostics-loaders adds `api`,
  13-diagnostics-programs adds `render`; no `loaders` layer exists, ever).
- Layer 10 is a restructure, not a port: numerical parity is judged against
  the pre-layer git HEAD, not src_bak; C6 means "the relocated tests pass
  with unchanged asserted values".

## Escalation triggers (stop and ask the user)

- A layer FAILs review twice.
- A checkpoint requires weakening an architecture test.
- Test data needed for parity does not exist and cannot be synthesized
  (note it in the review, skip loudly, and continue — escalate only if the
  layer's core capability is untestable).
- Anything requiring edits to C sources or the gkeyll submodule.
