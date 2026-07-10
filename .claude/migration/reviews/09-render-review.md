# Layer 09 — render: review

Scope reviewed: working-tree diff on top of commit `d4c801c` (08-ops-physics),
i.e. everything `git status --short` reports as modified/untracked under
`src/postgkyl/render/`, `src/postgkyl/ops/animate.py`,
`src/postgkyl/ops/__init__.py`, `pyproject.toml`, and the corresponding
`tests/test_render_*.py` / `tests/test_ops_animate.py`.

## Doctrine adherence

- **0. Locality of reasoning** — adheres. Each backend module
  (`matplotlib.py`, `plotly.py`, `pyvista.py`, `animate.py`) is readable on
  its own; shared prep lives in one place (`_prep.py`).
- **I. Data is inert. Functions transform.** — adheres. `PlotPanel`
  (`src/postgkyl/render/_prep.py:96-105`) is a frozen dataclass; every
  backend function takes a `GDataState` and returns a figure/None, no
  stateful objects introduced.
- **II. Make illegal states unrepresentable.** — not applicable / adheres.
  No new type is introduced that could represent an illegal plot state;
  `PlotPanel` only holds already-validated arrays.
- **III. A function is one idea.** — mostly adheres. `plotly()`
  (`src/postgkyl/render/plotly.py:362-603`) is long (~240 lines) but this is
  inherited structure from `src_bak/postgkyl/output/plotly.py` (nearly the
  same length) with the same internal factoring
  (`_apply_plot_style`/`_plotly_colorscale`/`_resolve_plotly_aspect`/
  `_scene_axis`); the layer's job was to port, not to refactor, so I do not
  count this as a new violation.
- **IV. The signature tells the whole truth.** — **violates.** The
  `plotly()` docstring (`src/postgkyl/render/plotly.py:394-398`) asserts
  "the signature and semantics are unchanged except that `data` is a
  `GDataState`... and `num_axes`/`figsize` no longer accept the CLI's
  comma-string spellings." This is false: `xscale`, `yscale`, `zscale` were
  removed from the signature entirely (present in
  `src_bak/postgkyl/output/plotly.py:470-472`, absent from
  `src/postgkyl/render/plotly.py:362-386`), and `num_axes` itself was
  removed, not merely reformatted. See C1.
- **V. Every fact has one home.** — **violates.** The "modal dataset must be
  bridged to a plottable NumPy shadow, else raise" fact is retyped verbatim
  in both `src/postgkyl/ops/plot.py:21-36` and
  `src/postgkyl/ops/animate.py:21-37` (same error message, same
  `dg.rep.materialize` call) instead of sharing one function. See C2.
- **VI. Separate what from how.** — adheres. `render/` still imports only
  `core`/`numerics` (verified by the import-contract test); `ops/animate.py`
  does the GDataState-unwrapping, `render/animate.py` does the Matplotlib
  mechanics.
- **VII. Notation is execution; lowering is transliteration.** — **violates**
  for the same reason as IV: the `plotly()` docstring is the "spec" a caller
  reads, and it misrepresents what the lowering actually does (drops
  `xscale`/`yscale`/`zscale`, which fed directly into the rendered
  coordinates/colors in the old code — `src_bak/postgkyl/output/plotly.py:720,727-728,744-746`
  — not just labels).
- **VIII. Earn your abstractions.** — **violates** (same finding as V): a
  second use of the "materialize modal → NumPy shadow" logic already exists
  (`ops/animate.py`) and the layer's own precedent
  (`src/postgkyl/ops/_guards.py`, introduced in 08-ops-physics specifically
  to centralize a repeated verb-level check) shows the correct pattern was
  known and simply not applied here.
- **IX. An abstraction is a contract.** — adheres. `PlotPanel`'s guarantee
  (squeezed grid/values + resolved labels) is honored consistently by
  `matplotlib.py`.
- **X. Trust the most formal thing first.** — adheres for what is tested:
  `test_render_plotly.py`/`test_render_pyvista.py` assert on real numeric
  values (`assert_allclose` on ranges, colorscales, z-data), not just
  shapes. It does not extend to the dropped scale parameters, since no test
  exercises what was removed (there is nothing left to assert against).

