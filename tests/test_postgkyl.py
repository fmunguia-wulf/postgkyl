"""Smoke tests + architecture contract for the postgkyl library.

Run:  PYTHONPATH=src pytest tests/test_postgkyl.py -v
"""

import ast
import collections
import os
import sys

import numpy as np
import pytest

# Make src/ importable without an install.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
  sys.path.insert(0, SRC)

import matplotlib
matplotlib.use("Agg")

import postgkyl as pg  # noqa: E402

DATA = os.path.join(ROOT, "tests", "test_data")
F1 = os.path.join(DATA, "rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl")
F2D = os.path.join(DATA, "generated", "2d_ms_p1.gkyl")


def test_load_metadata():
  d = pg.load(F1)
  assert d.num_dims == 1
  assert d.ctx["basis_type"] == "serendipity"
  assert d.ctx["poly_order"] == 1
  assert not d.is_interpolated          # raw modal data


def test_golden_script_1d():
  g = pg.load(F1).interp().sel(comp=0)
  assert g.is_interpolated
  assert g.num_comps == 1
  assert g.num_dims == 1
  assert g.values.shape[0] == 48         # 24 cells * (p+1=2) interp points
  assert type(g).__name__ == "GData"    # subclass propagated through verbs
  fig = g.plot(show=False)
  assert fig is not None


def test_golden_script_2d():
  g = pg.load(F2D).interp().sel(comp=0)
  assert g.num_dims == 2
  assert g.values.shape == (16, 16, 1)
  assert g.plot(show=False) is not None


def test_arithmetic_and_ufunc():
  a = pg.load(F1).interp().sel(comp=0)
  b = pg.load(F1).interp().sel(comp=0)
  assert isinstance(a + b, pg.GData)
  assert isinstance(a * 2.0, pg.GData)
  assert isinstance(2.0 * a, pg.GData)          # reflected
  mag = np.sqrt(a ** 2 + b ** 2)                # ufunc keeps it a GData
  assert isinstance(mag, pg.GData)
  assert np.allclose(mag.values, np.sqrt(a.values ** 2 + b.values ** 2))
  assert np.asarray(a).shape == a.values.shape  # __array__


def test_capability_guardrails_on_modal_data():
  """Modal data supports the Gkeyll verbs; everything NumPy-shaped refuses."""
  a = pg.load(F1)
  with pytest.raises(ValueError):
    np.sqrt(a)                                   # general ufunc: no modal meaning
  with pytest.raises(ValueError):
    np.asarray(a)                                # coefficients are not point values
  with pytest.raises(ValueError):
    a.sel(comp=0)                                # slicing would mix basis functions
  with pytest.raises(ValueError):
    _ = a + a.interp()                           # mixed modal + field domains


# --------------------------------------------------------------------------
# The modal domain: DG operations running inside Gkeyll (REFACTOR_GKEYLL_FFI.md)
# --------------------------------------------------------------------------
from postgkyl import ffi  # noqa: E402

needs_gkeyll = pytest.mark.skipif(not ffi.available(),
    reason="no compiled Gkeyll (libg0core.so) found")


@needs_gkeyll
def test_load_lands_in_the_modal_domain():
  d = pg.load(F1)
  assert d.backend == "gkyl"                     # native gkyl_array storage
  assert d.native is not None
  assert d.values.shape == (24, 6)                # read-only view for inspection
  assert not d.values.flags.writeable
  g = d.interp()                                 # the one-way bridge
  assert g.backend == "numpy"                    # ...to a by-value NumPy array
  assert g.values.flags.writeable


@needs_gkeyll
def test_ffi_abi_guard():
  """Layout-exact struct mirrors: C writes where Python reads."""
  import ctypes
  b = ffi.basis.get_basis("serendipity", 2, 1)
  assert (b.ndim, b.poly_order, b.num_basis) == (2, 1, 4)
  assert b.id == b"serendipity"
  lib = ffi.require()
  rng = ffi.structs.GkylRange()
  lo, up = (ctypes.c_int * 2)(1, 1), (ctypes.c_int * 2)(8, 50)
  lib.gkyl_range_init(ctypes.byref(rng), 2, lo, up)
  assert rng.volume == 400 and rng.ndim == 2


