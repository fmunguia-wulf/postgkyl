# Postgkyl Refactor Plan — One Verb Library, Two Front-Ends

> **Purpose.** Re-organize the `commands/` layer so that a single *master class* /
> verb library drives both the Python script API and the CLI. The CLI becomes a thin
> shell (migrated from Click to Typer); the script API reads top-down like prose
> (`pg.load('f.gkyl').interp().sel(z0=0).plot()`); and `GData` gains Python-native
> ergonomics (printing, `+ - * /`, NumPy interop). The two surfaces share **one
> implementation per verb** so they can never drift again.
>
> **Source documents.** Human-authored intent: `RESEDIGN_NOTES.md` (authoritative).
> Prior-session design: `API_REDESIGN.md`. This plan reconciles the two, grounds them
> in the current code, resolves the open conflicts, and lays out a phased path.

---

## 0. Implementation status (live)

**Delivered and green — 768 tests passing (from a 639 baseline, +129 new, zero regressions).**

| Phase | Status | Where |
|---|---|---|
| 1 — GData ergonomics (`_result`, `.copy`, `__repr__`/`__str__`, `is_interpolated`, arithmetic dunders, `__array__`/`__array_ufunc__`, guardrails) | ✅ Done | `data/gdata.py`; `tests/test_gdata.py` |
| 2 — `ops/` seam (`select`, `interpolate`, `differentiate`, `integrate`, `_dg`) | ✅ Done | `ops/`; `tests/test_ops.py` |
| 3 — Fluent methods (`sel/select`, `interp/interpolate`, `diff/differentiate`, `integrate`, `plot`, `with_`) | ✅ Done | `data/gdata.py`; `tests/test_ops.py` |
| 4 — `output.plot_datasets` + `pg.plot` + `GData.plot` | ✅ Done | `output/plot.py`, `__init__.py`; `tests/test_plot_datasets.py` |
| 5 — `DatasetGroup` (broadcast + terminal verbs, `.with_`, `&`) | ✅ Done | `group.py`; `tests/test_group.py` |
| 6 — CLI thinned over `ops` (`select`, `interpolate`, `differentiate`, `integrate`, `plot`) via `commands/_apply.py` — behavior unchanged | ✅ Done | `commands/`; parity in `tests/test_commands.py` |
| 7 — `pg.load` callable + `pg.load.many` | ✅ Done | `loader.py`; `tests/test_loader.py` |
| 8 — port remaining verbs to `ops`+fluent+thin-CLI (26 verbs) | ✅ Done | `ops/`; `tests/test_ops*.py` |
| Golden scripts #1–#6 verified end-to-end | ✅ Done | `tests/test_golden_scripts.py` |

**Verb coverage (Phase 8 — 26 `ops` verbs, 32 fluent `GData` methods).** `ops` + fluent
`GData` methods + thinned Click commands now exist for: `select`, `interpolate`,
`differentiate`, `integrate`, `fft`, `magsq`, `mask`, `relchange`, `agyro`, `mom_agyro`,
`current`, `energetics`, `parrotate`, `perprotate` (+ `bparrotate`/`bperprotate` via
`coords='3:6'`), `transform_frame`, `euler`, `tenmoment`, `mhd`, `velocity`, `grid`,
`val2coord`, `extract_input`, `laguerre_compose`, `fit`, `growth`, and `collect` (group
aggregation). Terminal fluent methods: `plot`, `plotly`, `pyvista`, `plotly_animate`, and
`animate` (`DatasetGroup.animate` via new `output.animate`); `write`/`info` already on
`GData`; `print(d)` covers `pr`. Discovery: `pg.load.outputs()` covers `listoutputs`.

Bugs fixed while porting: `mask` (broken context/typos), `val2coord` (removed `np.int`),
`pkpm` (broken f-string tuple), and a `grid`-verb/`grid`-property name collision was
avoided (the verb is `ops.grid`; `GData.grid` stays the grid-array property).

**CLI framework decision (resolved).** Stays on **Click** (thinned), not Typer. The §8.3
spike showed Typer is not installed, the suite has 103 `ctx.invoke` Click call-sites, and
chaining isn't first-class in Typer; the user confirmed "thin over ops, keep Click." The
`ops` seam is framework-independent, so a Typer swap remains a clean, isolated follow-up.

**Loaders (live in the `pg.load` namespace, not `ops`)**
- **`gk_distf`** is a *loader*, not a `verb(data) -> data` transform: it reads the saved
  `Jf` plus its companion Jacobian/mapping files, divides and interpolates them, and emits
  interpolated `GData` ready for array math. It is therefore incorporated the same way the
  CLI `load` command is — exposed on the loader singleton as **`pg.load.gk_distf(name,
  species, frame, ...)`**, returning a `GData` for one frame or a `DatasetGroup` for a
  range/list of frames (mirroring `pg.load.many`). The per-frame math stays in
  `commands/gk_distf.py:load_gk_distf`; frame-spec parsing is shared via
  `commands/gk_distf.py:resolve_frames`, used by both the CLI command and the loader.

**Intentionally NOT verbs (remain CLI commands / script helpers)**
- **Standalone GK analysis+visualization tools** — `gk_energy_balance`, `gk_nodes`,
  `gk_particle_balance` (246–471 lines each). These load files, compute, and
  render complete figures; they are mini-applications, not `verb(data) -> data` transforms,
  so they stay as CLI commands. `trajectory` (3D particle-path animation) is the same shape.
