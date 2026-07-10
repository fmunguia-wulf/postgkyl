# Layer 14 — cli (thin Click shells over the public API)

## Mission

Port every remaining old command as a thin Click command in `cli/commands/`,
plus the CLI infrastructure. Each command uses ONLY the public API
(`import postgkyl as pg`, GData methods) — cli depends on the facade alone.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. `CLAUDE.md` — cli section (chained pipeline is native Click; the ~12-line
   `get_command` override does abbreviation + bare-filename-as-load)
3. Exemplars: `src/postgkyl/cli/{app.py,state.py,_apply.py,commands/*.py}` —
   copy their shape exactly (how a command pulls datasets from the chain
   state, applies a verb, pushes results back)
4. Old commands for option vocabulary: `src_bak/postgkyl/commands/<name>.py` —
   keep option names/abbreviations byte-compatible where the verb supports
   them; drop options whose backing feature was deliberately not ported and
   list each drop.
5. `tests_bak/test_commands.py` (74 tests) + `tests_bak/cli/test_cli_integration.py`
   — the behavioral contract for option parsing.

## Commands to add (one module each, registered in `COMMANDS`)

Verb shells (core verbs, via `GData` methods / `pg.*`): `fft, magsq,
relchange, mask, collect, grid, val2coord, extractinput, fit, growth,
differentiate, ev, map, integrate (grow options to old parity), animate`.
Diagnostic shells (equation-specific, via `pg.diagnostics.<module>` — the
facade re-exports the subpackage, so `import postgkyl as pg` stays the only
import): `euler, tenmoment, mhd, velocity, agyro, current, energetics,
parrotate, perprotate, bparrotate, bperprotate, transform_frame,
laguerre_compose`. For `euler`/`tenmoment`/`mhd`, build the `-v/--variable`
option's vocabulary from the module's `VARIABLES` table (one home for the
quantity names — never retype the string list in the CLI).
Render shells: `plot` (grow to old option parity: log axes, vmin/vmax,
colorbar, multi-panel, save), `plotly`, `plotly_animate`, `pyvista`.
Loader shells: `gk_distf`, `gk_load_quantity`, `gkyl_pkpm` — thin wrappers
over the equation-internal loaders (`pg.diagnostics.gyrokinetics.load_gk_distf`
/ `load_gk_quantity`, `pg.diagnostics.pkpm.load_pkpm`).
Utility commands: `listoutputs` (uses `pg.diagnostics.discovery`), `status`
(activate/deactivate datasets in the chain state), `style` (render.style),
`pr` (print values), `config` ONLY if it still has a backing store — else
skip and note.

Infra:
- `utils/verb_print.py` → `cli/_verbosity.py` on Click
  (`ctx.obj` verbosity flag + timestamped `click.echo`), wired into `app.py`
  like the old `pgkyl.py` did.
- `utils/set_frame.py` → frame-list resolution helper in `cli/` if the loader
  shells need it.
- Old `commands/_options.py` / `_load_opts.py` — port as shared Click option
  decorators in `cli/_options.py` (one home for repeated option groups).

Skip (superseded/deferred per PLAN.md): `dg_avg`, `dg_evproj`,
`dg_local_poly`, Typer-era `data_space`/`state` (already rebuilt).
Also delete the orphaned `src/postgkyl/commands/` remnants (git status shows
deleted-but-tracked `dg_avg.py`/`dg_evproj.py` there) — that directory should
not exist in the new tree.

## Tests

`tests/test_cli_commands.py` (+ split by family if large) using
`click.testing.CliRunner`, porting `tests_bak/test_commands.py` cases:
- Every command: `--help` renders (loop over ALL registered commands —
  cheap and catches wiring errors).
- Chained pipelines per family on `tests/test_data/` files:
  `<file> interp magsq plot --save` (Agg + `tmp_path`), `ev` expressions,
  moments chains on the copied euler fixtures, `listoutputs` on a tmp dir of
  conventionally-named files.
- Abbreviations still resolve (`interp`, `sel`, plus any new collisions —
  e.g. `e` must not silently pick between `ev`/`euler`/`energetics`: assert
  ambiguous-prefix behavior).
- Option-parity spot checks against the old command's documented options.

## Definition of done

1. Full suite green; architecture tests pass (cli imports facade only).
2. `--cov=postgkyl.cli` ≥ 85%.
3. `pgkyl --help` lists every command; no command's help crashes.
4. Report: command inventory (ported / skipped+why), dropped options list,
   abbreviation collisions found, coverage, pytest summary.
