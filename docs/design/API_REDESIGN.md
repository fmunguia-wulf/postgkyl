# Postgkyl Script API Redesign — Fluent `GData` over a Unified Verb Layer

> Design doc produced collaboratively. Approved plan also stored at
> `~/.claude/plans/tidy-sprouting-wolf.md`. Implementation not yet started.

## Context

`pgkyl` has two interfaces that drifted into two different mental models:

- **CLI** (`pgkyl file.gkyl interp sel --z0 0 plot`) — a left-to-right chain of verbs.
- **Script** (`pg.GData(...)`, then `pg.GInterpModal(d).interpolate()`, then `pg.tools...`,
  then `pg.output.plot(...)`) — scattered statements with intermediate objects, ordered
  differently from how you read the operation.

Users align with one or the other and the two surfaces are maintained separately, so they
diverge in naming and behavior. The goal (inspired by the "readable code / build a
language" idea) is a **top-down**, prose-like script API where a line reads as
*subject → verb → verb → verb*, and where **the script verb and the CLI verb are the same
implementation** so they can never drift again.

This dovetails with `RESTRUCTURING.md` item #2 ("thin out CLI commands"): the same seam
that makes commands testable is the seam that lets scripts and the CLI share one verb
library.

Intended outcome:

```python
import postgkyl as pg
pg.load('elc_M0_0.gkyl').interp().sel(z0=0.0).plot()
```

is the *normal* way to script, the CLI is a thin shell over the identical verbs, and
`GData` gains Python-native ergonomics (`print`, `+ - * /`, `pg.plot(a, b)`).

## Locked design decisions (from discussion)

1. **No new class — extend `GData`.** `pg.load(...)` returns a `GData`; fluent verbs are
   methods on it. Keeps surface small; `GData` *is* the dataset.
2. **`print(data)`** → concise summary header + numpy's truncated preview of values and
   grid. Rich metadata via `.info()` (already exists); raw arrays via `.values` / `.grid`
   (already exist as properties).
3. **Simulation loading** uses keyword args:
   `pg.load.simulation('name', model='gk', cdim=1, vdim=2)` (also accept `dims='1x2v'`).
   Auto-detect where possible, kwargs override.
4. **Combining** is primarily varargs: `pg.plot(data1, data2)`. A `.with_()` /
   `DatasetGroup` exists for chaining, but `pg.plot(a, b, ...)` is the documented path.
5. **Flexible evaluation:** verbs **return a new `GData` by default** (so a stored handle
   stays stable — `n = load().sel(...); ...; print(n)` shows what you expect). Every verb
   accepts **`inplace=True`** to mutate and return `self` for large 5D data. This
   generalizes the `overwrite=` flag the codebase already uses (e.g.
   `postgkyl.data.select(dat, overwrite=True)`, `dg.interpolate(..., overwrite=True)`).
   A fully lazy pipeline is deferred (see Future).

## Design principles

- **Read order = data flow.** `load().interp().sel().plot()` — each verb takes the dataset
  and returns a dataset.
- **One verb, one implementation, two front-ends.** CLI command name == `GData` method
  name == verb-function name.
- **Don't reimplement; wrap.** The verb layer calls existing `tools/`, `data/select.py`,
  `data/dg.py`, `output/`.
- **Python-native where it helps.** Dunders for arithmetic and printing;
  `pg.plot(*datasets)` for the common "show these together" case.

## Target scripts (top-down — the API exists to make these read well)

```python
import postgkyl as pg

# 1. Quick look
pg.load('elc_M0_0.gkyl').interp().plot()

# 2. Slice, keep a handle, inspect
n = pg.load('elc_M0_0.gkyl').interp().sel(z0=0.0)
n.plot()
print(n)                 # <GData (x:64)> + truncated values/grid

# 3. Compare two runs on one figure (varargs)
a = pg.load('runA_M0_0.gkyl').interp().sel(z1=0.0)
b = pg.load('runB_M0_0.gkyl').interp().sel(z1=0.0)
pg.plot(a, b)            # overlaid, auto legend

# 4. Arithmetic via dunders (replaces simple `ev 'f g -'`)
ref  = pg.load('elc_M0_0.gkyl').interp()
late = pg.load('elc_M0_5.gkyl').interp()
err  = abs(late - ref) / ref
err.plot(title='relative change')

# 5. Reductions / spectral
pg.load('elc_M0_0.gkyl').interp().integrate().info()
pg.load('phi_0.gkyl').interp().sel(z1=0.0).fft().plot()

# 6. A whole simulation
sim = pg.load.simulation('gk55', model='gk', cdim=1, vdim=2)
sim.species                                   # ['elc', 'ion']
sim.field('elc', 'M0').frame(10).interp().plot()
sim.field('elc', 'M0').frames().interp().sel(z0=0.0).animate()

# 7. Time series across frames
sim.field('elc', 'M0').frames().interp().integrate().collect().plot()
```

These define the verb vocabulary: `load`, `interp`(`interpolate`), `sel`(`select`),
`plot`, `animate`, `collect`, `integrate`, `differentiate`, `fft`, `growth`, `ev`,
`mask`, `write`, `info`, plus moment/diagnostic verbs (`agyro`, `euler`, `tenmoment`, …).
All already exist as CLI commands.

## Architecture: one verb library, two thin front-ends

```
L0  tools/                    pure numpy fns                       (unchanged)
L1  data/ GData + readers     I/O + grid/values storage            (extended, not broken)
L2  ops/  verb functions      ONE implementation per verb          (NEW seam)
        e.g. ops.select(data, z0=..., inplace=False) -> GData
L3a GData fluent methods      1-line delegations to L2, return GData/group   (NEW)
L3b commands/ Click shells    ~15-line shells calling L2           (thinned)
```

Single source of truth: `GData.sel(...)`, the CLI `select` command, and `ops.select(...)`
all run the same L2 function.

### L2 verb-function contract

```python
# src/postgkyl/ops/select.py  (logic moved out of commands/select.py + data/select.py)
def select(data: GData, *, z0=None, ..., comp=None, inplace=False, **meta) -> GData:
    grid, values = _select_arrays(data, z0=z0, ...)     # the existing pure logic
    return data._result(grid, values, inplace=inplace, **meta)
```

`GData._result(grid, values, inplace, tag=None, label=None)` is one new helper that
centralizes the "mutate via `push` vs. emit a new tagged `GData`" branch currently
copy-pasted across every command (see `commands/select.py`, `commands/interpolate.py`).

### L3a: methods on `GData` (delegation, with lazy imports to avoid cycles)

```python
class GData:
    def sel(self, *, inplace=False, **z):      # alias: select
        from postgkyl import ops
        return ops.select(self, inplace=inplace, **z)

    def interp(self, basis=None, p=None, interp=None, *, inplace=False):  # alias: interpolate
        from postgkyl import ops
        return ops.interpolate(self, basis=basis, p=p, interp=interp, inplace=inplace)

    def plot(self, **kw):
        from postgkyl import output
        return output.plot_datasets([self], **kw)   # returns self for chaining
```

`basis`/`p` default to `self.ctx['basis_type']`/`ctx['is_modal']` (already populated by the
readers). `GInterpModal(data)` already auto-detects poly_order+basis when both are `None`
(`dg.py:397`), so `.interp()` with no args works.

### L3b: Click shells become trivial

```python
# commands/select.py  (after)
@click.command()
@click.option('--z0'); ...; @click.pass_context
def select(ctx, **kw):
    for dat in ctx.obj['data'].iterator(kw['use']):
        ops.select(dat, inplace=True, z0=kw['z0'], ...)
```

The multiblock branch currently embedded in `commands/select.py` moves into
`ops/select.py` so both front-ends get it.

## Python-native surface on `GData`

- **Dunders:** `__add__/__sub__/__mul__/__truediv__/__pow__` and reflected (`__radd__`…),
  `__neg__`, `__abs__`. Operate elementwise on `get_values()`; scalar broadcasts;
  **require grid compatibility** (matching shapes) and raise a clear `ValueError`
  otherwise. Result is a new `GData` carrying the left operand's grid/ctx. Keep
  `.ev('f 5 +')` for complex RPN.
- **`__repr__` / `__str__`:** header
  (`<GData (x:64, vpar:32) + 1 comp | bounds x[0,1] vpar[-6,6] | ms p1 | tag 'elc'>`)
  followed by numpy's truncated `values` and `grid` preview. (Note: `info()` already
  returns a rich metadata string; `__repr__` does not yet exist — safe to add.)