## Principles adherence (PYTHON_PRINCIPLES.md)

- **#1 absolute imports** — adheres, all `postgkyl.*`.
- **#2 respect the layer DAG** — adheres; `render: {core, numerics}` and
  `ops: {..., render, ...}` edges are unchanged from `_ALLOWED`, no new edge
  requested or added; `test_import_contract_no_violations` passes.
- **#3 optional deps guarded once at top** — adheres for `matplotlib`/
  `render.style`; **N/A** for `plotly`/`pyvista` since `pyproject.toml`
  lists them as hard deps (per the layer file), so no guard is required —
  confirmed no `try/except ImportError` needed and none added.
- **#4 no typer/ctypes** — adheres.
- **#5 `__init__.py` re-exports only** — adheres
  (`src/postgkyl/render/__init__.py`, `src/postgkyl/ops/__init__.py`).
- **#6 type-annotate public functions** — mostly adheres; `animate()`'s
  `data` parameter (`src/postgkyl/render/animate.py:157`,
  `src/postgkyl/ops/animate.py:40`) has no type annotation (inherently hard
  to spell — "dataset, or list of datasets, or list of lists" — but a
  `Iterable[GDataState] | Iterable[Sequence[GDataState]]` alias would have
  been possible). Minor.
- **#7 keyword-only options** — adheres throughout (`*datasets`/`data, *,
  ...` patterns).
- **#8 no mutable default arguments** — adheres (`aspect_ratio=(1,1,1)` is a
  tuple, immutable; dict/list defaults are `None`, resolved inside).
- **#12 frozen records** — adheres (`PlotPanel`).
- **#14 NumPy discipline** — adheres; `np.asarray` used at boundaries
  (`_prep.py:64`), no unexplained large-array copies spotted.
- **#15 docstrings** — mostly adheres, **except** the `plotly()` accuracy
  problem under IV/VII, and the narration comment under #16.
- **#16 comments state constraints, not narration** — **violates**, minor:
  `src/postgkyl/render/matplotlib.py:26` reads "-- ported from the old
  tree's `pgkyl_colorbar`," a changelog-style comment PYTHON_PRINCIPLES #16
  explicitly forbids ("git holds history").
- **#17 one test file per module, ~100% coverage** — adheres; see Coverage
  section (96%/89%/100%).
- **#18 tests assert values not shapes** — adheres; e.g.
  `test_surface_z_matches_values`, `test_axis_ranges_match_data_extent`,
  `TestSaveFrames`.
- **#19 tests independent/deterministic** — adheres; Agg backend set up
  front, figures closed in a fixture, `tmp_path` used for all file I/O,
  `ffmpeg`/GL/optional-dep gated with `skipif`/`importorskip`.
- **#21 copy liberally, never change numerical behavior silently** —
  **violates**: see C1. The scale-parameter drop is an undocumented
  behavioral change relative to `src_bak`.

## Criticisms

**C1 (major — undocumented numeric/feature regression).** `xscale`,
`yscale`, `zscale` existed in both `src_bak/postgkyl/output/plotly.py:470-472`
and `src_bak/postgkyl/output/pyvista.py:27` and fed directly into the
rendered coordinates/colors/axis bounds (not just labels — e.g.
`value = np.asarray(values[..., comp]) * zscale + zshift` at
`src_bak/postgkyl/output/plotly.py:720`, and the shift/scale-corrected
`axes_ranges` bounds tuple passed to `show_bounds` at
`src_bak/postgkyl/output/pyvista.py:267-273`). The new
`src/postgkyl/render/plotly.py:362-386` and
`src/postgkyl/render/pyvista.py:41-55` signatures drop all three scale
parameters entirely (only the shifts survive), and
`src/postgkyl/render/pyvista.py:229-237`'s `show_bounds` call drops the
`axes_ranges` argument outright, so the displayed axis bounds are always the
internal `[-aspect, aspect]`-normalized coordinates rather than the true
physical extent (with or without a shift/scale the user requested) — a
genuine display regression, not just a removed convenience. Worse,
`plotly()`'s docstring (`src/postgkyl/render/plotly.py:394-398`) claims the
signature is "unchanged except" for two unrelated, minor details, which is
false and will mislead the next person who trusts it.
*Failure scenario*: a caller migrating a script that did
`pg.plotly(d, zscale=1e3, xscale=0.01)` to convert units gets a hard
`TypeError: unexpected keyword argument 'zscale'` (loud, not silent) with a
plotly-3D scatter/volume/surface figure whose color range, height, and axis
extents can no longer be independently unit-converted from the shift; for
`pyvista()` the failure is quieter — the call still succeeds, but the
rendered axis tick labels are wrong (normalized `[-1,1]`-ish values instead
of the physical range), which nothing in the test suite can catch because
no pyvista test inspects `show_bounds`'s `axes_ranges` argument.
*Fix*: restore `xscale`/`yscale`/`zscale` with the old semantics in both
backends (or, if the decision is to intentionally simplify, correct the
`plotly()` docstring to say so and add the parity-table entry the
instruction file's Definition of Done requires).

**C2 (major — maintainability / doctrine V, VIII).** The "modal dataset must
be bridged through its NumPy shadow before rendering, else raise" logic is
duplicated verbatim between `src/postgkyl/ops/plot.py:21-36` and
`src/postgkyl/ops/animate.py:21-37` (identical error message text, identical
`dg.rep.materialize(...)` call). This is a second use of the same fact with
no shared home, despite this exact pattern (a repeated verb-level check)
having just been centralized one layer earlier into `ops/_guards.py`
(08-ops-physics).
*Failure scenario*: a future change to the modal-bridging contract (e.g. a
new representation, or a wording change to the error message) has to be
applied in two places by hand; missing one silently reintroduces
inconsistent error text/behavior between `.plot()` and `.animate()`.
*Fix*: factor `_materialize`/the inline block in `ops/plot.py` into one
shared helper (e.g. `ops/_materialize.py` or a function next to
`ops/_guards.py`) and have both verbs call it.

**C3 (moderate — process/spec non-conformance).** The instruction file's
Definition of Done item 4 requires "a feature parity table vs `output/plot.py`
(each old kwarg: ported / dropped+why)." No such report exists anywhere in
the repo (`.claude/migration/notes/` has no `09-render` entry, no PR
description was available to this reviewer). Given the size of the gap
between `src_bak/postgkyl/output/plot.py`'s `plot()`/`plot_datasets()` (which
supports `streamline`, `quiver`, `contour`, `lineouts`, per-panel
`subplot_titles`/`subplot_xlabels`/`subplot_ylabels`, `legend_axis`,
per-dataset `color`/`linewidth`/`linestyle`/`markersize`/`edgecolors`,
`hashtag`, `xkcd`, the `jet`-colormap deprecation warning, colorbar `extend`
arrows from `zmin`/`zmax` clipping, and the multi-dataset `globalrange`/
`cutoffglobalrange`/`multiblock`/`saveframes` orchestration in
`plot_datasets`) and the new `src/postgkyl/render/matplotlib.py::plot()`
(which supports none of the above), there is no way for a reviewer or future
maintainer to tell which omissions are deliberate scope-narrowing (the layer
file's own source→target map only promises "multi-panel, colorbar, log axes,
vmin/vmax, aspect, labels") versus accidental gaps.
*Fix*: write the required table (even post hoc) into
`.claude/migration/notes/09-render-parity.md` or the layer's commit message.

**C4 (minor — regressed error message).** The 2-D dimensionality guard's
error text lost its actionable suggestion:
`src/postgkyl/render/matplotlib.py:117` raises
`f"{num_dims}D plotting is not supported in this port"`, whereas
`src_bak/postgkyl/output/plot.py:113` raised "Only 1D and 2D plots are
currently supported. Please use 'plotly' or 'pyvista' for 3D data." The new
message tells the caller what failed but not what to do next, regressing
PYTHON_PRINCIPLES #10 ("names the offending value and the fix").
*Fix*: append the "use plotly()/pyvista() for 3-D data" hint.

**C5 (minor — doctrine/principles #16).** A changelog-style narration
comment: `src/postgkyl/render/matplotlib.py:26`, "`make_axes_locatable` --
ported from the old tree's `pgkyl_colorbar`." Harmless today, but exactly
the pattern #16 forbids since git already holds this history.

**C6 (minor — coverage-report honesty).** `test_render_plotly.py`'s
`test_html_export_zero_rotation_period_omits_script`
(`tests/test_render_plotly.py:334-341`) is named and commented as testing
the "static (no post_script)" branch of `save_rotating_plotly_figure`, but
measured coverage shows `src/postgkyl/render/plotly.py:293` (the
`fig.write_html(file_name)` line in that branch) is **not** covered. With
`rotation_period=1.0e18` (finite), `omega = 2*pi/1.0e18 ≈ 6.28e-18`, which is
representable and strictly `> 0.0` in float64, so the `if omega > 0.0:`
branch is taken instead — the test does not exercise what it claims to.
Either the test should pass `rotation_period=math.inf` (the only way to
drive `omega` to exactly `0.0`) or the branch is effectively dead code for
all finite periods and should be reconsidered.

**C7 (minor — test gap, pyvista).** `mesh_clip_plane` is exercised only in
contour mode (`tests/test_render_pyvista.py:73-74`,
`test_clip_plane_does_not_raise`, default `is_contour=True`); the volume-mode
branch at `src/postgkyl/render/pyvista.py:208-211`
(`pl.add_mesh_clip_plane(grid3d, ...)`) has no matching test, unlike its
`mesh_slice_plane` sibling which does test both modes
(`test_mesh_slice_plane_contour_mode_does_not_raise` /
`test_mesh_slice_plane_volume_mode_does_not_raise`).

## Coverage

Measured with `PYTHONPATH=src python -m pytest tests/ -q --cov=postgkyl --cov-report=term-missing`
(running `--cov` scoped to just the render/animate modules triggers an
unrelated `numpy`/coverage double-import error in this environment when the
full `tests/` collection runs; the whole-package run below does not have
that problem and reports the same per-file numbers):

```
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src/postgkyl/ops/animate.py                   19      0   100%
src/postgkyl/render/__init__.py                5      0   100%
src/postgkyl/render/_prep.py                  68      0   100%
src/postgkyl/render/animate.py               102      0   100%
src/postgkyl/render/labels.py                 25      0   100%
src/postgkyl/render/matplotlib.py             77      0   100%
src/postgkyl/render/plotly.py                330     13    96%   106, 121-124, 137, 152, 160, 163, 189, 293, 329, 335, 341, 347
src/postgkyl/render/pyvista.py               114     12    89%   32-33, 209, 245-249, 252, 260, 267-268, 273
src/postgkyl/render/style.py                  11      0   100%
```

All files clear the layer's 85% bar comfortably. Do the gaps hold up?

- `plotly.py` 106, 121-124, 137, 152, 160, 163, 189: defensive/edge branches
  in the small numeric helpers (`_opacity_mapping`'s malformed-colorscale
  fallback, `_finite_range`'s all-NaN fallback, `_log_colorbar_ticks`'
  non-finite/rounding edges, `_apply_log_colorscale`'s degenerate-range
  guard) — plausible as "defensive, never hit with well-formed inputs from
  this module's own callers," but this justification is not written down
  anywhere (no report exists, C3). 329/335/341/347 are the
  `_prepare_3d_coordinates`/`_prepare_2d_coordinates` `ValueError` guards for
  a wrong coordinate count — legitimately unreachable through the public
  `plotly()` entry point (which always builds exactly 2 or 3 coordinate
  arrays from `grid`), so an "unreachable through the public API" label
  would hold up if written down. 293 is **not** a good gap — see C6, the
  test that was supposed to cover it doesn't.
- `pyvista.py` 32-33: the `except (RuntimeError, ValueError): raise`
  passthrough in `_require_gl_context` is never hit because the two
  `ValueError`s in `pyvista()` are both raised before entering the wrapped
  callable — plausible but undocumented. 245-249/252 (spin timer/click
  callbacks) and 260/267-268 (`.html`/`.vtksz` export, gated behind the
  optional `trame`/`trame_vtk` packages) and 273 (`pl.show()`, interactive
  only) are legitimately environment-gated per PYTHON_PRINCIPLES #17. 209
  (`mesh_clip_plane` in volume mode) is a real, avoidable gap — see C7.

## Verdict

**PASS WITH FIXES.** The layer's mechanics are solid: the full suite passes
(1053 passed, 2 skipped), all four architecture tests pass unchanged,
package-data relocation works end to end (`pip install -e .` verified), the
ported numeric helpers I checked line-by-line against `src_bak`
(`_log_colorbar_ticks`, `_apply_log_colorscale`, `_opacity_mapping`,
`squeeze_collapsed_axes`'s curvilinear-mean handling, `_frame_value_range`'s
percentile-cutoff math, the pgkyl colorbar) reproduce the old arithmetic
exactly, and coverage clears the bar with only small, mostly-justifiable
gaps. The reason this isn't a plain PASS is C1: a real, silently-dropped
numeric feature (`xscale`/`yscale`/`zscale`) spanning two backends, paired
with a docstring that affirmatively (and incorrectly) claims parity — that
is exactly the kind of "spec becomes a lie" the doctrine warns against, and
it is compounded by C3 (no parity report exists to tell a maintainer this
was intentional) and C2 (duplicated verb logic that the layer's own
immediately-preceding precedent, `ops/_guards.py`, shows how to avoid). None
of these require a re-implementation — they are targeted, well-scoped fixes
(restore or correctly document the dropped scale kwargs, extract one shared
`_materialize` helper, write the parity table, fix two minor
messages/comments/tests) — hence PASS WITH FIXES rather than FAIL.

## Resolutions

**C1: FIXED.** Restored `xscale`/`yscale`/`zscale` in both backends with the
old semantics, verbatim:
- `src/postgkyl/render/plotly.py`: signature restores `xscale`/`yscale`/
  `zscale` (line ~366-368); `resolve_axis_labels(...)` now passes them
  through (line ~424); coordinate/value computation restores
  `value = np.asarray(values[..., comp]) * zscale + zshift` (line ~463) and
  `x = (... + xshift) * xscale` / `y = (... + yshift) * yscale` / (surface
  mode, line ~470-471) and `x/y/z = (... + shift) * scale` (volume mode,
  line ~484-486) — matching `src_bak/postgkyl/output/plotly.py:720,727-728,744-746`
  exactly.
- `src/postgkyl/render/pyvista.py`: signature restores `xscale`/`yscale`/
  `zscale` (line ~53-54); `resolve_axis_labels(...)` passes them through
  (line ~120-122); the `show_bounds` call now computes and passes
  `axes_ranges` from `pl.bounds` and the pre-normalization `xmin`/`xmax`/etc.
  (line ~238-254), matching `src_bak/postgkyl/output/pyvista.py:267-273`
  exactly (the mesh itself stays normalized to `aspect_ratio`; only the
  displayed tick range/labels carry the physical scale/shift, exactly as
  the old code did).
- `plotly()`'s docstring (`src/postgkyl/render/plotly.py:394-405`) now states
  precisely what changed: `data`'s type, `figsize`'s comma-string spelling,
  and `num_axes`'s removal (with the reason and the `.sel(comp=...)`
  replacement) — no more false "unchanged except" claim.
- New tests: `test_scale_and_shift_apply_to_surface_coordinates_and_height`,
  `test_scale_and_shift_apply_to_volume_coordinates`,
  `test_zscale_zshift_apply_to_volume_color_value`
  (`tests/test_render_plotly.py`) and
  `test_show_bounds_axes_ranges_reflect_scale_and_shift`
  (`tests/test_render_pyvista.py`) assert on the actual numeric effect of
  the restored kwargs, not just that they're accepted.

**C2: FIXED.** Extracted the duplicated "bridge modal data to its plottable
NumPy shadow, else raise" logic into
`src/postgkyl/ops/_materialize.py::materialize_for_render`, mirroring the
`ops/_guards.py` precedent this review cited. `src/postgkyl/ops/plot.py` and
`src/postgkyl/ops/animate.py` both now import and call the one shared
function; neither retypes the error message or the `dg.rep.materialize` call
anymore. Verified by the pre-existing `tests/test_ops_animate.py::test_raw_modal_frame_without_representation_raises`
and `tests/test_postgkyl.py::test_conversions_are_always_explicit`'s
`a.plot(show=False)` assertion, both still green against the refactored code
(`tests/test_ops_animate.py`, `tests/test_postgkyl.py:280`).

**C3: FIXED.** Wrote the required feature-parity table to
`.claude/migration/notes/09-render-parity.md`: every kwarg of
`output/plot.py::plot()`/`plot_datasets()`/`animate()` and
`output/plotly.py::plotly()`/`output/pyvista.py::pyvista()`, marked
ported/dropped+why, including the two just-restored `xscale`/`yscale`/
`zscale` entries and an explicit note on why the 2-D Matplotlib backend does
not get them (no 3rd coordinate axis, and the instruction file's promised
scope for that backend is narrower than the 3-D backends').

**C4: FIXED.** `src/postgkyl/render/matplotlib.py`'s dimensionality-guard
message now reads `f"{num_dims}D plotting is not supported here; use
plotly() or pyvista() for 3D data."` (line ~117-119), restoring the old
tree's actionable hint. `tests/test_coverage_leaf.py::test_plot_rejects_more_than_two_dimensions`
(`match="plotting is not supported"`) still passes unchanged since the
matched substring survives.

