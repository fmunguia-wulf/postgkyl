# Postgkyl

![pytest](https://github.com/ammarhakim/postgkyl/actions/workflows/test.yml/badge.svg)

Postgkyl reads, analyzes, and visualizes Gkeyll simulation data through a
Python library and the composable `pgkyl` command-line tool.

## Installation

Use Python 3.10 or newer on Linux or macOS. On Windows, use
[Ubuntu in WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Source builds need Git, Make, and a C compiler: install `git build-essential
python3-venv python3-dev` on Ubuntu/Debian, or the Xcode command-line tools
(`xcode-select --install`) on macOS.

```bash
git clone https://github.com/ammarhakim/postgkyl.git
cd postgkyl
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
pgkyl --version
```

pip installs the dependencies and builds the Gkeyll bridge automatically.
The first build downloads Gkeyll and may take several minutes. Reactivate the
environment with `source .venv/bin/activate` in each new terminal.

For development, replace the install command above with:

```bash
python -m pip install -e '.[test]'
```

To install a published release in an active environment, use
`python -m pip install postgkyl`. Compatible wheels include the native bridge.
See the [installation guide](docs/source/installation.md) for alternative
environments, native rebuilds, and troubleshooting.

## Updating

With the environment active, run:

```bash
bash scripts/update_pgkyl.sh
```

This explicitly updates both Postgkyl and Gkeyll, rebuilds, and reinstalls.
Use `--editable` for a developer installation. Ordinary installs and rebuilds
reuse the existing Gkeyll checkout, including local edits, without fetching
upstream or switching branches.

## Documentation

Read the [documentation](https://gkeyll.readthedocs.io/en/latest/postgkyl/index.html),
[examples](examples/README.md), or [notebooks](notebooks/README.md).
For command help, run `pgkyl --help` or, for example, `pgkyl interpolate --help`.

The [development guide](docs/source/development.md) covers tests, formatting,
native development, and release packages. The
[documentation guide](docs/source/contributing.rst) describes local website
builds; [integration notes](docs/integration-plan.md) cover the host website.

## Contributors

See the [contributors on GitHub](https://github.com/ammarhakim/postgkyl/graphs/contributors).

## License

Postgkyl is distributed under the MIT License.
