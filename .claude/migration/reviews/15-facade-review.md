# Layer 15 — facade, docs, and final benchmarks — review

Scope actually touched by this layer (verified via `git show f7f4413 --stat`):
`.claude/migration/CHECKPOINTS.md`, `.claude/migration/PLAN.md`,
`.claude/migration/FINAL_REPORT.md` (new), `src/postgkyl/__init__.py` (one
docstring line), `src/postgkyl/io/mapping.py` (docstring), plus the untracked
(gitignored-at-root) `CLAUDE.md` and `MAPPING.md`. No functional source
change. This is a docs/audit layer, so the review below is weighted toward
whether the claims in those docs are *true*, since that is the entire
deliverable.

## Doctrine adherence

- **0. Locality of reasoning** — Adheres. The two docstring edits
  (`src/postgkyl/__init__.py:35`, `src/postgkyl/io/mapping.py:5-13`) are
  self-contained corrections; nothing forces a global search to trust them.
- **I. Data is inert. Functions transform.** — Not applicable (no new data
  types or functions).
- **II. Make illegal states unrepresentable.** — Not applicable.
- **III. A function is one idea.** — Not applicable.
- **IV. The signature tells the whole truth.** — Not applicable.
- **V. Every fact has one home.** — **Violates.** This is the principle a
  facade/docs-audit layer exists to serve, and it is violated twice:
  - `.claude/migration/PLAN.md:162-164` asserts, as a benchmark-time finding,
    that "`cli/commands/fit.py` imports `postgkyl.numerics` directly, a
    layer-14-scope bug." This is false for the shipped file (verified: no
    `numerics` import appears in `src/postgkyl/cli/commands/fit.py` at HEAD,
    at `9d99d97`, or at `38f27b3`; `test_import_contract_no_violations`
    passes with zero violations). The doc now disagrees with the code it
    describes — exactly the "two sources of truth and zero" failure mode
    doctrine 0/V name.
  - `CLAUDE.md`'s "Commands" section (added by this layer) says
    `pgkyl elc_M0_0.gkyl elc_M1i_0.gkyl velocity --num-moms 5 interp plot`.
    `velocity` has no `--num-moms` option (that belongs to `euler`); running
    the example fails with `Error: No such option '--num-moms'`. The doc and
    the CLI it documents disagree.
- **VI. Separate what from how.** — Not applicable.
- **VII. Notation is execution; lowering is transliteration.** — Not
  applicable.
- **VIII. Earn your abstractions.** — Not applicable.
- **IX. An abstraction is a contract.** — Not applicable.
- **X. Trust the most formal thing first.** — **Violates.** Both defects
  above are exactly the failure this principle warns against: a docs claim
  was written without re-running the most formal available check (the
  import-contract test for C1/PLAN.md; `pgkyl <cmd> --help` or actually
  executing the example for C2/CLAUDE.md) before committing it as fact. The
  layer's own benchmark section *did* separately re-run
  `test_import_contract_no_violations`-equivalent checks and got a clean
  result, but the PLAN.md prose was not reconciled against that clean
  result.

## Principles adherence (PYTHON_PRINCIPLES.md)

- **Rule 2 (respect the layer DAG / `_ALLOWED`)** — Adheres in the actual
  tree: `test_import_contract_no_violations` passes, no new edges were
  added, none were needed. The *prose* claiming an edge violation exists is
  the problem (see doctrine V above), not the code.
- **Rule 5 (`__init__.py` files re-export; they do not define)** —
  Re-verified: `test_facade_is_pure_reexport` passes; `src/postgkyl/__init__.py`
  defines no functions/classes.