**C5: FIXED.** Removed the changelog-style comment on
`src/postgkyl/render/matplotlib.py:24-26`; the docstring now states only the
constraint (`make_axes_locatable` appends beside `ax` instead of shrinking
it), not the porting history.

**C6: FIXED.** `tests/test_render_plotly.py::test_html_export_zero_rotation_period_omits_script`
had two bugs, not one: the reviewed version passed `1.0e18` positionally
into `polar_angle` (not `rotation_period`, which stayed a normal `2.0`,
`omega = 2*pi/2.0`, definitely `> 0.0`) — my first fix attempt (swapping in
`math.inf` at the same position) reproduced the identical mistake and
actually failed outright (`np.sin`/`np.cos` of `deg2rad(inf)` -> NaN,
confirmed by the `RuntimeWarning: invalid value encountered in sin/cos` this
produced). The test now calls every angle/period argument by keyword
(`starting_azimuthal_angle=0.0, fps=10, polar_angle=60.0,
rotation_period=math.inf, radius=2.0`) and asserts
`"recomputeRotationParams" not in out.read_text()` (a JS identifier from
`rotation_controls.js` that only appears in the embedded post-script). Full
per-file coverage (`--cov=postgkyl --cov-report=term-missing`, run over the
whole `tests/` collection per the review's own workaround for the scoped-run
double-import issue) confirms `src/postgkyl/render/plotly.py:293` is no
longer in the missing-lines list.