- **Inherently CLI/REPL state** — `status`/`activate`/`deactivate` (DataSpace stack state),
  `style` (matplotlib rcParams), `load` (the CLI loader; `pg.load` is the script equivalent).
- The full-featured CLI `animate` keeps its grouptags/multiblock/saveframes branches; the
  common one-frame-per-dataset path is available to scripts via `output.animate` /
  `DatasetGroup.animate`. The CLI `collect` keeps its chunk/multi-tag orchestration;
  `ops.collect` covers the single-group case. `fit`/`growth` keep their result-printing CLI
  bodies, with `ops.fit`/`ops.growth` (+ `GData.fit`/`GData.growth`) as the script entry.
- `temp.py` (`mult`/`pow`/`log`/`abs`/`norm`) is dead code (unregistered, references a
  defunct context) — superseded by the GData arithmetic dunders.

**Remaining (future phases)**
- Phase 7 — `Simulation` (species/frame model) not started.
- Phase 9 — doctest wiring (`[tool.pytest.ini_options]` + `--doctest-modules`), a bundled
  `pg.example()` fixture for portable doctests, and a user migration guide.
- The multiblock branch of `select` still lives in the command (not yet moved into `ops`).

---

## 1. Executive summary

Today `pgkyl` has **two divergent interfaces** over the same functionality:

- **CLI** — a left-to-right chain of verbs: `pgkyl f.gkyl interp sel --z0 0 plot`.
- **Script** — scattered statements with intermediate objects:
  `d = pg.GData(...)`, `pg.GInterpModal(d).interpolate(overwrite=True)`,
  `pg.tools...`, `pg.output.plot(...)`.

They are maintained separately and drift in naming and behavior. The fix is a single
**verb layer** (`src/postgkyl/ops/`) that is the *only* implementation of each
operation. On top of it sit **two thin front-ends**:

```
L0  tools/                 pure numpy functions                      (unchanged)
L1  data/  GData + readers  I/O + grid/values storage                (extended, not broken)
L2  ops/   verb functions   ONE implementation per verb  ← NEW SEAM  (the "master class" logic)
           ops.select(data, *, z0=…, inplace=False) -> GData
L3a GData / DatasetGroup    fluent methods (1-line delegations to L2) ← NEW
L3b commands/ (Typer)       thin shells that translate argv → L2/L3   (thinned + Typer)
```

**The single source of truth:** `GData.sel(...)`, `DatasetGroup.sel(...)`, the CLI
`select` command, and `ops.select(...)` all run the exact same L2 function.

The end-state golden script:

```python
import postgkyl as pg
pg.load('elc_M0_0.gkyl').interp().sel(z0=0.0).plot()
```

---

## 2. Goals & non-goals

**Goals**
1. One implementation per verb; CLI verb name == `GData` method name == `ops.<verb>`.
2. Top-down, prose-like script API: `subject → verb → verb → verb`.
3. `GData` is the **master class**: fluent verbs, `print()`, arithmetic dunders, and
   NumPy interop (`np.sqrt(a**2 + b**2)` returns a `GData` carrying its grid).
4. **Guardrails:** block NumPy/arithmetic on raw (non-interpolated) DG modal data with
   a clear error.
5. CLI is a thin Typer layer over the verb library; chaining UX preserved.
6. Examples live in docstrings and are **verified in CI** (doctests).
7. Every phase is independently shippable and keeps `pytest` green.

**Non-goals (this round)**
- Lazy/deferred pipeline execution (record verbs, run at a terminal). *Deferred.*
- Rewriting the numerical `tools/` — they stay pure and untouched.
- Changing on-disk file formats or reader internals.
- Comparison dunders producing masks (`d > 0`). *Deferred.*

---

## 3. Current-state findings (what shapes the design)

Grounded in the code as of this branch:

| Area | Finding | Implication |
|---|---|---|
| `GData` (`data/gdata.py`) | Central class. Stores `_grid` (list of 1-D arrays) + `_values` ((N+1)-D array). `ctx` dict holds all metadata. Has `push(grid, values)` (mutate-in-place, returns self), `.grid`/`.values` read/write properties, `.info()`, `.write()`, `.tag`/`.label`/`.status`. **No** `__repr__`, dunders, `__array__`, or `.copy()`. | `push()` is the existing "overwrite" mechanism → basis for `_result()`. Ergonomics are pure additions. |
| Interpolation (`data/dg.py`) | `GInterpModal(data, poly_order=None, basis_type=None, num_interp=None, …)` auto-detects `poly_order`/`basis_type` from `ctx` when `None`. `interpolate(comp=0, overwrite=False)` returns `(grid, values)` or pushes. | `.interp()` with no args already works via auto-detect. |
| **Modal/nodal state** | `ctx["is_modal"]` is set `True` by the readers (`gkyl_reader.py:194`, `gkyl_adios_reader.py:155/159`) and **never cleared after interpolation**. The `is_modal` locals in `commands/interpolate.py`/`differentiate.py` only pick `GInterpModal` vs `GInterpNodal`. | **There is no reliable "has been interpolated" flag today.** The guardrail (Goal 4) requires us to add one (see §9). |
| Command boilerplate | ~10 "transform" commands repeat the same *tag-or-overwrite* branch (canonical: `commands/interpolate.py:67-75`): if `--tag` → build new `GData(ctx=dat.ctx)`, `push`, `dataspace.add`; else call the op with `overwrite=True`. | This branch belongs in **one** helper (`_result()` + a CLI `apply()` middleware). |
| `commands/plot.py` | ~80 Click options, a pre-loop *globalrange* scan computing shared vmin/vmax, then a loop calling `postgkyl.output.plot(dat, args, label_prefix=…, **kwargs)` once per dataset; handles figure numbering, subplots, legend, save, batch_mode. | The multi-dataset loop becomes `output.plot_datasets([...], **kw)`, shared by `pg.plot` and the CLI. |
| `ev_cmd.py` | Already implements numpy-level ops on `(grid, values)` stacks: `add, subtract, mult, divide, power, sq, sqrt, abs, sin/cos/tan, log, log10, min/max, mean, exp, grad, integrate, curl, divergence, …` with an RPN registry. | Arithmetic dunders + `__array_ufunc__` can **reuse** this logic; keep `.ev('f g -')` for complex RPN. |
| CLI plumbing (`pgkyl.py`) | Click `chain=True` group with a custom `PgkylCommandGroup` providing: command **abbreviation**, explicit **aliases** (`pl`,`ply`,`pv`,…), and **bare filenames as implicit `load`**. `DataSpace` (dict tag→list[GData]) holds the stack; commands iterate via `ctx.obj["data"].iterator(use)`. | Chaining + abbreviation + bare-file load is the CLI **contract** to preserve. It is a Click-group feature (see §8 — biggest migration risk). |
| Tests | CLI tested by **`ctx.invoke(cmd.x)`** with a hand-built Click `Context` (`tests/test_commands.py`), **not** `CliRunner`. `tests/cli`, `tests/unit`, `tests/integration` are empty. **No** doctest config; no `[tool.pytest.ini_options]`. | Typer migration needs a test strategy (§12). Doctests must be wired up. |
| `pyproject.toml` | `[project.scripts] pgkyl = "postgkyl.pgkyl:cli"`. Deps include `click>=8.1.7`; **`numpy>=1.24.4,<2`**; `python>=3.10`. Optional groups: `adios`, `test`. | Swap `click`→`typer`; update entry point; respect NumPy<2 in all new code. |
| Test fixtures | Small `.gkyl` files exist: `shock-f-ser-p1.gkyl` (2.2 K), `twostream-field-energy.gkyl` (1-D, good for line plots), `twostream-f-p2.gkyl` (129 K). | Good doctest fixtures — but see §12 for path-portability (`pg.example(...)`). |

---

## 4. Target architecture

### 4.1 The object model

| Object | Role | Lives in |
|---|---|---|
| **`GData`** | The **master class** — a single dataset and the fluent subject of every verb. Verb methods (delegating to `ops`), arithmetic dunders, NumPy protocol, `__repr__`, `_result()`, `.copy()`, `.with_()`. | `data/gdata.py` (extended) |
| **`ops.<verb>`** | The verb library — exactly one implementation per operation. Pure-ish functions `op(data, *, …, inplace=False) -> GData`. Wrap `tools/`, `data/`, `output/`. | `ops/` (NEW) |
| **`DatasetGroup`** | Ordered collection of `GData`. Non-terminal verbs **broadcast** over members (return a new group); terminal verbs (`plot`, `animate`, `info`, `write`) act on all together. Backs `.with_()`, `pg.load.many()`, `Simulation` frame sweeps, and the CLI stack. | `group.py` (NEW) |
| **`Simulation`** | Knows the Gkeyll file-naming convention. `sim.species`, `sim.fields`, `sim.field(sp, name).frame(i)/.frames()`. | `sim.py` (NEW, late phase) |
| **`_Loader` / `pg.load`** | Callable singleton + namespace: `pg.load(file)`, `pg.load.many(glob)`, `pg.load.simulation(name, …)`. | `loader.py` (NEW) |
| **`pg.plot`, `pg.animate`, …** | Top-level varargs helpers: `pg.plot(a, b)`. Thin wrappers over `output.plot_datasets`. | `__init__.py` / `output/` |
| **Typer CLI** | A thin shell mapping argv → `DatasetGroup`/`GData` verb calls. Preserves chaining, abbreviation, aliases, bare-file load. | `commands/` + `pgkyl.py` (thinned) |

### 4.2 "What is the master class?" — resolving the two docs

`RESEDIGN_NOTES.md` asks for *"a master class that has methods for the commands… the
CLI wraps the master object… the layer here sits between `commands/` and click."*
`API_REDESIGN.md` says *"no new class — extend `GData`."* **These are the same design:**
the master class **is `GData`**, elevated to a fluent facade whose methods are the verbs,
backed by the new `ops/` seam. The CLI calls those same verbs.

- The **verb vocabulary** is defined once in `ops/`.
- **Two fluent front-ends** expose it: `GData` (one dataset) and `DatasetGroup` (many).
- The **CLI** is a Typer shell that builds a `DatasetGroup` from argv and calls verbs on
  it. The chain `pgkyl f sel plot` becomes, literally, `load(f).sel(...).plot(...)`.

*Rejected alternative:* a single monolithic orchestrator object holding the whole
`DataSpace`. It breaks read-order = data-flow, doesn't compose, and doesn't match the
human's own examples (`pg.load(...).select(...).plot()`). `GData`-as-facade +
`DatasetGroup` is strictly more composable.

---

## 5. Core contracts (code sketches)

These are the load-bearing pieces. Signatures are illustrative but precise.

### 5.1 `GData._result()` — centralize the tag-or-overwrite branch