- **`.values` / `.grid`** already exist as read/write properties — no change needed.
- **`.copy()`:** explicit deep copy (so users can opt out of `inplace`).

## Combining datasets

- `pg.plot(*datasets, **kw)` — primary. Move the multi-dataset
  figure/subplot/legend/`globalrange` loop currently in `commands/plot.py` into
  `output.plot_datasets(list_of_gdata, **kw)`; both `pg.plot` and the CLI `plot` command
  call it.
- `data1.with_(*others) -> DatasetGroup` — a light ordered collection whose verb methods
  broadcast over members and whose `.plot()` calls `plot_datasets`. Enables
  `group.interp().sel(...).animate()`. (`&` operator optional sugar; not required.)

## `pg.load` — callable + namespace

`load` is a small callable singleton instance (`pg.load = _Loader()`):

- `pg.load('file.gkyl', **gdata_kwargs)` → `GData` (wraps current `GData(...)`).
- `pg.load.simulation(name, *, model=None, cdim=None, vdim=None, dims=None, species=None) -> Simulation`.
- `pg.load.many('glob*.gkyl') -> DatasetGroup` (convenience over globbing).

`Simulation` knows the file-naming convention and exposes: `sim.species`, `sim.fields`,
`sim.model`, `sim.dims`, and `sim.field(species, name)` → a `DatasetGroup`-producing handle
with `.frame(i)` / `.frames(start=0, stop=None, step=1)`. Model/dims auto-detected from
files; kwargs override. (Mirror/model types can live in `utils/gkeyll_enums.py` alongside
the existing geometry enums.)