**C7: FIXED.** Added
`tests/test_render_pyvista.py::TestPyvista::test_clip_plane_volume_mode_does_not_raise`
(`pyvista(_volume(), show=False, is_contour=False, mesh_clip_plane=True)`),
mirroring the existing `mesh_slice_plane` contour/volume pair. Coverage
confirms `src/postgkyl/render/pyvista.py`'s volume-mode `mesh_clip_plane`
branch (line 215 post-fix) is no longer in the missing-lines list.

### Final verification

Full suite: `PYTHONPATH=src python -m pytest tests/ -q` -> `1058 passed, 2
skipped in 56.95s`. All four architecture tests
(`test_facade_is_pure_reexport`, `test_import_contract_no_violations`,
`test_foreign_floor_confined_to_ffi`, `test_import_graph_is_acyclic`) verified
green in isolation. Coverage (`--cov=postgkyl --cov-report=term-missing`,
whole-suite run): `render/__init__.py` 100%, `render/_prep.py` 100%,
`render/animate.py` 100%, `render/labels.py` 100%, `render/matplotlib.py`
100%, `render/plotly.py` 96% (330 stmts, 12 miss — one fewer missing line
than before, C6's line 293 now covered; remaining gaps are the
defensive/unreachable-through-the-public-API branches the review already
judged acceptable), `render/pyvista.py` 91% (116 stmts, 11 miss — one fewer
missing line than before, C7's volume-mode `mesh_clip_plane` branch now
covered; remaining gaps are the GL-window spin/click-callback code and the
optional-`trame`-gated `.html`/`.vtksz`/interactive-`show()` paths, per
PYTHON_PRINCIPLES #17), `render/style.py` 100%, `ops/plot.py` 100%,
`ops/animate.py` 100%, `ops/_materialize.py` (new) 100%.
