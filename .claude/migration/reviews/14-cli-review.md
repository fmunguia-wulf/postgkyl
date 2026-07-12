# Layer 14 — cli — review

## Doctrine adherence

**0. Locality of reasoning.** *Partial violation.* Most command modules are
small, self-contained shells that can be read in isolation (the goal of this
principle). But `collect.py:28`, `ev.py:24`, and `val2coord.py:20-26`
silently replace `ctx.obj.datasets` with only the just-produced result(s),
so understanding what happens to *other* datasets already in the working
set (loaded earlier in the chain, or deactivated by `status`) requires
tracing through `_apply.py`'s active-flag contract and noticing these three
commands don't honor it — a global, not local, reasoning burden. See C1.

**I. Data is inert. Functions transform.** Adheres. `is_active`/`set_active`
(`cli/_apply.py:19-25`) are free functions operating on a plain attribute;
no new methods or behavior are added to `GData`/`GDataState`. All 40+ new
command modules are thin functions, no classes.

**II. Make illegal states unrepresentable.** *Partial/accepted tradeoff.*
`_cli_active` (`cli/_apply.py`) is an untyped, unenforced dynamic attribute
bolted onto `GData` instances via `getattr`/plain assignment rather than a
checked field of the dataset's own type — a dataset can be "inactive"
without that being part of its declared shape. The module docstring
explicitly justifies this as the least-bad option given `GDataState` is
verb-less (doctrine V trade-off, stated honestly) — I read this as a
reasoned exception rather than an oversight, so not scored as a violation,
but it is worth the fixer's attention that nothing stops a future verb from
silently dropping this attribute when copying a dataset.

**III. A function is one idea.** Adheres. Each command does exactly one
verb's argument-collection-and-delegate job. `plot.py`'s command has 19
parameters, but they are a flat 1:1 pass-through to `render.plot`'s existing
option surface (established in an earlier layer), not two concepts wearing
one signature.

**IV. The signature tells the whole truth.** *Violation.*
`cli/commands/integrate.py` keeps the old command's name and general shape
(a terminal verb that prints a value) but silently changes what is being
computed: the old `integrate <axis>` computed a NumPy trapezoidal integral
over a chosen axis of interpolated data; the new `integrate --op {none,abs,sq}`
computes a whole-grid Gkeyll native-modal integral. Nothing in the signature,
docstring, or help text discloses that this is a different capability under
the same name, not a superset of the old one. See C2.

**V. Every fact has one home.** *Violation.* The old axis-restricted,
field-domain integral (`postgkyl.tools.calculus.integrate` in `src_bak`) was
ported faithfully to `src/postgkyl/numerics/calculus.py::integrate` back in
layer 02 ("mirrors the legacy behaviour exactly", per its own docstring) but
was never wired into any `ops` verb, `GData` method, or CLI command — it is
dead, unreachable code, a second orphaned "home" for integration logic that
duplicates (and contradicts) `ops/integrate.py`'s Gkeyll-modal integral. Also
`cli/_apply.py:64`'s `find_all_by_tag` is a speculative second home for
tag-lookup that nothing calls (grep across `src/` and `tests/` finds zero
call sites) — see C6.

**VI. Separate what from how.** Adheres. Every command module only collects
Click options and delegates to `postgkyl` facade calls / `GData` methods;
no math, no file-format knowledge, no plotting internals leak into `cli/`.

