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

F1 = os.path.join(ROOT, "gk_lorentzian_mirror-elc_MaxwellianMoments_65.gkyl")
F2 = os.path.join(ROOT, "gk_lorentzian_mirror-ion_BiMaxwellianMoments_65.gkyl")
F2D = os.path.join(ROOT, "gk_lorentzian_mirror_2x-ion_BiMaxwellianMoments_65.gkyl")


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
  assert g.values.shape[0] == 800       # 400 cells * (p+1=2) interp points
  assert type(g).__name__ == "GData"    # subclass propagated through verbs
  fig = g.plot(show=False)
  assert fig is not None


def test_golden_script_2d():
  g = pg.load(F2D).interp().sel(comp=0)
  assert g.num_dims == 2
  assert g.values.shape == (8, 800, 1)
  assert g.plot(show=False) is not None


def test_arithmetic_and_ufunc():
  a = pg.load(F1).interp().sel(comp=0)
  b = pg.load(F2).interp().sel(comp=0)
  assert isinstance(a + b, pg.GData)
  assert isinstance(a * 2.0, pg.GData)
  assert isinstance(2.0 * a, pg.GData)          # reflected
  mag = np.sqrt(a ** 2 + b ** 2)                # ufunc keeps it a GData
  assert isinstance(mag, pg.GData)
  assert np.allclose(mag.values, np.sqrt(a.values ** 2 + b.values ** 2))
  assert np.asarray(a).shape == a.values.shape  # __array__


def test_arithmetic_guardrail_on_raw_modal():
  with pytest.raises(ValueError):
    _ = pg.load(F1) + pg.load(F2)                # raw modal -> refused


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
    "numerics": set(), "dg": set(), "io": set(),
    "core":   {"io"},
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
      if not f.endswith(".py") or f == "matrices.py":  # vendored sympy file
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
