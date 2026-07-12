# `pgkyl` CLI tutorial

Every command below is real: it runs against the fixture files already
committed under `tests/test_data/`, and `tests/test_examples.py` replays each
one (via `click.testing.CliRunner`, from the repository root) as a
regression check. If the CLI's surface ever changes in a way that breaks one
of these commands, that test fails -- this file cannot silently drift out of
date the way a hand-maintained tutorial can.

Run any line yourself from the repository root, after `pip install -e .[test]`.

## 1. Inspect a file

`info` is the "what is this?" command -- dimensions, components, grid,
value range, and the DG basis/order it was written with.

```bash
pgkyl tests/test_data/rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl info
```

## 2. The chain: interpolate -> select -> plot

Raw `.gkyl` files hold DG *coefficients*; `interpolate` bridges them onto a
uniform mesh of plain values, `select` narrows down to one component (or one
coordinate slice), and `plot` renders it. `--batch-mode` (a top-level flag,
before the file) turns off the interactive window so this can run headless;
`--saveas` on `plot` writes a PNG instead.

```bash
pgkyl --batch-mode tests/test_data/rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl \
    interpolate select --comp 0 plot --saveas out.png
```

Every verb name has a short abbreviation Click resolves automatically
(`interp` -> `interpolate`, `sel` -> `select`, `pr` -> `print`, ...):

```bash
pgkyl tests/test_data/rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl \
    interp sel --comp 0 info
```

## 3. Discontinuity-preserving plots with `dg_local_poly`

`interpolate` produces a continuous refined mesh; `dg_local_poly` instead
evaluates the DG polynomial cell-by-cell and splices a NaN at every
inter-cell interface, so a plot shows genuine discontinuities instead of
smoothing over them -- useful for shocks or anything with jumps at cell
boundaries.

```bash
pgkyl --batch-mode tests/test_data/twostream-f-p2_0.bp \
    dg_local_poly select --z1 0.0 --z2 0.0 plot --saveas out.png
```

## 4. DynVector utilities: `print` and `fit`

`.bp` files without a spatial grid (diagnostics like a field-energy history)
are DynVectors: `print` dumps the raw array, and `fit` fits a model to it
(here, a straight line to `log(field energy)` vs. time -- the growth-rate
use case).

```bash
pgkyl tests/test_data/twostream-field-energy.bp print
pgkyl tests/test_data/twostream-field-energy.bp fit linear
```

## 5. Gyrokinetics: pre-named quantities and distribution functions

`gk_load_quantity` loads one of a registry of named gyrokinetic quantities
(list them with `--qlist`) straight from a simulation's naming convention --
no manual file paths. `--name`/`-n` is the simulation's *name prefix*
(not a path); `--path`/`-p` is the directory to look in.

```bash
pgkyl gk_load_quantity --qlist
pgkyl gk_load_quantity -q geo_int_jacobtot_inv -n rt_gk_tcv_iwl_1x2v_p1 \
    -p tests/test_data info
```

`gk_distf` reconstructs a full distribution function from the saved
`Jf`-times-Jacobian(s) files (here `-n` *does* include the directory, since
`gk_distf` has no separate `--path`):

```bash
pgkyl gk_distf -n tests/test_data/rt_gk_tcv_iwl_1x2v_p1 -s elc -f 250 \
    --jacobtot-inv-file tests/test_data/rt_gk_tcv_iwl_1x2v_p1-geo_int_jacobtot_inv.gkyl \
    info
```

## 6. Saving to another format

`save` writes the active dataset(s) out as `gkyl`/`txt`/`npy`/`vtk`.

```bash
pgkyl tests/test_data/twostream-f-p2_0.bp save --out distf --format npy
```

## 7. The working set: `status`

Every loaded file becomes a dataset in the session's working set; verbs
after it act on whichever datasets are currently active. `status` lists
them.

```bash
pgkyl tests/test_data/rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl status
```

## See also

- `pgkyl --help` lists every registered command, grouped by section
  (Verbs / Diagnostics / Render / Utility).
- `pgkyl <command> --help` documents that command's options -- most carry a
  worked example in their docstring, e.g. `pgkyl dg_local_poly --help`.
- `examples/scripts/` is the Python-script equivalent of this tutorial (the
  fluent `GData` API instead of the chained CLI).
