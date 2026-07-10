# Layer 09 — render: feature parity table (Definition of Done #4)

Written post hoc, in response to review criticism C3
(`.claude/migration/reviews/09-render-review.md`). Ported/dropped status for
every keyword the old tree accepted, checked against
`src_bak/postgkyl/output/{plot.py,plotly.py,pyvista.py}` and the new
`src/postgkyl/render/{matplotlib.py,plotly.py,pyvista.py}` +
`src/postgkyl/ops/{plot.py,animate.py}`.

## `output/plot.py::plot()` -> `render/matplotlib.py::plot()`

The layer instruction file's own source->target map scopes this port to
"multi-panel, colorbar, log axes, vmin/vmax, aspect, labels" — everything
else below is a **deliberate** scope-narrowing per that map, not an
oversight, unless marked otherwise.

| Old kwarg | Status | Why |
|---|---|---|
| `data`, `args` | dropped (`args`) / changed (`data`) | `data` is now `*datasets: GDataState`, no CLI arg-string dual input (PYTHON_PRINCIPLES #9); `args` was CLI-string plumbing (`scatter` flag piggybacked on it), unused by the script API. |
| `figure` | ported, renamed `fig` | Same "reuse this figure" hook, used by `render/animate.py` to redraw one figure per frame. |
| `squeeze`, `num_axes`, `start_axes` | dropped | `squeeze`/`num_axes`/`start_axes` selected/relabeled a *subset* of a dataset's own axes for CLI multi-arg plotting; the fluent surface has no CLI arg parsing to feed them from — `.sel()` upstream replaces this. |
| `num_subplot_row`, `num_subplot_col` | ported | Same names/semantics, `render/_prep.py::subplot_grid`. |
| `streamline`, `sdensity`, `quiver` | dropped | Vector-field overlays; no vector-valued dataset support was added in this layer (out of the instruction file's promised scope). |
| `contour`, `clevels`, `cnlevels`, `cont_label` | dropped | Contour-line overlay mode; not in the promised scope (2-D is pcolormesh only). |
| `diverging` | ported | `cmap=None` + `diverging=True` -> `"RdBu_r"`, same as old. |
| `lineouts` | dropped | Old cross-section-line extraction feature; no 3-D-to-1-D lineout verb exists yet (would need a new `ops` verb, out of `render`'s layer boundary). |
| `xmin`,`xmax`,`ymin`,`ymax`,`zmin`,`zmax` | dropped | Old per-axis crop by rebuilding a sliced `(grid, values)` pair before plotting; superseded by `.sel()` (layer 07) — the equivalent crop is a verb-layer operation now, not a render-time one. |
| `xscale`,`yscale`,`zscale`,`xshift`,`yshift`,`zshift` | dropped (2-D backend) | The 2-D matplotlib panel has no 3rd (`z`) coordinate axis to scale, and the promised scope list ("labels") only covers label text, not a coordinate transform; restored instead in `plotly()`/`pyvista()` where they were a real regression (C1) since those genuinely have 3-D coordinates. A future layer could add 2-D `x/yscale` if requested. |
| `relax` | dropped | Old "don't error on axis mismatch across overlaid datasets" escape hatch; the new `numerics.grids_compatible`-based checks intentionally do not have a bypass. |
| `style`, `rcParams` | ported | Same names/semantics via `render/style.py`. |
| `legend`, `label_prefix` | ported (`legend` via per-dataset `labels`) | 1-D overlay legend, `label_prefix` folded into the caller building `labels`. |
| `legend_axis` | dropped | Old multi-panel "only this one panel gets a legend" placement option; every panel gets its own legend/labels now (simpler, matches "one idea" — doctrine III). |
| `colorbar` | ported | Same name/semantics. |
| `xlabel`, `ylabel`, `clabel` | ported | Same names/semantics, `render/_prep.py::resolve_axis_labels`. |
| `title` | ported | Same name/semantics (`fig.suptitle`). |
| `subplot_titles`, `subplot_xlabels`, `subplot_ylabels` | dropped | Per-panel comma-string label overrides (CLI-string parsing); out of scope without the CLI layer (layer 13) that would parse them. |
| `logx`, `logy`, `logz` | ported | Same names/semantics (`ax.set_xscale`/`set_yscale`/`LogNorm`). |
| `fixaspect` | dropped, `aspect` ported | `fixaspect` was a boolean shortcut for a specific `aspect` value in the old CLI; the single `aspect` kwarg (`ax.set_aspect`) subsumes it. |
| `edgecolors`, `markersize`, `linewidth`, `linestyle`, `color` | dropped | Per-dataset Matplotlib style overrides for 1-D lines; not in the promised scope ("labels", not per-line style) — `style`/`rcParams` cover the global case. |
| `showgrid`, `hashtag`, `xkcd` | dropped | Cosmetic extras (grid toggle, watermark, xkcd-font mode); ported for `plotly()`/`pyvista()` (already present there) but not added to the 2-D Matplotlib path, which the instruction file scopes narrower. |
| `figsize` | ported | Same name/semantics. |
| `jet`, `cmap` | `cmap` ported, `jet` dropped | `cmap` unchanged; `jet` was a deprecation-warning shim for the old default colormap name — no longer a default anyone can select into by accident. |
| `vmin`, `vmax` (new) | n/a, new name | The old tree spelled these `zmin`/`zmax` for the *color* floor/ceiling in `plot_datasets`' `cutoffglobalrange` path; the new `vmin`/`vmax` are the direct, always-available equivalent (promised by the instruction file). |

## `output/plot.py::plot_datasets()` orchestration kwargs

| Old kwarg | Status | Why |
|---|---|---|
| `globalrange`, `cutoffglobalrange` | dropped | Cross-dataset value-range auto-scan (percentile cutoff); no verb computes this yet — would need a new multi-dataset reduction, out of `render`'s boundary (mechanics, not a "what"). |
| `subplots` (comma-string), `no_legend`, `multiblock` | dropped | CLI-string parsing / multiblock-file orchestration; multiblock loading is a `loaders/`-layer concern, not `render`'s. |
| `save`, `saveas`, `dpi`, `batch_mode` | ported (as `save`) | `matplotlib.py::plot(save=...)` covers the single-figure save case; `saveframes`/`batch_mode` map onto `render/animate.py`'s frame-saving instead. |
| `show` | ported | Same name/semantics. |

## `output/plot.py::animate()` -> `render/animate.py::animate()`

| Old kwarg | Status | Why |
|---|---|---|
| `interval`, `show`, `save`, `saveas`, `fps`, `dpi` | ported | Same names/semantics (`FuncAnimation`, movie export via `ffmpeg` subprocess). |
| `fixed_range`, `cutoffglobalrange` | dropped | Same global-range-scan feature as `plot_datasets`, not reimplemented (see above). |
| `notitle` | dropped | Inverse boolean of `title`; the new `render/matplotlib.py::plot(title=None)` already omits the title with `None` as the default, so the extra flag was redundant. |
| `nproc`, `tmpdir` | dropped | Multiprocess frame-saving; `render/animate.py`'s `_save_frames` writes serially to `tmp_path`/a caller-given prefix, matching the layer instruction file's simpler test-facing contract. |
| `saveframes` | ported | Same name/semantics (prefix -> per-frame file paths). |

## `output/plotly.py::plotly()` -> `render/plotly.py::plotly()`

All kwargs ported with identical semantics **except**:

| Old kwarg | Status | Why |
|---|---|---|
| `num_axes` | dropped | CLI "restrict to this many components" override, orthogonal to `squeeze`; no CLI comma-string source to parse it from on the fluent surface. Use `.sel(comp=...)` upstream instead. |
| `data` type | changed | `GDataState`, not `GData \| (grid, values)` (no dual-input signature, PYTHON_PRINCIPLES #9). |
| `figsize` | changed (spelling only) | No longer accepts the CLI's comma-string spelling; same `(w, h)` tuple semantics. |
| `xscale`,`yscale`,`zscale` | **restored** (was a regression, C1) | Ported with identical semantics: multiply the plotted coordinates (and, in surface mode, the height/color value) exactly as `src_bak/postgkyl/output/plotly.py:720,727-728,744-746` did. |

## `output/pyvista.py::pyvista()` -> `render/pyvista.py::pyvista()`

All kwargs ported with identical semantics **except**:

| Old kwarg | Status | Why |
|---|---|---|
| `args`, `**kwargs` | dropped | CLI-string plumbing, unused by the script API. |
| `data` type | changed | `GDataState`, not `GData \| (grid, values)`. |
| `xscale`,`yscale`,`zscale` | **restored** (was a regression, C1) | Ported with identical semantics: the mesh itself stays normalized to `aspect_ratio` (PyVista handles non-integer extents poorly), but the displayed bounding-box tick range (`show_bounds(axes_ranges=...)`) and axis labels now again reflect the requested shift/scale, matching `src_bak/postgkyl/output/pyvista.py:267-273`. |

## Coverage / skip conditions (Definition of Done #4, cont.)

See the review document's Coverage section for the full per-line breakdown;
summary: `plotly.py` 96% (defensive numeric-helper branches + two
unreachable-through-the-public-API `ValueError` guards), `pyvista.py` 91%
(one `except`-passthrough never hit before the two `ValueError` guards, plus
GL-window/spin-timer/optional-`trame`-export code paths gated by
`pytest.importorskip`/`needs_gl`, per PYTHON_PRINCIPLES #17), all other
`render/*` modules and `ops/plot.py`/`ops/animate.py`/`ops/_materialize.py`
100%.

## Pytest summary

`PYTHONPATH=src python -m pytest tests/ -q` — see the Resolutions section of
the review document for the exact final line.