@needs_gkeyll
def test_interp_matrix_matches_analytic_basis():
  """Matrices built from Gkeyll's eval() match the normalized Legendre basis."""
  m = ffi.basis.interp_matrix("serendipity", 1, 1, 2)   # points z = -+1/2
  expect = np.array([[1 / np.sqrt(2), -np.sqrt(3.0 / 2.0) / 2],
                     [1 / np.sqrt(2), +np.sqrt(3.0 / 2.0) / 2]])
  assert np.allclose(m, expect)
  m2 = ffi.basis.interp_matrix("serendipity", 1, 2, 3)  # p2, points -+2/3, 0
  z = np.array([-2.0 / 3.0, 0.0, 2.0 / 3.0])
  assert np.allclose(m2[:, 2], 2.371708245126285 * z ** 2 - 0.7905694150420951)


@needs_gkeyll
def test_weak_algebra_identities():
  """div(mul(a, b), b) == a — Gkeyll's weak kernels are exact inverses."""
  a, b = pg.load(F1), pg.load(F1)
  back = (a * b / b).interp().values
  ref = a.interp().values
  for f in (0, 2):  # density and T; field 1 (u_par) is identically ~0 -> 0/0
    scale = np.abs(ref[..., f]).max()
    assert np.abs(back[..., f] - ref[..., f]).max() / scale < 1e-12


@needs_gkeyll
def test_modal_linear_ops_commute_with_interp():
  """interp is linear: modal +,-,scalar* agree with their NumPy counterparts."""
  a, b = pg.load(F1), pg.load(F1)
  assert np.allclose((a + b).interp().values, a.interp().values + b.interp().values)
  assert np.allclose((a - b).interp().values, 0.0)
  assert np.allclose((2.5 * a).interp().values, 2.5 * a.interp().values)
  assert np.allclose((-a).interp().values, -(a.interp().values))
  assert np.allclose((a ** 2).interp().values, (a * a).interp().values)
  shifted = (a + 1.0e18).interp().values - a.interp().values
  assert np.allclose(shifted, 1.0e18, rtol=1e-6)