```python
# data/gdata.py
def _result(self, grid, values, *, inplace=False, tag=None, label=None, **ctx_updates):
    """The one place that decides 'mutate self' vs 'emit a new GData'."""
    target = self if inplace else self.copy(data=False)
    target.push(grid, values)                 # existing mutate primitive
    if tag is not None:   target.set_tag(tag)
    if label is not None: target.set_label(label)
    target.ctx.update(ctx_updates)            # e.g. interpolated=True
    return target

def copy(self, data=True):
    """Deep copy of metadata (and optionally arrays) without re-reading a file."""
    new = GData(tag=self._tag, label=self._custom_label, ctx=self.ctx)  # ctx is copied in __init__
    if data and self._values is not None:
        new.push([g.copy() for g in self._grid], self._values.copy())
    new.color = self.color
    return new
```

This single helper replaces the copy-pasted branch in `select.py`, `interpolate.py`,
`differentiate.py`, `integrate.py`, `fft.py`, `magsq.py`, `relchange.py`, `mask.py`, … .

### 5.2 L2 verb contract

```python
# ops/select.py  (absorbs commands/select.py orchestration + data/select.py logic)
def select(data, *, comp=None, z0=None, z1=None, …, z5=None,
           inplace=False, tag=None, label=None) -> "GData":
    grid, values = _select_arrays(data, comp=comp, z0=z0, …)   # the existing pure logic
    return data._result(grid, values, inplace=inplace, tag=tag, label=label)
```

- **Returns a new `GData` by default** (so a stored handle stays stable); `inplace=True`
  mutates and returns `self` (for large 5-D data). This generalizes today's `overwrite=`.
- `ops.interpolate` additionally sets `interpolated=True` in `ctx` (see §9).
- The multiblock branch currently embedded in `commands/select.py` moves *into*
  `ops/select.py` so **both** front-ends get it.

### 5.3 L3a fluent methods (1-line delegations, lazy imports to avoid cycles)

```python
# data/gdata.py
def sel(self, *, inplace=False, **z):
    from postgkyl import ops
    return ops.select(self, inplace=inplace, **z)
select = sel                                   # canonical name == CLI command name

def interp(self, basis=None, p=None, interp=None, *, inplace=False):
    from postgkyl import ops
    return ops.interpolate(self, basis=basis, p=p, interp=interp, inplace=inplace)
interpolate = interp

def plot(self, **kw):
    from postgkyl import output
    return output.plot_datasets([self], **kw)  # returns a figure; self stays chainable via group
```

### 5.4 Arithmetic dunders + NumPy protocol (guardrailed)

```python
# data/gdata.py
_HANDLED_TYPES = (numbers.Number, np.ndarray)

def __array__(self, dtype=None):               # lets np.asarray(d), plt.plot(d.grid, d) work
    return np.asarray(self._values, dtype=dtype)

def __array_ufunc__(self, ufunc, method, *inputs, **kw):
    if method != "__call__":
        return NotImplemented
    self._require_operable()                    # guardrail (§9)
    raw = [x._operand() if isinstance(x, GData) else x for x in inputs]
    for x in inputs:                            # grid-compatibility check
        if isinstance(x, GData): self._check_compatible(x)
    out = ufunc(*raw, **kw)
    return self._result(self._grid, out)        # new GData carrying left grid/ctx

def __add__(self, other):  return np.add(self, other)
def __sub__(self, other):  return np.subtract(self, other)
def __mul__(self, other):  return np.multiply(self, other)
def __truediv__(self, o):  return np.true_divide(self, o)
def __pow__(self, other):  return np.power(self, other)
__radd__ = __add__; __rmul__ = __mul__         # reflected; rsub/rtruediv/rpow defined explicitly
def __neg__(self):  return np.negative(self)
def __abs__(self):  return np.abs(self)
```