**VII. Notation is execution; lowering is transliteration.** *Violation*,
same root cause as IV: the CLI is the "lowering" of the old command
vocabulary, and principle VII specifically warns that the lowering layer
must reproduce the spec "exactly — nothing added, nothing dropped, nothing
reinterpreted... If the lowering changes anything, the spec is a lie."
`integrate`'s silent capability swap (C2) and `fit`'s dropped prefix-matching
of the `FIT_TYPE` argument (C4, `fit lin` used to resolve to `linear`, now
hard-fails) are both cases where the lowering added an opinion ("only the
literal name will do", "only whole-grid integration exists now") that the
old spec did not have, without flagging it as an intentional change.

**VIII. Earn your abstractions.** *Violation.* `find_all_by_tag`
(`cli/_apply.py:64-66`) exists with no second use anywhere in `src/` or
`tests/` — a helper written ahead of any actual caller. See C6.

**IX. An abstraction is a contract.** *Violation.* `_apply.py`'s module
docstring and `status.py`'s docstring together assert a contract: "Deactivated
datasets are skipped by transform commands... and by the terminal commands
(info, plot, save)" — implying deactivation is reversible and datasets are
never silently dropped from the working set. `collect.py`, `ev.py`, and
`val2coord.py` break this contract by replacing the *entire* `ctx.obj.datasets`
list with just the newly produced result(s), discarding any dataset that was
inactive or didn't match `--use` — including ones the user could previously
reactivate with `status --activate`. Confirmed by direct reproduction (see
C1). `energetics`/`agyro` also violate the (implicit, undocumented) contract
that a multi-input diagnostic deactivates all of its consumed inputs — see C3.

**X. Trust the most formal thing first.** *Partial.* There is no static type
checker in this project, so tests are the most formal available layer, and
they are extensive (1412 passed at HEAD-of-worktree, 96% line coverage of
`postgkyl.cli`). But the test suite exercises *that a command runs
successfully*, not always *that its old-parity behavior is preserved* — the
three bugs above (C1, C2, C4) all pass the existing test suite and were only
caught by direct reproduction against `src_bak`, meaning the formal layer
(tests) under-specifies the very contract (parity + working-set integrity)
this layer's instruction file cares most about.

## Principles adherence

1. **Absolute imports spelled `postgkyl`.** Adheres — every new module uses
   `import postgkyl as pg` or package-relative `from .._apply import ...`.
2. **Respect the layer DAG.** Adheres — `test_import_contract_no_violations`,
   `test_import_graph_is_acyclic`, `test_foreign_floor_confined_to_ffi`, and
   `test_facade_is_pure_reexport` all pass; cli imports only the facade and
   its own `cli/` siblings.
3. **Guard optional deps at import time.** N/A for this diff — matplotlib,
   plotly, and pyvista are hard dependencies per `pyproject.toml`; the only
   optional dep (`adios2`) is untouched by this layer. `style.py` does a
   local `import matplotlib as mpl` inside the command body rather than at
   module top, which is a minor style deviation (matplotlib is a hard dep,
   so there's no import-guarding reason for it) but not an optional-dep
   violation.
4. **No typer, no ctypes.** Adheres — grep for `typer`/`ctypes` across the
   new files returns nothing; everything is Click.
5. **`__init__.py` re-exports only.** Adheres — `commands/__init__.py` only
   imports submodules and builds the `COMMANDS`/`COMMAND_SECTIONS` list/dict
   literals; no function or class defined there.
6. **Type-annotate every public function.** *Established-convention gap, not
   new.* None of the new command callbacks annotate parameter types (only
   `-> None` return annotations), relying on Click's `type=` for the actual
   type declaration. This matches the pre-existing exemplars
   (`interpolate.py`, `select.py`) the instruction file explicitly told the
   implementer to "copy... exactly," so it is not a regression introduced by
   this diff, but it is a real, repository-wide gap against this rule.
7. **Keyword-only options.** Adheres — every Click option is a `--flag`, no
   positional booleans.
8. **No mutable default arguments.** Adheres.
9. **Take arrays/GDataState appropriately; no dual-input parsing.** Adheres
   — commands delegate to `GData` fluent methods or `postgkyl`/`pg.diagnostics`
   functions; none reimplement array unwrapping.
10. **Raise, don't print-and-continue.** *Violation.* `val2coord.py` has no
    guard for an empty (or `--use`-filtered-to-empty) pool — see C1's second,
    more severe manifestation: it silently wipes the working set to `[]`
    with exit code 0 and no message, instead of raising `click.UsageError`
    the way `collect`, `ev`, `current`, `fit`, and `growth` all correctly do
    for the same empty-pool case.
11. **Pure core, effects at the edges.** Adheres — file writes, plotting,
    and printing only happen in `cli`/`render`/`io`, as expected for this layer.

17-20 (tests). Mostly adheres: `tests/test_cli_commands.py` +
`tests/test_cli_diagnostics.py` port the old behavioral corpus, use real
fixtures under `tests/test_data`, assert values (not just shapes, e.g.
`test_euler_density_value`), and the architecture tests are untouched and
green. Gaps: `find_all_by_tag` (rule 17's "~100% line coverage... justified
misses" is not met — it's neither covered nor justified, it's simply unused)
and the missing-guard/silent-wipe behaviors in C1/C10 above were not tested
even though the sibling commands' equivalent guards were.

21. **Copy liberally, then adapt; never change numerical behavior silently.**
    Violated by `integrate`'s renamed-but-different capability (C2) and by
    the fit-type prefix-matching drop (C4) — both are undocumented behavior
    changes under an unchanged command name.
22. **Do not port the obsolete.** Adheres — no `dg_avg`/`dg_evproj`/
    `dg_local_poly`/Typer-era commands were ported; `test_config_and_dg_
    commands_are_not_registered` checks this.
23. **Never edit `src_bak`/`tests_bak`.** Adheres — `git status`/`git diff`
    show no changes under either tree.
24. **Leave the tree green.** Adheres — `PYTHONPATH=src python -m pytest
    tests/ -q` passes: 1412 passed, 6 skipped, 0 failed.

## Criticisms

**C1. `collect`/`ev`/`val2coord` silently discard datasets that are not part
of their output, breaking the working-set/`status` contract; `val2coord`
does this even on a completely empty match, with no error.**
`src/postgkyl/cli/commands/collect.py:28`, `ev.py:24`, `val2coord.py:26`.
All three end with `ctx.obj.datasets = [result]` (or `= out`) instead of
splicing the result into the existing list. Reproduced directly:
```
pgkyl ENERGY ENERGY status --deactivate 0 collect status
# -> only 1 dataset remains; the deactivated original is gone, not reactivatable
```
and, more severely, for `val2coord`:
```
pgkyl ENERGY ENERGY val2coord -x 0 -y 1 --use nonexistent_tag status
# exit code 0, no output at all -- the entire working set silently vanished
```
A user chaining `load A --tag a; load B --tag b; collect --use a; plot` (or
any pipeline where not every loaded dataset participates in a `collect`/`ev`/
`val2coord` call) loses dataset `b` outright instead of it surviving
untouched, and a mistyped `--use` tag on `val2coord` silently empties the
session rather than failing loudly. Fix: replace the pool's positions in
`ctx.obj.datasets` with the result(s) (mirroring how `apply()`/`current`/
`fit`/`growth` correctly leave non-participating datasets alone), and add
the same "no datasets to operate on" `click.UsageError` guard `val2coord`
is missing.

**C2. `integrate` silently redefines the old command's meaning instead of
growing it to old parity, per this layer's own instruction file, and the
capability it replaced is now dead code.**
`src/postgkyl/cli/commands/integrate.py` (whole file);
`src/postgkyl/numerics/calculus.py::integrate` (unreachable);
`.claude/migration/layers/14-cli.md:28` ("`integrate` (grow options to old
parity)"). The old CLI's `integrate <axis>` performed a NumPy trapezoidal
integral over a *chosen axis* of interpolated data (`ops/integrate.py` in
`src_bak`, wrapping `tools/calculus.py::integrate`, which was ported
verbatim into `src/postgkyl/numerics/calculus.py` back in layer 02). The new
`integrate --op {none,abs,sq}` is an entirely different, whole-grid,
Gkeyll-native-modal integral with no axis argument at all — not a superset,
a replacement, under the identical command name. `tests/test_cli_commands.py`
lines ~248-251 assert this is intentional and claim "see integrate.py's
docstring and this layer's report," but `integrate.py`'s docstring says
nothing about a dropped axis capability, and no report file exists in the
repo to check. Fix: either restore an axis-based integrate path (wiring the
already-ported `numerics.calculus.integrate` through a new/extended `ops`
verb) or, at minimum, name the capability change explicitly in
`integrate.py`'s own docstring and in a written report, rather than only in
a test comment that overstates what was actually documented.

**C3. Multi-tag diagnostic commands are inconsistent about which consumed
inputs they deactivate, and one confirmed case (`energetics`) diverges from
`src_bak`.**
`src/postgkyl/cli/commands/energetics.py:22` deactivates `elc`/`ion` but not
`field` (confirmed by direct invocation: `field` stays active after
`energetics` runs); `src_bak/postgkyl/commands/energetics.py` deactivates
all three (`elc`, `ion`, *and* `field`). `agyro.py:22` deactivates only the
pressure tensor, not the B-field input (`src_bak`'s `agyro` deactivated
neither, so this is a new, partial, undocumented choice, inconsistent with
`velocity`/`current`/`parrotate`/`perprotate`/`bparrotate`/`bperprotate`,
which all deactivate every consumed input). A user running
`energetics ... plot` sees the raw EM field dataset unexpectedly overlaid
next to the energetics result, where the old tool would have hidden it.
Fix: settle one rule ("a diagnostic command deactivates every dataset it
consumed as an input") and apply it uniformly across all seven multi-tag
commands; add `is_active(...)` assertions to `test_cli_diagnostics.py` for
every consumed tag, not just some.

**C4. `fit`'s `FIT_TYPE` argument silently dropped the old CLI's
prefix-matching/abbreviation support.**
`src/postgkyl/cli/commands/fit.py` passes `fit_type` straight through to
`d.fit(fit_type, ...)`, which requires an exact `numerics.fit.FIT_FUNCTIONS`
key or a valid RPN expression (`numerics/fit.py:218-224`, no `startswith`
matching). `src_bak/postgkyl/commands/fit.py`'s `FitTypeParam.convert`
resolved abbreviations the same way command names are abbreviated
(`fit lin` -> `linear`). Reproduced: `pgkyl ENERGY fit lin` now fails with
"fit_type 'lin' not recognized," a regression for any old script or muscle
memory relying on the abbreviation. This is not listed as a deliberate drop
anywhere. Fix: either restore prefix-matching for `FIT_TYPE` as a
`click.ParamType` in `fit.py` (which is exactly where it lived before — this
was CLI-layer logic, not core-verb logic, so nothing below `cli/` needs to
change), or document the drop explicitly.

**C5. `growth` dropped the old CLI's `--dir`/`--instantaneous` options
without documenting the drop.**
`src/postgkyl/cli/commands/growth.py` offers `--guess`/`--min-n` only.
`src_bak/postgkyl/commands/growth.py` additionally supported `--dir` (choose
which axis of 2-D DynVector data to compute a per-mode growth rate along)
and `--instantaneous` (an interactive matplotlib plot of the pointwise
growth rate over time). These are real, distinct capabilities (not just
convenience), silently absent with no docstring note and no entry in a
report. Given the layer instruction explicitly requires listing "each drop"
(`.claude/migration/layers/14-cli.md:135`), this should at minimum be named
in `growth.py`'s docstring.

**C6. Dead/unearned code: `find_all_by_tag` has no caller anywhere in the
tree.** `src/postgkyl/cli/_apply.py:64-66`. `grep -rn "find_all_by_tag"
src/ tests/` returns only the definition. It is also one of the five
uncovered lines in `_apply.py` (see Coverage). Fix: delete it until a second
call site actually needs it (doctrine VIII), or use it somewhere and cover it.

**C7 (minor). `plot --figsize` has no input guard.**
`src/postgkyl/cli/commands/plot.py`: `w, h = figsize.split(",")` raises an
unhandled `ValueError` (not a `click.UsageError`) for any malformed value
(e.g. `--figsize 10`), inconsistent with principle 10's "raise ... with a
message that names the offending value and the fix" and with how every
other command in this layer validates its own string-encoded options
(`parse_indices`, `val2coord`'s `-x`/`-y`, etc. either succeed or produce a
clean usage error). Low impact (single option, easy to work around), so
kept as minor.

## Coverage

Measured via `coverage run --source=src/postgkyl/cli -m pytest tests/ -q`
then `coverage report -m` (direct `pytest --cov=postgkyl.cli` hit an
unrelated `numpy`/`matplotlib` "cannot load module more than once per
process" collection error in this environment; the `coverage run` wrapper
avoids it and instruments the same source):

```
Name                                            Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------
src/postgkyl/cli/__init__.py                        2      0   100%
src/postgkyl/cli/_apply.py                         34      5    85%   44, 46, 61, 66, 73
src/postgkyl/cli/_options.py                       12      0   100%
src/postgkyl/cli/_variable.py                       7      0   100%
src/postgkyl/cli/app.py                            45      1    98%   62
src/postgkyl/cli/commands/__init__.py               6      0   100%
src/postgkyl/cli/commands/agyro.py                 18      0   100%
src/postgkyl/cli/commands/animate.py               22      1    95%   34
src/postgkyl/cli/commands/bparrotate.py            18      0   100%
src/postgkyl/cli/commands/bperprotate.py           18      0   100%
src/postgkyl/cli/commands/collect.py               21      2    90%   28, 30
src/postgkyl/cli/commands/current.py               28      3    89%   28, 36-37
src/postgkyl/cli/commands/differentiate.py         12      0   100%
src/postgkyl/cli/commands/energetics.py            22      0   100%
src/postgkyl/cli/commands/euler.py                 18      0   100%
src/postgkyl/cli/commands/ev.py                    19      2    89%   32-33
src/postgkyl/cli/commands/extractinput.py          14      1    93%   18
src/postgkyl/cli/commands/fft.py                   13      0   100%
src/postgkyl/cli/commands/fit.py                   37      2    95%   51, 53
src/postgkyl/cli/commands/gk_distf.py              27      0   100%
src/postgkyl/cli/commands/gk_load_quantity.py      22      0   100%
src/postgkyl/cli/commands/gkyl_pkpm.py             15      0   100%
src/postgkyl/cli/commands/grid.py                  12      0   100%
src/postgkyl/cli/commands/growth.py                30      4    87%   28, 30, 36-37
src/postgkyl/cli/commands/info.py                   8      0   100%
src/postgkyl/cli/commands/integrate.py             19      1    95%   24
src/postgkyl/cli/commands/interpolate.py           10      0   100%
src/postgkyl/cli/commands/laguerre_compose.py      17      0   100%
src/postgkyl/cli/commands/listoutputs.py           14      0   100%
src/postgkyl/cli/commands/load.py                  12      0   100%
src/postgkyl/cli/commands/magsq.py                 12      0   100%
src/postgkyl/cli/commands/map.py                   13      1    92%   26
src/postgkyl/cli/commands/mask.py                  16      0   100%
src/postgkyl/cli/commands/mhd.py                   18      0   100%
src/postgkyl/cli/commands/parrotate.py             19      0   100%
src/postgkyl/cli/commands/perprotate.py            19      0   100%
src/postgkyl/cli/commands/plot.py                  38      2    95%   47-48
src/postgkyl/cli/commands/plotly.py                44      5    89%   44, 55, 62-65
src/postgkyl/cli/commands/plotly_animate.py        25      4    84%   29, 34, 38-39
src/postgkyl/cli/commands/print.py                 19      1    95%   23
src/postgkyl/cli/commands/pyvista.py               32      3    91%   40, 42, 47
src/postgkyl/cli/commands/relchange.py             20      1    95%   28
src/postgkyl/cli/commands/save.py                  11      0   100%
src/postgkyl/cli/commands/select.py                14      0   100%
src/postgkyl/cli/commands/status.py                19      0   100%
src/postgkyl/cli/commands/style.py                 18      1    94%   23
src/postgkyl/cli/commands/tenmoment.py             17      0   100%
src/postgkyl/cli/commands/transform_frame.py       18      0   100%
src/postgkyl/cli/commands/val2coord.py             20      1    95%   26
src/postgkyl/cli/commands/velocity.py              18      0   100%
src/postgkyl/cli/state.py                          10      0   100%
-----------------------------------------------------------------------------
TOTAL                                             972     41    96%
```

96% overall, well above the layer's 85% floor, and no report to cross-check
line-by-line justifications against was found in the repo. Spot-checking
the misses myself:

- `_apply.py` 44/46/61/73: the inactive-dataset pass-through branch, the
  `--use` tag-mismatch pass-through branch, `find_by_tag`'s not-found raise,
  and `parse_indices`'s comma-separated branch are all real, reachable,
  *documented* behaviors with no test — not "defensive unreachable" misses,
  they are missing tests for shipped functionality. `_apply.py` 66 is
  `find_all_by_tag`, which is dead code (C6) — its miss is "justified" only
  in the sense that deleting it is the right fix, not that it's fine to
  leave uncovered.
- `plotly.py` 44/55/62-65, `plotly_animate.py` 29/34/38-39,
  `pyvista.py` 40/42/47, `animate.py` 34: mostly the non-batch
  (`fig.show()`/interactive-window) branches, which can't run headless in
  CI — a legitimate, standard justification, consistent with similar misses
  accepted in the `09-render` layer's review.
  `plotly.py` 44 specifically is the "> 1 dataset, multi-file save path"
  branch (`f"{i}_{save_path}"`), which is a real untested code path, not an
  interactive-only one — should be closed with a two-dataset `--save` test.
- `collect.py` 28/30, `growth.py` 28/30, `current.py` 36-37, `ev.py` 32-33,
  `fit.py` 51/53: all the `click.UsageError` "no datasets" guards — plausible
  to justify as "the obviously-correct guard clause," but since C1 shows the
  *equivalent* guard is entirely missing from `val2coord.py`, I'd rather see
  these covered than asserted-by-symmetry.
- `map.py` 26, `relchange.py` 28, `val2coord.py` 26, `extractinput.py` 18,
  `style.py` 23, `print.py` 23, `integrate.py` 24, `app.py` 62: small
  single-line misses (an option branch or an error path), acceptable minor
  gaps individually, not flagged further.

## Verdict

**PASS WITH FIXES (fixer required).** The bulk of the layer is solid: every
command from the instruction file's inventory is present and wired through
`COMMANDS`/`COMMAND_SECTIONS`, the abbreviation/ambiguity mechanism works as
a genuine property (tested generically, not per-hardcoded-letter), the
architecture tests are untouched and green, the full suite passes (1412
passed, 0 failed), and coverage (96%) comfortably clears the 85% floor. But
three concrete, reproduced defects need fixing before this should be
considered done: (C1) `collect`/`ev`/`val2coord` silently discard datasets
outside their own output — including, for `val2coord`, wiping the entire
working set to empty with exit code 0 when `--use` matches nothing — which
is a real data-loss bug in ordinary chained usage, not a style nit; (C2)
`integrate` was redefined under an unchanged name in direct contradiction of
this layer's own instruction to "grow options to old parity," leaving the
already-ported axis-based integral as unreachable dead code, with a test
comment that inaccurately claims this is documented elsewhere; and (C4) a
confirmed regression in `fit`'s type-name abbreviation. C3/C5/C6/C7 are
smaller but should be swept up in the same pass. None of this calls the
layer's overall architecture or majority of commands into question, so a
full re-implementation is not warranted — a fixer pass addressing C1-C7 (and
tightening the coverage misses noted above) should suffice.