## Restructuring steps (phased, each independently shippable)

1. **Add `GData._result(grid, values, inplace, tag, label)`** + `.copy()`. Pure addition.
   Add `__repr__`/`__str__` and arithmetic dunders (self-contained, easy to unit-test).
2. **Create `src/postgkyl/ops/`** and move verb logic there, starting with `select`,
   `interpolate`, `plot` (highest traffic). Re-export `postgkyl.data.select` for
   back-compat.
3. **Add fluent methods to `GData`** delegating to `ops` (lazy imports).
4. **Factor `output.plot_datasets([...], **kw)`** out of `commands/plot.py`; add top-level
   `pg.plot`.
5. **Thin the Click commands** to call `ops.*` (start with `select`, `interpolate`,
   `plot`; then the rest). CLI syntax/behavior unchanged — verified by `tests/cli`.
6. **`_Loader` + `pg.load`**, then `Simulation` + `DatasetGroup`.
7. **Docs/doctests:** put the golden scripts above into module docstrings as `>>>`
   doctests (per RESTRUCTURING.md item #3) so the API and examples can't drift.

Order keeps every step green: 1–4 are additive; 5 only swaps command internals; 6–7 build
the simulation layer on top.

## Critical files

- `src/postgkyl/__init__.py` — export `load`, `plot`, keep `GData`.
- `src/postgkyl/data/gdata.py` — fluent methods, dunders, `__repr__`/`__str__`, `_result`,
  `.copy()`. (`.values`/`.grid`/`.info()` already present.)
- `src/postgkyl/ops/` (new) — `select.py`, `interpolate.py`, … one verb each; absorbs logic
  from `commands/*` and `data/select.py`, `data/dg.py`.
- `src/postgkyl/output/plot.py` — add `plot_datasets(list, **kw)` (multi-dataset loop from
  `commands/plot.py`).
- `src/postgkyl/commands/select.py`, `interpolate.py`, `plot.py`, … — thinned shells.
- `src/postgkyl/commands/data_space.py` — optionally back `DataSpace` with `DatasetGroup`;
  not required for phase 1.
- New: `src/postgkyl/sim.py` (`Simulation`), `src/postgkyl/loader.py` (`_Loader`),
  `src/postgkyl/group.py` (`DatasetGroup`).

## Verification

- `pytest` (and `tests/cli` CliRunner tests) stay green after each phase — proves CLI
  behavior unchanged.
- Run representative chains unchanged, e.g. `pgkyl <file> interp sel --z0 0 plot --save`.
- New doctest examples (the golden scripts) run via `pytest --doctest-modules src/postgkyl`.
- Manual smoke test in a REPL against a file in `tests/`:
  `pg.load(<test file>).interp().sel(z0=0.0)` → check `print`, `.values.shape`, arithmetic
  (`(d - d).values` ≈ 0), and `pg.plot(d, d)`.
- Confirm `inplace=True` mutates and `inplace=False` (default) leaves the source handle
  unchanged.

## Future (explicitly out of scope now)

- **Lazy pipeline mode** (record verbs, execute at a terminal like `.plot()`/`.values`) for
  big-data and frame sweeps — revisit once the eager API and the `ops` seam are proven.
- `&` operator sugar for `with_`.
- Comparison dunders producing masks.
