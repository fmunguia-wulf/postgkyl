"""Gyrokinetic diagnostics: named quantities and distribution functions.

``postgkyl.diagnostics.gyrokinetics`` is another equation-specific module in
the diagnostics layer (like ``five_moment`` in
``examples/scripts/03_diagnostics_five_moment.py``), but for gyrokinetic
simulations it owns its own *loading* too -- a simulation's files follow a
naming convention (``<name>-<species>_<quantity>_<frame>.gkyl``), so instead
of calling ``pg.load`` on individual filenames, you ask for a quantity by
name and the loader resolves which files it needs:

* ``pg.available_gk_quantities()`` lists the registered quantity names.
* ``pg.load_gk_quantity(quantity, species, name, frame, path=...)`` resolves
  the source file(s) for that quantity, computes it, and returns one
  ``GData`` per requested species -- already interpolated, ready to
  ``.select()``/``.plot()`` like anything else.
* ``pg.load_gk_distf(name=..., species=..., frame=..., ...)`` reconstructs a
  full distribution function from the saved ``Jf``-times-Jacobian(s) files
  (what the CLI's ``gk_distf`` command wraps).

This uses the ``rt_gk_tcv_iwl*`` fixtures staged in ``tests/test_data`` --
two related simulations: ``rt_gk_tcv_iwl_adapt_source_1x2v_p1`` wrote ion
Hamiltonian moments (``M0``/``M1`` are derivable from those), and
``rt_gk_tcv_iwl_1x2v_p1`` wrote the electron distribution function plus its
geometry (``geo_int_jacobtot_inv``).

Run directly:
    MPLBACKEND=Agg PYTHONPATH=src python examples/scripts/04_gyrokinetics.py
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")

import numpy as np

import postgkyl as pg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "tests", "test_data")
OUTPUT_DIR = os.environ.get("PGKYL_EXAMPLE_OUTPUT", os.path.join(HERE, "output"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

HMOM_NAME = "rt_gk_tcv_iwl_adapt_source_1x2v_p1"  # wrote ion Hamiltonian moments
GK_NAME = "rt_gk_tcv_iwl_1x2v_p1"                 # wrote elc distf + geometry

print("registered quantities:", pg.available_gk_quantities())

# 1. A moment quantity ("M0", the density) resolved straight from the
#    HamiltonianMoments file the registry knows how to read; already
#    interpolated, so it's a regular one-component field.
m0, = pg.load_gk_quantity("M0", "ion", HMOM_NAME, "250", path=DATA)
print("M0:", repr(m0), " label:", m0.get_label())
assert m0.num_comps == 1
assert np.all(np.isfinite(np.asarray(m0)))

fig = m0.plot(title=m0.get_label(), show=False)
fig.savefig(os.path.join(OUTPUT_DIR, "04_gyrokinetics_M0.png"))

# 2. "M1" needs the species mass to convert a momentum-like moment into a
#    velocity -- extra per-quantity parameters go through **extra.
m1, = pg.load_gk_quantity("M1", "ion", HMOM_NAME, "250", path=DATA, mass=2.0)
print("M1:", repr(m1), " label:", m1.get_label())
assert np.all(np.isfinite(np.asarray(m1)))

# 3. A species-independent geometric factor, from the other simulation --
#    ``species=None`` since geometry isn't per-species.
jacobtot_inv, = pg.load_gk_quantity("geo_int_jacobtot_inv", None, GK_NAME, path=DATA)
print("(J B)^-1:", repr(jacobtot_inv), " label:", jacobtot_inv.get_label())

fig = jacobtot_inv.plot(title=jacobtot_inv.get_label(), show=False)
fig.savefig(os.path.join(OUTPUT_DIR, "04_gyrokinetics_jacobtot_inv.png"))

# 4. The full electron distribution function: 3D (x, vpar, mu), built from
#    the saved Jf-times-Jacobian(s) file plus the geometry factor above.
distf = pg.load_gk_distf(name=os.path.join(DATA, GK_NAME), species="elc",
    frame=250, jacobtot_inv_file=os.path.join(DATA, f"{GK_NAME}-geo_int_jacobtot_inv.gkyl"))
print("distf:", repr(distf))
assert distf.num_dims == 3
assert distf.num_comps == 1
assert np.all(np.isfinite(np.asarray(distf)))

# It's a regular GData from here on -- e.g. select a fixed-mu slice down to
# the (x, vpar) plane and plot it, same as any other 2D field.
slice_2d = distf.select(z2=0.0)
fig = slice_2d.plot(title="elc distf, mu=0 slice", show=False)
fig.savefig(os.path.join(OUTPUT_DIR, "04_gyrokinetics_distf_slice.png"))

print("04_gyrokinetics: OK")
