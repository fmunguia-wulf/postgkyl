"""Contracts of the native setuptools command, independent of compilation."""

import runpy
from pathlib import Path

import pytest
import setuptools
from setuptools.dist import Distribution

ROOT = Path(__file__).parents[1]


@pytest.fixture
def setup_config(monkeypatch):
  config = {}
  monkeypatch.setattr(setuptools, "setup",
                      lambda **kwargs: config.update(kwargs))
  monkeypatch.setenv("POSTGKYL_SKIP_GKEYLL_BUILD", "0")
  namespace = runpy.run_path(ROOT / "setup.py")
  return config, namespace


# Setuptools asks install_lib for output metadata even for PEP 660 builds.
@pytest.mark.filterwarnings(
    "ignore:setup.py install is deprecated:setuptools.warnings.SetuptoolsDeprecationWarning"
)
@pytest.mark.parametrize("editable", [False, True])
def test_native_outputs_include_library_and_provenance(setup_config, tmp_path,
                                                       editable):
  config, _ = setup_config
  distribution = Distribution({
      **config, "packages": ["postgkyl.gpython"],
      "package_dir": {
          "": "src"
      }
  })
  command = distribution.get_command_obj("build_ext")
  command.build_lib = str(tmp_path / "lib")
  command.editable_mode = editable
  command.ensure_finalized()
  outputs = command.get_outputs()
  for name in ("libg0core.so", "_build_info.json"):
    built = str(tmp_path / "lib/postgkyl/gpython" / name)
    assert built in outputs
    assert command.get_output_mapping()[built] == str(
        Path("src/postgkyl/gpython") / name)
  assert any(Path(path).name.startswith("_gpython.") for path in outputs)
  assert distribution.has_ext_modules()


def test_skip_build_produces_pure_python_distribution(monkeypatch):
  config = {}
  monkeypatch.setattr(setuptools, "setup",
                      lambda **kwargs: config.update(kwargs))
  monkeypatch.setenv("POSTGKYL_SKIP_GKEYLL_BUILD", "1")
  runpy.run_path(ROOT / "setup.py")
  assert not Distribution(config).has_ext_modules()


def test_skip_build_rejects_misspelled_value(monkeypatch):
  monkeypatch.setenv("POSTGKYL_SKIP_GKEYLL_BUILD", "true")
  with pytest.raises(ValueError, match="must be 0 or 1"):
    runpy.run_path(ROOT / "setup.py")