@needs_gkeyll
def test_integrate_via_gkeyll():
  """pg-level integrate == the coefficient-space formula (exact for DG)."""
  a = pg.load(F1)
  result = a.integrate()
  v = a.values                                   # (cells, nfields*num_basis) view
  dx = float((a.bounds[1][0] - a.bounds[0][0]) / a.num_cells[0])
  nb = 2                                         # serendipity 1D p1
  manual = np.array([v[:, f * nb].sum() * dx / np.sqrt(2.0)
                     for f in range(v.shape[-1] // nb)])
  assert np.allclose(result, manual)
  assert np.all(a.integrate(op="abs") >= np.abs(result) * (1 - 1e-12))
  with pytest.raises(ValueError):
    a.interp().integrate()                       # field domain: not a modal verb


def test_write_roundtrip(tmp_path):
  a = pg.load(F1).interp().sel(comp=0)
  out = a.write(str(tmp_path / "rt.gkyl"))
  back = pg.load(out)
  assert np.allclose(back.values, a.values)


def test_info_returns_string(capsys):
  s = pg.load(F1).info()
  assert "Number of components" in s


def test_cli_chained(tmp_path):
  """The chained CLI: bare filename -> load, interp, sel, plot --save."""
  from click.testing import CliRunner
  from postgkyl.cli.app import cli

  out = tmp_path / "cli.png"
  result = CliRunner().invoke(cli, [
      "--batch-mode", F1, "interp", "sel", "--comp", "0", "plot", "--save", str(out)])
  assert result.exit_code == 0, result.output
  assert out.exists()


def test_cli_abbreviation_and_info():
  """`interp`/`sel` resolve by unique-prefix abbreviation."""
  from click.testing import CliRunner
  from postgkyl.cli.app import cli

  result = CliRunner().invoke(cli, [F1, "interp", "sel", "--comp", "0", "info"])
  assert result.exit_code == 0, result.output
  assert "interpolated" in result.output


# --------------------------------------------------------------------------
# Architecture contract: the layering is a strict, cycle-free DAG.
# --------------------------------------------------------------------------
_ALLOWED = {
    "ffi":    set(),                                # the foreign floor (only ctypes owner)
    "numerics": set(),
    "dg":     {"ffi"},                              # interp bridge + modal ops -> kernels
    "io":     {"ffi"},                              # C-native reader -> gkyl_array_rio
    "core":   {"io", "ffi"},                        # container holds a GkylArray backend
    "render": {"core", "numerics"},
    "ops":    {"core", "dg", "numerics", "render"},
    "api":    {"core", "ops", "io"},
    "":       {"api", "ops", "render", "io"},       # facade: pure re-export of public names
    "cli":    {""},                                   # top surface: pure consumer of the facade
}
_LAYERS = set(_ALLOWED)


def _layer(path, pkg_root):
  parts = os.path.relpath(path, pkg_root).split(os.sep)
  return parts[0] if len(parts) > 1 else ""


def _import_targets(node):
  if isinstance(node, ast.Import):
    for n in node.names:
      if n.name == "postgkyl" or n.name.startswith("postgkyl."):
        t = n.name.split(".")
        yield t[1] if len(t) > 1 else ""
  elif isinstance(node, ast.ImportFrom):
    if node.level:
      return
    mod = node.module or ""
    if mod == "postgkyl":
      for n in node.names:
        yield n.name if n.name in _LAYERS else ""
    elif mod.startswith("postgkyl."):
      yield mod.split(".")[1]


def _build_edges():
  pkg_root = os.path.join(SRC, "postgkyl")
  edges = collections.defaultdict(set)
  violations = []
  for dp, _, files in os.walk(pkg_root):
    for f in files:
      if not f.endswith(".py"):
        continue
      p = os.path.join(dp, f)
      src = _layer(p, pkg_root)
      for node in ast.walk(ast.parse(open(p).read(), p)):
        for tgt in _import_targets(node):
          if tgt == src:
            continue
          edges[src].add(tgt)
          if tgt not in _ALLOWED.get(src, set()):
            violations.append(f"{os.path.relpath(p, pkg_root)} [{src or 'facade'}] -> [{tgt or 'facade'}]")
  return edges, violations


def test_facade_is_pure_reexport():
  """__init__.py must define no functions/classes — only re-export names."""
  facade = os.path.join(SRC, "postgkyl", "__init__.py")
  tree = ast.parse(open(facade).read(), facade)
  defs = [n.name for n in tree.body
          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
  assert not defs, f"facade should be pure re-export, but defines: {defs}"


def test_import_contract_no_violations():
  _, violations = _build_edges()
  assert not violations, "layer contract violations:\n" + "\n".join(violations)


def test_ctypes_confined_to_ffi():
  """ffi/ is the only package that may touch ctypes (or native memory)."""
  pkg_root = os.path.join(SRC, "postgkyl")
  offenders = []
  for dp, _, files in os.walk(pkg_root):
    for f in files:
      if not f.endswith(".py"):
        continue
      p = os.path.join(dp, f)
      if _layer(p, pkg_root) == "ffi":
        continue
      for node in ast.walk(ast.parse(open(p).read(), p)):
        if isinstance(node, ast.Import) and any(
            n.name.split(".")[0] == "ctypes" for n in node.names):
          offenders.append(os.path.relpath(p, pkg_root))
        elif isinstance(node, ast.ImportFrom) and (
            (node.module or "").split(".")[0] == "ctypes"):
          offenders.append(os.path.relpath(p, pkg_root))
  assert not offenders, f"ctypes leaked above the ffi floor: {offenders}"


def test_import_graph_is_acyclic():
  edges, _ = _build_edges()
  color = collections.defaultdict(int)
  cycles = []

  def dfs(u, stack):
    color[u] = 1
    for w in edges.get(u, ()):
      if color[w] == 1:
        cycles.append(stack + [w])
      elif color[w] == 0:
        dfs(w, stack + [w])
    color[u] = 2

  for n in list(edges):
    if color[n] == 0:
      dfs(n, [n])
  assert not cycles, f"import cycle(s): {cycles}"
