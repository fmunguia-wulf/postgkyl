# Postgkyl

![pytest](https://github.com/ammarhakim/postgkyl/actions/workflows/test.yml/badge.svg)

This is the Postgkyl project. It is both Python library and command-line tool
designed to provide unified access to Gkeyll data together with a broad variety
of analytical and visualization tools.

## Documentation

Full documentation of the Gkeyll project is available at
[ReadTheDocs](http://gkeyll.rtfd.io).

## Quick Start

Postgkyl has two usage modes: a **low-level data API** for direct file access, and a
**high-level simulation API** (``postgkyl.Simulation``) for physics-aware workflows.

### Low-level API

```python
import postgkyl as pg

# Load a Gkeyll output file
data = pg.GData("run-elc_10.gkyl")

# DG interpolation from basis coefficients to nodal values
dg = pg.GInterpModal(data, poly_order=1, basis_type="ms")
dg.interpolate(overwrite=True)

# Access the result
grid = data.get_grid()    # list of 1-D arrays, one per dimension
vals = data.get_values()  # N-D numpy array
```

### Command-line interface

```bash
# Load, interpolate, and plot in one pipeline
pgkyl run-elc_10.gkyl interpolate plot

# Select a component and slice before plotting
pgkyl run-field_5.gkyl select --comp 0 plot --xlabel 'x (m)'
```

### High-level simulation API

```python
import postgkyl as pg

# 1. Describe the simulation geometry and species
sim = pg.Simulation(dimensionality='3x2v')
sim.set_phys_param()
sim.set_geom_param(R_axis=0.9, B_axis=1.4, x_LCFS=0.05, a_shift=0.0,
                   kappa=1.4, delta=0.4)

elc = pg.Species('elc', m=9.109e-31, q=-1.602e-19,
                 T0=500*1.602e-19, n0=3e19, Bref=1.4)
ion = pg.Species('ion', m=2*1.673e-27, q=1.602e-19,
                 T0=500*1.602e-19, n0=3e19, Bref=1.4)
sim.add_species(elc)
sim.add_species(ion)

# 2. Point to the data directory
sim.set_data_param(simdir='/path/to/run/', fileprefix='run')

# 3. Load a field at a specific time frame
frame = pg.Frame(sim, 'ni', tf=10, load=True)
print(frame.values.shape)  # (Nx, Ny, Nz)

# 4. Slice to 2D and inspect
frame.slice('z', 0.0)          # cut at z = 0
print(frame.new_grids[0])      # radial grid after normalization
```

### Optional extras

Install optional dependency groups to unlock additional features:

```bash
pip install postgkyl[sim]        # h5py, imageio, freeqdsk
pip install postgkyl[interfaces] # h5py, netCDF4 (FLAN reader)
pip install postgkyl[adios]      # ADIOS2 (bp file reader)
pip install postgkyl[all]        # everything above
```

## Dependencies and Installation

Postgkyl requires the following packages:

* [click](https://pypi.org/project/click/)
* [matplotlib](https://pypi.org/project/matplotlib/)
* [msgpack](https://pypi.org/project/msgpack/)
* [numpy](https://pypi.org/project/numpy/)
* [scipy](https://pypi.org/project/scipy/)
* [sympy](https://pypi.org/project/sympy/)
* [tables](https://pypi.org/project/tables/)

Note that Posgkyl currently does not work with NumPy >= 2.0; the update is in
the works. In addition, there are two optional dependencies:

* [adios2](https://pypi.org/project/adios2/)
* [pytest](https://pypi.org/project/pytest/)

ADIOS 2 is required for reading Gkeyll 2 `bp` output files and it is not needed
when working only with `gkylzero`. [pytest](https://docs.pytest.org/en/stable/)
is required only for developers.

### Setting up virtual environment (recommended)

We strongly recommend creating a virtual Python environment for everybody
working with more than one Python project (this includes even using both
Postgkyl and Sphinx). The two recommended options are
[venv](https://docs.python.org/3/library/venv.html) and
[mamba](https://mamba.readthedocs.io/en/latest/).

With `venv`, one can create the virtual environment with:

```bash
python -m venv /path/to/new/virtual/environments/pgkyl
```

then activate it with:

| bash/zsh | `source <venv>/bin/activate`      |
| fish     | `source <venv>/bin/activate.fish` |
| csh/tcsh | `source <venv>/bin/activate.csh`  |

and deactivate with:

```bash
deactivate
```

With `mamba`, one can create the virtual environment with:

```bash
mamba create -n pgkyl
```

then activate with:

```bash
mamba activate pgkyl
```

and deactivate with:

```bash
mamba deactivate
```

Note that with `mamba`, one can also use the provided `environment.yml` file,
which also includes dependency specifications:

```bash
mamba env create -f environment.yml
```

### Installing Postgkyl

The Postgkyl itself is installed with `pip`.[^1] Developers and uses who want to
have the most up-to-date version should install Postgkyl from the source code:

```bash
git clone https://github.com/ammarhakim/postgkyl.git
cd postgkyl
pip install -e .[adios,test]
```

Alternatively, Postgkyl can be installed directly from [PyPI](https://pypi.org/project/postgkyl/):

```bash
pip install -e postgkyl[adios,test]
```

Note that ADIOS2 is not available on PyPI for Mac OSX; therefore, Mac users who
want to use it need to install the dependency from elsewhere, for example, using
the above-mentioned `mamba` and then do *not* use the `adios` tag with `pip`.

## Testing

Postgkyl utilizes [pytest](https://docs.pytest.org/) for testing. The tests can
be called manually from the root Postgkyl directory simply by using:

```bash
pytest [-v]
```

## Authors

The full list of authors can be found [here](AUTHORS.md).

## License

Postgkyl is distributed under the MIT License.

[^1]: This does *not* require any additional modifications of `PYTHONPATH`. If
    Postgkyl was used previously through `PYTHONPATH`, we strongly recommend
    removing the path to the Postgkyl repository from the variable.