- **Rule 16 (comments state constraints, not narration; no changelog
  comments)** — Adheres for the two docstring edits actually shipped in
  `src/`; both state a present-tense constraint ("is unused by `ops/map.py`
  ... but is kept for...") rather than narrating the change.
- **Rule 17 (~100% coverage per layer, justified misses listed)** — Adheres.
  Measured independently (see Coverage below): 99% overall, matches the
  report's own table exactly, and every sub-100% file was already reviewed
  and justified in the layers that own those files (12/13/14), which this
  layer correctly did not re-litigate.
- **Rule 24 (leave the tree green)** — Adheres for the code (`1419 passed, 6
  skipped`, reproduced independently, PYTHONPATH and installed-package modes
  both green). Does not fully adhere for the *docs*, which is this layer's
  actual product (see C1/C2 below).

## Criticisms

**C1. `PLAN.md:162-164` records a fabricated import-contract regression.**
The text: "one CLI import-contract regression discovered while running this
layer's benchmarks — `cli/commands/fit.py` imports `postgkyl.numerics`
directly, a layer-14-scope bug, not fixed here per this layer's Scope." No
version of `src/postgkyl/cli/commands/fit.py` in git history (`HEAD`,
`9d99d97`, `38f27b3`) imports `postgkyl.numerics`; it imports only `click`,
`.._apply`, and `.._options`. `test_import_contract_no_violations` and
`test_import_graph_is_acyclic` both pass cleanly against the current tree.
Failure scenario: a future contributor reads PLAN.md, goes hunting for a
"layer-14-scope bug" that does not exist, or worse, loses confidence in the
architecture-contract test because the plan doc claims it's currently being
violated. `FINAL_REPORT.md:433-439`'s "Known gaps" §1 compounds the
confusion by describing `cli/commands/fit.py`'s "import statement from `from
postgkyl import numerics`" as if that string is present in the file today,
when it is not (that import exists only in `ops/fit.py:22`, a different,
legitimately-allowed edge). Fix: strike the false regression claim from
PLAN.md, and rewrite the "Known gaps" §1 paragraph to describe the
*prefix-matching* capability gap (which is real and well documented
elsewhere in the same section) without implying the fit.py import currently
violates the contract.

**C2. `CLAUDE.md`'s new "Commands" example is broken.** `CLAUDE.md:95`:
`pgkyl elc_M0_0.gkyl elc_M1i_0.gkyl velocity --num-moms 5 interp plot`.
Reproduced live: `Error: No such option '--num-moms'.` — `velocity`'s only
options are `--density`/`-d` and `--momentum`/`-m`
(`src/postgkyl/cli/commands/velocity.py:15-19`); `--num-moms` belongs to
`euler` (`src/postgkyl/cli/commands/euler.py:21`). Failure scenario: this is
the file's own "Commands" section, whose stated purpose is copy-pasteable
examples; a reader following it verbatim gets an immediate CLI error on the
very layer whose mission was "refresh the commands in CLAUDE.md's Commands
section." Fix: either drop `--num-moms` from the `velocity` example, or
switch the example to `euler --num-moms 5` (which does take that flag), and
actually execute every example added to this section before landing it.

**C3. Stale leftover-sweep count in `FINAL_REPORT.md:115-122`.** The report
says `git grep -nE "postgkeyll|typer|ctypes" src/` returns "3 hits," listing
the facade's own architecture note as one of them — but that note is the
exact thing this layer's own facade-audit fixed (`ctypes -> libg0core.so` →
`compiled _gpython extension -> libg0core.so`); after the fix the same grep
returns 2 hits, both confirmed benign
(`diagnostics/gyrokinetics/quantities.py:5`, `diagnostics/plasma.py:9`). Not
a functional problem (the two real hits are correctly characterized), just
a count left stale after the fix that removed the third. Fix: re-run the
grep after making the docstring edit and update the count before writing it
into the permanent report.

**C4 (informational, not a defect of this layer).** `CHECKPOINTS.md`'s
`14-cli` row and `FINAL_REPORT.md`'s framing both state the layer-14 fixer
pass was "uncommitted at layer-15 time" and flag it for the orchestrator to
commit "before/with layer 15." At review time the fixer pass is in fact
committed (`9d99d97`, one commit before this layer's `f7f4413`), so the
concern was already resolved by the orchestrator exactly as requested. This
is expected staleness from a document written mid-process rather than a
defect — noted only so a reader of `CHECKPOINTS.md`/`FINAL_REPORT.md` isn't
confused by the "not yet committed" language when they check `git log` and
find it already is.

No other issues found: the facade re-export audit, the leftover-sweep's
`models`/`loaders`/`commands/`-directory/`postgkyl.output` checks, the
`MAPPING.md` "Where it lives" table, the `io/mapping.py` docstring fix, and
every benchmark number in `FINAL_REPORT.md` (full-suite count, coverage
table and total, fresh-install steps, wall-clock outliers) were independently
reproduced and matched exactly.

## Coverage

Reproduced independently (`PYTHONPATH=src python -m pytest tests/ -q
--cov=postgkyl --cov-report=term-missing`); the table matches
`FINAL_REPORT.md`'s verbatim:

```
TOTAL                                                        6440     63    99%
1419 passed, 6 skipped, 4 warnings in 108.07s
```

Per-package rollup as claimed: `cli` 96.2%, `diagnostics` 98.5%, all other
packages (`api`/`core`/`dg`/`gpython`/`io`/`numerics`/`ops`/`render`) 100%.
Layer-15 itself added no new modules, so there is no new-code coverage
threshold to apply to this layer specifically; the ≥85% overall floor from
the layer's own "Definition of done" is met (99%). Every non-100% file
(`cli/_apply.py`, `cli/commands/{animate,collect,current,ev,extractinput,
fit,growth,integrate,map,plotly,plotly_animate,print,pyvista,relchange,
style}.py`, `diagnostics/gyrokinetics/{distf,energy_balance,nodes,
particle_balance}.py`) was already reviewed and justified in the 12/13/14
layer reviews (interactive-picker branches, fixture-staging gaps for
`mc2nu`/`mapc2p`/`psi_file`, `find_by_tag`'s not-found raise). This layer
correctly did not re-litigate those; the justifications still hold on
inspection (spot-checked `diagnostics/gyrokinetics/distf.py:166-177` and
`diagnostics/gyrokinetics/nodes.py:221-241` — both are exactly the
documented untested `mc2nu`/`mapc2p`/`psi_file` branches, no fixture ships
that exercises them).

## Verdict

**PASS WITH FIXES.** The code-facing work (the two docstring corrections,
the facade re-export audit, the leftover sweep, and every reproduced
benchmark number) is accurate and clean — nothing here requires touching
`src/` again. But this layer's entire deliverable *is* documentation
accuracy, and it shipped two concrete factual errors in that documentation:
a fabricated "import-contract regression" written into `PLAN.md` (and
echoed into `FINAL_REPORT.md`'s known-gaps section) that does not exist in
any version of the file it names, and a broken copy-pasteable CLI example
newly added to `CLAUDE.md`'s "Commands" section. Both are cheap, mechanical
fixes (delete/rewrite two paragraphs of prose; swap one example command or
its flag) that a fixer pass should close before the migration is considered
formally done, since leaving them in place actively misleads the next
contributor who trusts these specific documents at face value.

Criticism headlines:
- C1 (major): `PLAN.md:162-164` records a fabricated `cli/commands/fit.py`
  import-contract regression that does not exist in any git revision of the
  file, echoed into `FINAL_REPORT.md`'s "Known gaps" §1.
- C2 (major): `CLAUDE.md`'s new "Commands" example uses `velocity
  --num-moms 5`, an option `velocity` does not have (it belongs to `euler`);
  the example fails when run.
- C3 (minor): `FINAL_REPORT.md`'s leftover-sweep grep count ("3 hits") is
  stale by one after this layer's own facade-docstring fix reduced it to 2.
- C4 (informational): "uncommitted fixer pass" language in
  `CHECKPOINTS.md`/`FINAL_REPORT.md` is now stale (the orchestrator has
  since committed it) but was correctly flagged at write-time and is
  self-resolving, not a defect to fix.

Review written to
`/home/maxwell-rosen/postgkyl/.claude/migration/reviews/15-facade-review.md`.

## Resolutions

C1: FIXED — `.claude/migration/PLAN.md:156-167`'s "Layer 15 (facade) status"
paragraph no longer claims a fabricated `cli/commands/fit.py`
`postgkyl.numerics` import-contract regression; it now states plainly that
`test_import_contract_no_violations`/`test_import_graph_is_acyclic` pass
cleanly, that `cli/commands/fit.py` imports only `click` and the shared
`.._apply`/`.._options` helpers, and that the only `from postgkyl import
numerics` edge anywhere is the legitimate `ops/fit.py:22`. Also fixed
`.claude/migration/FINAL_REPORT.md`'s "Known gaps" §1 (line ~420): removed
the sentence implying `cli/commands/fit.py` currently contains a `from
postgkyl import numerics` line; it now states up front that the file
imports neither `postgkyl.numerics` nor triggers a contract violation
today, then describes the *hypothetical* small edit (adding `import
postgkyl as pg` + `pg.numerics.FIT_FUNCTIONS`) as what a facade-export fix
would look like, without implying it already exists. Verified with
`test_import_contract_no_violations`/`test_import_graph_is_acyclic`, both
passing (`git grep -n "postgkyl.numerics\|from postgkyl import numerics"
src/postgkyl/cli/` confirms zero hits outside this rewritten prose).

C2: FIXED — `CLAUDE.md`'s "Commands" section (line ~95) no longer uses
`velocity --num-moms 5` (an option `velocity` doesn't have). Replaced with
`pgkyl euler_5m_0.gkyl interp euler -v pressure --num-moms 5 plot`, using
`euler`'s real `--num-moms`/`-v` options, and reordered `interp` *before*
the diagnostic (five_moment functions require NumPy-backed/interpolated
data, per `diagnostics/five_moment.py:209`'s "must be NumPy-backed" —
the old example had this backwards too, a second latent bug the review's
Click-level reproduction didn't reach). Verified live: built a synthetic
5-component dataset via `postgkyl.core.state.GDataState` + `io.writer.save`
and ran the corrected chain end-to-end through `postgkyl.cli.app`
(`--batch-mode ... interp -b ms -p 0 euler -v pressure --num-moms 5 plot`,
substituting explicit `-b ms -p 0` only because the hand-built fixture — unlike
a real Gkeyll-written file — carries no `basis_type`/`poly_order` metadata for
`interp` to auto-detect); it ran clean end to end and produced a real
`pgkyl.png`. A genuine Gkeyll five-moment output file needs no such override,
so the flags are omitted from the doc example itself.

C3: FIXED — `.claude/migration/FINAL_REPORT.md`'s leftover-sweep section
(line ~115) now says "2 hits" (re-verified: `git grep -nE
"postgkeyll|typer|ctypes" src/` → `diagnostics/gyrokinetics/quantities.py:5`,
`diagnostics/plasma.py:9`) instead of the stale "3 hits", and no longer
lists the facade's own architecture note as one of the hits (that hit was
removed by this layer's own docstring fix, per the review's own
observation).

C4: FIXED (not strictly required — review labeled this informational, not
a defect of this layer — but the update is cheap, in-scope for this same
docs layer, and removes the exact confusion the review flagged). Updated
`.claude/migration/CHECKPOINTS.md`'s `14-cli` row (dropped "uncommitted at
layer-15 time" language, now credits `38f27b3, 9d99d97`) and its `15-facade`
row (dropped "(pending commit — see FINAL_REPORT.md)", now shows `f7f4413`).
Updated `.claude/migration/FINAL_REPORT.md`'s top "Note on a concurrent
process" and "Known gaps" §7 to state the layer-14 fixer pass is committed
(`9d99d97`, landed before this layer's own `f7f4413`) rather than describing
it as still-pending. Verified against `git log --oneline`.

Full suite after all fixes: `PYTHONPATH=src python -m pytest tests/ -q` →
`1419 passed, 6 skipped, 4 warnings in 83.39s`. Coverage unchanged at 99%
(6440 stmts, 63 missed) — this fixer pass touched only docs
(`CLAUDE.md`/`PLAN.md`/`CHECKPOINTS.md`/`FINAL_REPORT.md`), no `src/`
files, so there is no new-code coverage delta to report. All four
architecture tests (`test_facade_is_pure_reexport`,
`test_import_contract_no_violations`, `test_foreign_floor_confined_to_ffi`,
`test_import_graph_is_acyclic`) re-verified passing.