Routing the dunders through `__array_ufunc__` gives one guardrailed path for **both**
`a + b` and `np.sqrt(a**2 + b**2)`, satisfying `RESEDIGN_NOTES` directly. (Reuse
`ev_cmd`'s array helpers internally where convenient.)

### 5.5 `__repr__` / `print(data)`

```python
def __repr__(self):
    # <GData (x:64, vpar:32) | 1 comp | bounds x[0,1] vpar[-6,6] | ms p1 | tag 'elc'>
    return _summary_header(self) + "\n" + np.array2string(self._values, threshold=12)
```

`.info()` (rich metadata) already exists and is unchanged.

### 5.6 CLI `apply()` middleware (kills Pattern-A boilerplate)

```python
# commands/_apply.py  (new)
def apply(ctx, op, *, use=None, tag=None, label=None, **op_kwargs):
    ds = ctx.obj["data"]
    for dat in ds.iterator(use):
        if tag:
            ds.add(op(dat, inplace=False, tag=tag, label=label, **op_kwargs))
        else:
            op(dat, inplace=True, **op_kwargs)
```

A thinned command then reads:

```python
@app.command()
def select(ctx, z0: str = None, …, use: str = None, tag: str = None):
    apply(ctx, ops.select, use=use, tag=tag, z0=z0, …)
```

### 5.7 `output.plot_datasets` + `pg.plot`

```python
# output/plot.py
def plot_datasets(datasets, **kw):
    """Multi-dataset figure: the globalrange scan + per-dataset loop currently in
    commands/plot.py. Both pg.plot and the CLI plot command call this."""
    …                                          # scan vmin/vmax, manage fig/subplots/legend/save
    for i, dat in enumerate(datasets):
        plot(dat, args, label_prefix=_label(dat, i, kw), **kw)   # existing single-dataset primitive
    …

# __init__.py
def plot(*datasets, **kw):
    from postgkyl import output
    return output.plot_datasets(_flatten(datasets), **kw)        # accepts GData, DatasetGroup, lists
```

### 5.8 `DatasetGroup` (broadcast + terminal verbs)

```python
# group.py
class DatasetGroup:
    def __init__(self, datasets): self._d = list(datasets)
    def __iter__(self):  return iter(self._d)
    def __getitem__(self, i): return self._d[i]
    def with_(self, *others):  return DatasetGroup(self._d + _flatten(others))
    __and__ = with_                                        # optional `a & b` sugar

    def __getattr__(self, name):                           # auto-broadcast non-terminal verbs
        def broadcast(*a, **k):
            return DatasetGroup([getattr(d, name)(*a, **k) for d in self._d])
        return broadcast

    def plot(self, **kw):                                  # terminal verbs defined explicitly
        from postgkyl import output
        return output.plot_datasets(self._d, **kw)
    def collect(self, **kw):  …                            # many → one
```

`GData.with_(*others) -> DatasetGroup` enables `a.with_(b).interp().sel(...).animate()`.

> **Naming note (`.and()`):** `RESEDIGN_NOTES` writes `data1.and(data2)`, but `and` is a
> Python **reserved keyword** — a method literally named `and` is a `SyntaxError`. We
> adopt **`.with_()`** (with optional `&` operator sugar) as the spelling. *Decision in §14.*

### 5.9 `_Loader` / `pg.load`

```python
# loader.py
class _Loader:
    def __call__(self, file, **gdata_kwargs):  return GData(file, **gdata_kwargs)
    def many(self, pattern, **kw):  return DatasetGroup([GData(f, **kw) for f in sorted(glob(pattern))])
    def simulation(self, name, *, model=None, cdim=None, vdim=None, dims=None, species=None):
        return Simulation(name, model=model, cdim=cdim, vdim=vdim, dims=dims, species=species)
load = _Loader()        # exported as pg.load
```

---

## 6. The verb vocabulary (the heart of the refactor)

Every CLI command maps to **one** `ops` verb and **one** underlying implementation. The
fluent method name == CLI command name == `ops.<verb>`. Aliases are method-level only.

| Verb (canonical) | Alias(es) | `ops` module | Underlying impl | Pattern | Notes |
|---|---|---|---|---|---|
| `select` | `sel` | `ops/select.py` | `data/select.py` `_select_arrays` | transform | absorb multiblock branch |
| `interpolate` | `interp` | `ops/interpolate.py` | `data/dg.py` `GInterpModal/Nodal` | transform | sets `interpolated=True` |
| `differentiate` | `diff` | `ops/differentiate.py` | `data/dg.py` | transform | |
| `integrate` | — | `ops/integrate.py` | `tools/calculus.py` | transform | |
| `fft` | — | `ops/fft.py` | `tools/fft.py` | transform | psd/iso flags |
| `mask` | — | `ops/mask.py` | numpy masked array | transform | fix latent typos |
| `magsq` | — | `ops/magsq.py` | `tools/mag_sq.py` | transform | |
| `relchange` | — | `ops/relchange.py` | `tools/rel_change.py` | 2-input | |
| `ev` | — | `ops/ev.py` | `commands/ev_cmd.py` registry | RPN | keep RPN; dunders reuse helpers |
| `fit` | — | `ops/fit.py` | `tools/fit.py` | transform | |
| `growth` | — | `ops/growth.py` | `tools/growth.py` | transform | |
| `agyro` | `mom_agyro` | `ops/agyro.py` | `tools/pressure_diagnostics.py` | 2-input | |
| `euler` | — | `ops/moments.py` | `tools/prim_vars.py` (variant by name) | derived | |
| `tenmoment` | — | `ops/moments.py` | `tools/prim_vars.py` | derived | |
| `mhd` | — | `ops/moments.py` | `tools/prim_vars.py` | derived | |
| `velocity` | — | `ops/moments.py` | `tools/prim_vars.py` | derived | |
| `temp` | — | `ops/moments.py` | `tools/prim_vars.py` | derived | |
| `current` | — | `ops/current.py` | `tools/accumulate_current.py` | n-input | |
| `energetics` | — | `ops/energetics.py` | `tools/energetics.py` | n-input | |
| `parrotate` / `perprotate` | `bparrotate`/`bperprotate` | `ops/rotate.py` | `tools/parrotate.py`,`perprotate.py` | 2-input | b* = coords preset |
| `transform_frame` | `transformframe` | `ops/transform_frame.py` | `tools/transform_frame.py` | 2-input | |
| `laguerre_compose` | `laguerrecompose` | `ops/laguerre.py` | `tools/laguerre_compose.py` | 2-input | |
| `pkpm` | — | `ops/pkpm.py` | laguerre + transform_frame | workflow | |
| `collect` | — | `ops/collect.py` (on group) | GData stacking | many→one | DatasetGroup method |
| `plot` | `pl` | `ops/plot.py` → `output.plot_datasets` | `output/plot.py` | output | terminal |
| `animate` | — | `ops/animate.py` | `output/plot.py` | output | terminal |
| `plotly` | `ply` | `ops/plotly.py` | `output/plotly.py` | output | terminal |
| `plotly_animate` | `ply-anim` | `ops/plotly.py` | `output/plotly.py` | output | terminal |
| `pyvista` | `pv` | `ops/pyvista.py` | `output/pyvista.py` | output | terminal |
| `write` | — | `GData.write` (exists) | `data/write.py` | output | terminal |
| `info` | — | `GData.info` (exists) | — | query | terminal |
| `pr` | — | `ops/pr.py` | numpy print | query | maps to `print(d)` |
| `grid`, `listoutputs`, `extractinput`, `val2coord`, `gk_*`, `trajectory` | — | `ops/…` | respective `tools/`/`data/` | mixed | port last |
| `load` | — | `loader.py` `_Loader` | `GData(...)` | loader | — |
| `status`/`activate`/`deactivate`, `style` | — | *(CLI-only)* | `DataSpace`/`load_style` | CLI state | no `ops` verb |

**Pattern legend:** *transform* = single dataset in→out (tag-or-overwrite); *2/n-input* =
combine inputs; *derived* = pick a `prim_vars` function by variable name; *output* =
terminal/visual; *query* = read-only; *many→one* = aggregation; *CLI state* = manages the
stack/figure, no numerical op.

---

## 7. Target scripts (the API exists to make these read well)

These become **doctests** (§12):

```python
import postgkyl as pg

# 1. Quick look
pg.load('elc_M0_0.gkyl').interp().plot()

# 2. Slice, keep a handle, inspect
n = pg.load('elc_M0_0.gkyl').interp().sel(z0=0.0)
n.plot();  print(n)                         # <GData (x:64)> + truncated values/grid

# 3. Compare two runs on one figure (varargs)
a = pg.load('runA_M0_0.gkyl').interp().sel(z1=0.0)
b = pg.load('runB_M0_0.gkyl').interp().sel(z1=0.0)
pg.plot(a, b)                               # or a.with_(b).plot()

# 4. Arithmetic via dunders / NumPy interop
ref  = pg.load('elc_M0_0.gkyl').interp()
late = pg.load('elc_M0_5.gkyl').interp()
err  = abs(late - ref) / ref
c    = np.sqrt(a**2 + b**2)                  # returns a GData with .grid
err.plot(title='relative change')

# 5. Reductions / spectral
pg.load('elc_M0_0.gkyl').interp().integrate().info()
pg.load('phi_0.gkyl').interp().sel(z1=0.0).fft().plot()

# 6/7. A whole simulation + time series (late phase)
sim = pg.load.simulation('gk55', model='gk', cdim=1, vdim=2)
sim.field('elc', 'M0').frames().interp().sel(z0=0.0).animate()
sim.field('elc', 'M0').frames().interp().integrate().collect().plot()
```

---

## 8. CLI migration: Click → Typer

### 8.1 The contract to preserve
From `pgkyl.py` / `PgkylCommandGroup`:
1. **Chaining** — `pgkyl f.gkyl interp sel --z0 0 plot` (Click `chain=True`).
2. **Abbreviation** — `pgkyl int` → `interpolate`.
3. **Explicit aliases** — `pl`, `ply`, `ply-anim`, `pv`.
4. **Bare filename = implicit `load`** — `pgkyl file.gkyl plot`.
5. **Global pre-options** — `--z0…--z5`, `-c`, `--c2p`, `--style`, `--batch-mode`, etc.

### 8.2 The risk
Typer is a thin layer **over Click**, but it does **not** expose Click's `chain=True`
multi-command pipeline as a first-class feature, and items 2–4 are implemented via a
**custom `click.Group` subclass**. A naive "all-Typer" rewrite would lose the chaining UX
that defines `pgkyl`. **This is the single biggest CLI risk.**

### 8.3 Recommended approach — hybrid (Typer commands under a custom chained group)
Because Typer compiles to Click (`typer.main.get_command(app)` yields a `click.Command`),
we can keep the **chaining/abbreviation/alias/bare-file machinery in a custom Click
`Group`** (as today) while declaring each **command with Typer's type-annotated style**
for cleaner option definitions and free help. Net effect:
- The root stays a `PgkylCommandGroup(chain=True)` (Click) — contract preserved.
- Individual commands move to Typer-style functions (modern, type-hinted, less boilerplate)
  and are registered into the group.
- Since every command body is now a ~3-line call into `ops`/`apply()`, the Click-vs-Typer
  surface is tiny either way.

> **Phase-0 spike (required):** build a 3-command throwaway proving `chain=True` +
> abbreviation + bare-file load works with Typer-declared commands under the custom group.
> If Typer cannot host the chained group cleanly, fall back to **"modernized Click"**
> (keep Click, adopt type-annotated decorators, still thin) — the architectural win (the
> `ops` seam) is independent of the CLI framework. *Decision in §14.*

### 8.4 Entry point & deps
- `pyproject.toml`: replace `click>=8.1.7` with `typer>=0.12` (pulls a compatible Click);
  `[project.scripts] pgkyl = "postgkyl.pgkyl:app"` (or keep `:cli` for the Click group).

---

## 9. NumPy interoperability & the modal/nodal guardrail

`RESEDIGN_NOTES` requires: *"guardrails on these methods so that we can't perform NumPy
operations on DG non-interpolated data."* **Today there is no reliable signal** —
`ctx["is_modal"]` is set by readers and never cleared after interpolation (§3).

**Design:**
1. **Add an explicit, authoritative state.** `ops.interpolate` and `ops.differentiate`
   set `ctx["interpolated"] = True` on their result. Expose a property:
   ```python
   @property
   def is_interpolated(self):
       # nodal-ready if it was never modal, or has been interpolated
       return (not self.ctx.get("is_modal", False)) or self.ctx.get("interpolated", False)
   ```
   *(Chosen over repurposing `is_modal` because other code reads `is_modal` to select the
   interp class; a dedicated key avoids semantic overload. Decision in §14.)*
2. **Guard the public numeric surface.** `_require_operable()` raises a clear error when
   a dunder or `__array_ufunc__` is invoked on raw modal data:
   ```python
   def _require_operable(self):
       if not self.is_interpolated:
           raise ValueError(
               "Cannot do array math on raw DG (modal) data — call .interp() first.")
   ```
3. **Grid compatibility.** Binary ops require matching grid shapes (scalars/plain arrays
   broadcast); mismatch → clear `ValueError` naming both shapes.
4. **`__array__`** returns the values so `np.asarray(d)` and `plt.plot(d.grid, d)` work.
   `__array_ufunc__` returns a new `GData` carrying the left operand's grid/ctx, so
   `np.sqrt(a**2 + b**2)` is itself a `GData` with `.grid` (matches the doc's example).

---

## 10. Backward compatibility & deprecation

- **Keep public names:** `pg.GData`, `pg.GInterpModal`, `pg.GInterpNodal`, `pg.tools`,
  `pg.output`, `pg.data` continue to import and behave as before.
- **Re-export moved logic:** `postgkyl.data.select` stays a working call that now
  delegates to `ops.select` (returning the historical `(grid, values)` for callers that
  expect it, via a compat shim). `GInterpModal(...).interpolate(overwrite=…)` unchanged.
- **`overwrite=` → `inplace=`:** verbs accept the new `inplace=` everywhere; where an old
  function had `overwrite=`, keep it as a deprecated alias for one release with a warning.
- **CLI behavior is byte-for-byte preserved** — verified by parity tests (§12). Only the
  *internals* of command functions change.
- New top-level names (`pg.load`, `pg.plot`, fluent methods) are **additive**.

---

## 11. Phased implementation roadmap

Each phase is independently shippable and keeps `pytest` green. Phases 1–5 are additive;
6 swaps command internals; 7–8 build the simulation/diagnostic layers; 9 hardens docs.

| Phase | Title | Deliverables | Green-keeping |
|---|---|---|---|
| **0** | Foundations & spikes | Add `[tool.pytest.ini_options]` (+ `--doctest-modules`, `testpaths`); scaffold `tests/cli`; run the **Typer-chaining spike** (§8.3); ratify §14 decisions. | No code paths changed. |
| **1** | `GData` ergonomics | `_result()`, `.copy()`, `__repr__`/`__str__`, `is_interpolated`, arithmetic dunders + reflected + `__neg__`/`__abs__`, `__array__`, `__array_ufunc__`, `_require_operable()`. Unit tests + doctests. | Pure additions; existing tests untouched. |
| **2** | `ops/` seam | Create `src/postgkyl/ops/`. Move `select`, `interpolate`, `differentiate` logic into `ops.*` returning `GData` via `_result`, honoring `inplace=`; `ops.interpolate` sets `interpolated=True`. Back-compat shim for `data.select`. Unit tests for `ops`. | Commands still call old paths or new `ops` with identical results. |
| **3** | Fluent methods | `GData.sel/select`, `interp/interpolate`, `diff`, `integrate`, `fft`, `mask`, `magsq` as 1-line delegations (lazy import). Doctests: golden scripts #1–#5 (#4 arithmetic/NumPy). | Additive. |
| **4** | `plot_datasets` + `pg.plot` | Factor multi-dataset loop + globalrange scan out of `commands/plot.py` into `output.plot_datasets`. Add `pg.plot`/`pg.animate`; `GData.plot/animate` delegate. CLI `plot` now calls `plot_datasets`. | `tests/test_plot.py` + CLI plot parity. |
| **5** | `DatasetGroup` + combining | `group.py` (broadcast `__getattr__` + terminal verbs), `GData.with_()`, `pg.plot(*datasets)` varargs, optional `&`. Optionally back `DataSpace` with it. | Additive; CLI unaffected. |
| **6** | Thin CLI + Typer | `commands/_apply.py` middleware; rewrite Pattern-A/B commands as thin shells calling `ops`. Migrate command declarations to Typer per Phase-0 decision; preserve chaining/abbrev/aliases/bare-file. Update `pyproject` deps + entry point. Migrate CLI tests (§12). | CLI parity tests + `tests/test_commands.py` ported. |
| **7** | Loader + Simulation | `loader.py` (`pg.load` callable + `.many` + `.simulation`); `sim.py` (`Simulation`, frame handles → `GData`/`DatasetGroup`). Doctests: golden #6–#7. | Additive. |
| **8** | Moment/diagnostic verbs | Port `agyro/euler/tenmoment/mhd/velocity/temp`, `current`, `energetics`, rotations, `transform_frame`, `laguerre`/`pkpm`, `collect` (group), plus `grid/listoutputs/extractinput/val2coord/gk_*`. Fluent methods + thin CLI for each. | Per-verb parity tests. |
| **9** | Docs & cleanup | All golden scripts as CI doctests; `pg.example(...)` fixture loader (§12); user migration guide; remove `commands/old/`, fix latent bugs (e.g. `mask` typos) opportunistically. | Full suite + doctests. |

---

## 12. Verification & CI strategy

The human's requirement — *"chock-full of examples that are verified through CI"* — is met
by doctests on the master class, plus parity tests guaranteeing the CLI never regresses.

1. **Keep `pytest` green every phase.** The existing 100+ tests are the safety net.
2. **Doctests as living examples.** Wire `--doctest-modules` into
   `[tool.pytest.ini_options]`. Every fluent verb's docstring carries a runnable `>>>`
   example. The golden scripts (§7) live in module docstrings.
3. **Portable fixtures for doctests.** Doctests must not depend on CWD. Add a tiny
   `pg.example(name)` helper that loads a bundled small sample (e.g. `shock-f-ser-p1`,
   `twostream-field-energy`) via `importlib.resources`, so `>>> pg.example('shock').interp()`
   runs anywhere in CI.
4. **CLI parity tests (new `tests/cli`).** Before Phase 6, capture golden outputs/states
   for representative chains (`interp sel --z0 0 plot --save`, `ev`, `collect`, `agyro`).
   After thinning/Typer, assert identical behavior. Use Typer's `CliRunner`
   (`from typer.testing import CliRunner`) — Typer compiles to Click, so this works; port
   the existing `ctx.invoke(...)` tests to it.
5. **`ops` unit tests.** Each verb tested directly at the `ops` layer (front-end-agnostic),
   covering `inplace=True/False`, tag/label, and grid/ctx propagation.
6. **REPL smoke checklist** (manual, per the design doc): `print(d)`, `d.values.shape`,
   `(d - d).values ≈ 0`, `np.sqrt(d**2).is_interpolated`, guardrail raises on raw modal,
   `pg.plot(d, d)`, `inplace=True` mutates / default leaves source unchanged.
7. **NumPy<2 & adios guards.** CI matrix keeps `numpy<2`; `adios2` paths remain optional
   (`try/except ImportError`).

---

## 13. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Typer can't host the chained-group UX cleanly | Med | Phase-0 spike; hybrid (custom Click group hosting Typer commands); fallback to "modernized Click". The `ops` win is framework-independent. |
| Guardrail signal unreliable (`is_modal` never cleared) | High (confirmed) | Add explicit `interpolated` flag set by `ops.interpolate`; `is_interpolated` property (§9). |
| `__array_ufunc__` surprises (reductions, `out=`, multi-output) | Med | Support `method=="__call__"` only initially; return `NotImplemented` otherwise; expand deliberately with tests. |
| `.copy()` accidentally re-reads files / shares mutable ctx | Med | Construct with `file_name=""`, copy `ctx` (ctor already copies), deep-copy arrays; unit-test aliasing. |
| Performance: default `inplace=False` copies large 5-D arrays | Med | `inplace=True` documented for big data; CLI uses `inplace=True` via `apply()`. |
| Hidden CLI behaviors (globalrange, batch_mode, multiblock, save naming) lost in `plot_datasets` extraction | Med | Move the loop verbatim first; parity tests on `tests/test_plot.py` + CLI golden chains. |
| Back-compat break for `data.select` returning `(grid, values)` | Low | Compat shim preserves the tuple return. |
| Scope creep across ~50 commands | Med | Land verbs by traffic (select/interp/plot first); §6 table tracks completion. |

---

## 14. Open decisions (recommendations baked in; confirm or override)

1. **Combine spelling:** `.with_()` + optional `&` (since `.and()` is a `SyntaxError`).
   *Recommended: `.with_()`.*
2. **Master class:** `GData`-as-fluent-facade + `DatasetGroup`, **not** a monolithic
   orchestrator. *Recommended as written (§4.2).*
3. **Guardrail flag:** dedicated `ctx["interpolated"]` + `is_interpolated` property, rather
   than overloading `is_modal`. *Recommended (§9).*
4. **CLI framework:** hybrid (custom Click chained group hosting Typer-declared commands);
   fall back to modernized-Click if the Phase-0 spike fails. *Recommended (§8.3).*
5. **Verb returns new by default; `inplace=` to mutate.** *Recommended (matches API_REDESIGN).*
6. **Method aliases** (`sel`/`select`, `interp`/`interpolate`): keep both, canonical name ==
   CLI command name. *Recommended.*

---

## 15. Critical files index

**Extend**
- `src/postgkyl/__init__.py` — export `load`, `plot`, `animate`; keep `GData`, `GInterp*`.
- `src/postgkyl/data/gdata.py` — `_result`, `.copy`, `__repr__`, dunders, `__array__`/
  `__array_ufunc__`, `is_interpolated`, fluent methods.
- `src/postgkyl/output/plot.py` — add `plot_datasets(list, **kw)` (loop from `commands/plot.py`).

**New**
- `src/postgkyl/ops/` — one module per verb (§6); the single source of truth.
- `src/postgkyl/group.py` — `DatasetGroup`.
- `src/postgkyl/loader.py` — `_Loader` / `pg.load`.
- `src/postgkyl/sim.py` — `Simulation` (Phase 7).
- `src/postgkyl/commands/_apply.py` — CLI tag-or-overwrite middleware.
- `tests/cli/` — Typer `CliRunner` parity tests; `pg.example()` fixture support.

**Thin**
- `src/postgkyl/commands/*.py` — ~3-line shells calling `ops`/`apply()`.
- `src/postgkyl/pgkyl.py` — root group (chaining/abbrev/alias/bare-file) hosting Typer commands.
- `src/postgkyl/commands/data_space.py` — optionally backed by `DatasetGroup`.

**Config**
- `pyproject.toml` — `click`→`typer`; entry point; `[tool.pytest.ini_options]` with
  `--doctest-modules` + `testpaths`.

---

*End of plan. Sections §14 (open decisions) and §8.3 (Typer spike) are the two gates to
clear before heavy implementation; everything in Phases 1–5 can proceed in parallel with
that since it is purely additive.*
