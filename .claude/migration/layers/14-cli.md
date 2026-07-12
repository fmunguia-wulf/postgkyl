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
`print` (print values — full name, not `pr`: see "Command naming and
abbreviation" below), `config` ONLY if it still has a backing store — else
skip and note.

## Help output organization

`pgkyl --help` lists ~40 commands once every verb/diagnostic/render/loader
shell above is registered — flat, that's noise for a user who only ever
touches one equation system. Fix this at the presentation layer only, not
by changing how commands resolve or chain:

- Override `PgkylGroup.format_commands` (the standard Click hook for
  grouped help — see `git`/`docker` for prior art) to print registered
  commands under section headers instead of one flat alphabetical list:
  **Verbs** (fft, magsq, relchange, mask, collect, grid, val2coord,
  extractinput, fit, growth, differentiate, ev, map, integrate, animate,
  interp, select), **Diagnostics** (euler, tenmoment, mhd, velocity, agyro,
  current, energetics, parrotate, perprotate, bparrotate, bperprotate,
  transform_frame, laguerre_compose), **Render** (plot, plotly,
  plotly_animate, pyvista, style), **Loaders** (load, gk_distf,
  gk_load_quantity, gkyl_pkpm), **Utility** (info, print, listoutputs,
  status, config).
- This is presentation only: every command stays a flat, chainable
  top-level `click.Command` registered in `COMMANDS` exactly as today.
  Do NOT nest diagnostics under a real `click.Group` subcommand (e.g.
  `pgkyl diagnostics euler`) — `chain=True` groups treat nested groups as
  chain members unreliably (argument boundaries between the subgroup and
  the next chain link become ambiguous), and `PgkylGroup.get_command`
  would need to recurse into a second namespace, duplicating the one
  resolution mechanism the doctrine says should have one home. The
  section headers solve discoverability without touching resolution.

## Command naming and abbreviation

Command names are spelled out in full (`print`, not `pr`; `interpolate`,
not `interp`) — short forms are never separate canonical names, they are
resolved dynamically by `PgkylGroup.get_command`'s prefix match
(`c.startswith(name)`, already implemented in `cli/app.py`). This is not
an alias table — it's the general parsing rule, so it falls out of
whatever full names the commands above are given, and it must keep
working as new commands are added:

- `pr` and `pri` both resolve uniquely to `print` (no other registered
  command starts with `pr`).
- `p` alone is genuinely ambiguous — `plot`, `print`, `plotly`,
  `plotly_animate`, `pyvista`, `parrotate`, `perprotate` all start with
  `p` — and must produce the `ctx.fail("Ambiguous command …")` error
  already implemented, not silently pick one.
- Do not add entries to `_ALIASES` to paper over a new ambiguity;
  either the ambiguity is real (let it fail, tell the user to type more
  characters) or the colliding command needs a distinguishable full name.

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
- Abbreviations still resolve via prefix match (`interp`, `sel`, `pr`/`pri`
  → `print`) and genuine collisions fail closed rather than silently
  picking one: assert `ctx.fail` on `e` (`ev`/`euler`/`energetics`) and on
  `p` (`plot`/`print`/`plotly`/`plotly_animate`/`pyvista`/`parrotate`/
  `perprotate`). Test this once as a generic property (shortest unique
  prefix per registered command resolves; shared prefixes error) rather
  than hardcoding each colliding letter.
- Option-parity spot checks against the old command's documented options.

## Definition of done

1. Full suite green; architecture tests pass (cli imports facade only).
2. `--cov=postgkyl.cli` ≥ 85%.
3. `pgkyl --help` lists every command; no command's help crashes.
4. Report: command inventory (ported / skipped+why), dropped options list,
   abbreviation collisions found, coverage, pytest summary.
