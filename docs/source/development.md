# Developing Postgkyl

Create and activate an environment as described in [Installation](installation.md),
then install the checkout directly in editable mode:

```bash
python -m pip install -e '.[test]'
```

Python edits take effect immediately. After native changes, repeat the install
command; it builds your existing Gkeyll checkout, including local edits.

## Tests

[pytest](https://docs.pytest.org/) runs the automated tests. From the
`postgkyl` folder, run:

```bash
python -m pytest tests/
```

The suite treats unexpected warnings as errors and validates marker names and
configuration. Add `-v` for individual results or `--durations=20` to find slow
tests. Documentation tests execute the complete example gallery through Python
and the CLI, so allow longer timeouts for integration runs.

Select a subset with `-m`:

```bash
python -m pytest -m compatibility
POSTGKYL_REQUIRE_GKEYLL=1 python -m pytest -m native --timeout=120
python -m pytest -m "render and not external_tool"
python -m pytest -m external_tool --timeout=180
python -m pytest -m "not external_tool" --timeout=600 --cov=postgkyl --cov-branch
```

Native CI requires the bridge instead of silently skipping native tests, and
coverage CI enforces the 99% threshold configured in `pyproject.toml`.
External renderer tests require Chrome and/or ffmpeg.

For pure-Python compatibility testing, install from a fresh checkout with
`POSTGKYL_SKIP_GKEYLL_BUILD=1 python -m pip install -e '.[test]'`, then run the
`compatibility` subset. This switch skips compilation; it does not remove native
artifacts from an existing editable checkout. Normal installations build the
bridge.

## Formatting

After installing the developer tools above, enable the checks that run
before a Git commit and run them over all tracked files:

```bash
pre-commit install
pre-commit run --all-files
```

pre-commit installs the pinned YAPF, clang-format, Ruff, and repository
checks. YAPF reads `.style.yapf`; clang-format reads `.clang-format`; Ruff
reads `pyproject.toml`. The automated pull-request checks use these same
tools and report any formatting changes needed.

## API and CLI documentation

Public command documentation lives on the Python function that implements the
operation. The equivalent `GData` spelling is a class-body alias to that same
function, so editor hover help, `help(pg.interpolate)`,
`help(data.interpolate)`, and `pgkyl interpolate --help` cannot maintain
separate descriptions.
The installed distribution includes a `py.typed` marker so language servers
consume these inline signatures and aliases from a virtual environment too.

Command docstrings use `Args:` entries in Google style. Every CLI-visible
parameter needs one entry; command compilation rejects missing, duplicate, or
unknown parameter documentation. `tests/test_documentation.py` additionally
checks the public Python surface, static fluent aliases, source/runtime
docstring identity, and deterministic CLI lowering. Run it directly with:

```bash
pytest tests/test_documentation.py
```

## Release packages

Build a wheel (an installable package) and test it in a clean environment:

```bash
python -m build
scripts/smoke_wheel.sh dist/*.whl
```

The wheel workflow builds portable Linux x86_64 and macOS Intel/Apple Silicon
wheels for the supported CPython versions. Each wheel runs native tests outside
the source tree with both the minimum supported and current NumPy. Linux wheels
are repaired with auditwheel; macOS wheels use delocate.

Run the workflow manually to review its artifacts. Publishing a GitHub release
also builds an sdist and publishes the validated distributions through the
`pypi` environment. Configure a PyPI trusted publisher for this repository,
`.github/workflows/wheels.yml`, and environment `pypi` before releasing.
See [PyPI's trusted publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

For a local portable Linux wheel build with Docker available:

```bash
python -m pip install cibuildwheel
python -m cibuildwheel --platform linux
```

A clean source build obtains the current Gkeyll `main`; an existing checkout is
reused. `pgkyl --version` records the producer revision and whether it had local
changes. Validate release artifacts from a fresh checkout so local producer
edits cannot enter a release accidentally.
