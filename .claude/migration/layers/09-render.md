# Layer 09 — render (visualization backends)

## Mission

Bring `render/` from "basic matplotlib plot" to the full old feature set:
multi-panel figures, animation, movie export, the pgkyl colorbar, style
loading, plus the plotly and pyvista backends. Render imports `core`/
`numerics` only and requires interpolated (field-domain / point-values) data.

## Read first

1. `.claude/DOCTRINE.md`, `.claude/migration/PYTHON_PRINCIPLES.md`
2. `src/postgkyl/render/matplotlib.py` and `ops/plot.py` — current seam
3. Sources: `src_bak/postgkyl/output/{plot.py,plotly.py,pyvista.py}`,
   `src_bak/postgkyl/utils/{axis_and_grid_prep.py,load_plot_data.py,latex_conversion.py,load_style.py}`
4. Old style assets: check `src_bak/` and pyproject's package-data
   (`postgkyl.output` ships `*.mplstyle`, `*.js`) — relocate any style files
   into `render/` and update `[tool.setuptools.package-data]` accordingly.

## Source → target map

| Source | Target | Adaptation |
|---|---|---|
| `output/plot.py` (`plot_datasets`, `pgkyl_colorbar`, figure layout) | `render/matplotlib.py` (extend) | Merge into the existing `plot(*datasets, ...)`: multi-panel (one panel per component / per dataset per the old semantics), colorbar, log axes, vmin/vmax, aspect, labels via `latex_conversion`. Keep the current function's signature backward-compatible; grow it with keyword-only options. |
| `output/plot.py` (`animate`, `_save_frames`, `_compile_movie`) | `render/animate.py` | Frame iteration over a sequence of datasets → `FuncAnimation` / saved frames / movie compile (subprocess to ffmpeg stays isolated here; probe availability, raise clearly if missing). |
| `utils/axis_and_grid_prep.py` | `render/_prep.py` | Axis/label/shift/scale prep, private helper. |
| `utils/load_plot_data.py` | `render/_prep.py` | Merge; it is the same concern (dataset → plottable arrays). |
| `utils/latex_conversion.py` | `render/labels.py` | `latex_to_unicode`, `latex_to_html`. |
| `utils/load_style.py` | `render/style.py` | Matplotlib rc/style application from an .mplstyle path — WITHOUT the typer context; `apply_style(path_or_name)` pure-ish (mutates mpl rcParams — that is its one documented effect). CLI wiring waits for layer 13. |
| `output/plotly.py` | `render/plotly.py` | `plotly` + `plotly_animate` + rotating-figure export. plotly/kaleido are hard deps. |
| `output/pyvista.py` | `render/pyvista.py` | 3-D volume/isosurface. pyvista is a hard dep but needs a GL context — every entry point must work headless-or-raise-cleanly (`off_screen=True`). |

Mapped grids: per MAPPING.md's BACKEND row — 2-D pcolormesh accepts 2-D X/Y
nodal arrays; 1-D mapped axes only need center computation on non-uniform
edges. Verify with a test on a mapped dataset (layer 08's map verb exists).

`ops/plot.py` keeps delegating; if animation needs a verb, add `ops/animate.py`
following the verb contract (authorized by this file) and re-export it.

## Tests

Use the Agg backend (`matplotlib.use("Agg")` before pyplot import in each test
module) and close figures in teardown. Port the assertion styles from
`tests_bak/{test_plot.py,test_plot_datasets.py,test_output.py}` (76 tests):
assert on the returned figure/axes structure (panel count, axis labels, image
array extents, colorbar presence), never on pixels. Animation: build 3 frames
from `tests/test_data/generated/` series, assert frame count and that saving
frames writes files to `tmp_path`; skip movie-compile test if ffmpeg absent
(`shutil.which`). Plotly: assert on the figure dict (traces, layout). Pyvista:
`pytest.importorskip` + try off-screen; skip cleanly if no GL. Labels: exact
string cases for latex_to_unicode/html.

## Definition of done

1. Full suite green; architecture tests pass (`render → core, numerics` only).
2. `--cov=postgkyl.render` ≥ 85% (GUI/GL branches justified-skippable).
3. Style files relocated + package-data updated; `pip install -e .` still works.
4. Report: feature parity table vs `output/plot.py` (each old kwarg: ported /
   dropped+why), backends' skip conditions, coverage, pytest summary.
