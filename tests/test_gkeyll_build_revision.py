"""Exercise source updates against a local Git remote without compiling."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).parents[1]


def _git(directory, *args):
  return subprocess.check_output(
      ["git", "-C", str(directory), *args], text=True).strip()


@pytest.fixture
def checkout(tmp_path):
  remote = tmp_path / "remote"
  remote.mkdir()
  _git(remote, "init", "-b", "main")
  _git(remote, "config", "user.name", "Build test")
  _git(remote, "config", "user.email", "build@example.invalid")
  configure = remote / "configure"
  configure.write_text(
      "#!/bin/sh\nmkdir -p build/core\ntouch build/core/libg0core.so\n")
  configure.chmod(0o755)
  _git(remote, "add", "configure")
  _git(remote, "commit", "-m", "Initial source")
  workspace = tmp_path / "workspace"
  scripts = workspace / "scripts"
  scripts.mkdir(parents=True)
  source = (ROOT / "scripts/build_gkeyll.sh").read_text()
  (scripts / "build_gkeyll.sh").write_text(
      source.replace("https://github.com/ammarhakim/gkeyll.git",
                     remote.as_uri()))
  shutil.copyfile(ROOT / "scripts/gkeyll-branch", scripts / "gkeyll-branch")
  (scripts / "build_gpython.sh").write_text("#!/bin/sh\nexit 0\n")
  binary_dir = tmp_path / "bin"
  binary_dir.mkdir()
  make = binary_dir / "make"
  make.write_text("#!/bin/sh\nexit 0\n")
  make.chmod(0o755)
  env = dict(os.environ, PATH=str(binary_dir) + os.pathsep + os.environ["PATH"])
  # A stale environment override must never restore commit pinning.
  env["GKEYLL_REVISION"] = _git(remote, "rev-parse", "HEAD")
  return workspace, remote, env


def _build(checkout):
  workspace, _, env = checkout
  return subprocess.run(["sh", str(workspace / "scripts/build_gkeyll.sh")],
                        cwd=workspace,
                        env=env,
                        text=True,
                        capture_output=True,
                        timeout=20)


@pytest.mark.parametrize("existing_branch", [None, "old-feature"])
def test_build_follows_main_as_remote_advances(checkout, existing_branch):
  workspace, remote, _ = checkout
  if existing_branch is not None:
    _git(remote, "branch", existing_branch)
    _git(workspace, "clone", "--depth", "1", "--branch", existing_branch,
         remote.as_uri(), "gkeyll")
  first = _build(checkout)
  assert first.returncode == 0, first.stderr
  producer = workspace / "gkeyll"
  initial = _git(producer, "rev-parse", "HEAD")
  _git(remote, "commit", "--allow-empty", "-m", "New upstream change")
  latest = _git(remote, "rev-parse", "HEAD")
  assert latest != initial
  second = _build(checkout)
  assert second.returncode == 0, second.stderr
  assert _git(producer, "rev-parse", "HEAD") == latest
  assert _git(producer, "symbolic-ref", "--short", "HEAD") == "main"
  assert _git(producer, "rev-parse", "--abbrev-ref",
              "@{upstream}") == "origin/main"


@pytest.mark.parametrize("local_change", ["dirty", "commit"])
def test_build_preserves_and_refuses_local_changes(checkout, local_change):
  workspace, _, _ = checkout
  first = _build(checkout)
  assert first.returncode == 0, first.stderr
  producer = workspace / "gkeyll"
  configure = producer / "configure"
  changed = configure.read_text() + "# local change\n"
  configure.write_text(changed)
  if local_change == "commit":
    _git(producer, "add", "configure")
    _git(producer, "-c", "user.name=Build test", "-c",
         "user.email=build@example.invalid", "commit", "-m", "Local work")
  before = _git(producer, "rev-parse", "HEAD")
  result = _build(checkout)
  assert result.returncode != 0
  expected = "tracked modifications" if local_change == "dirty" else "local commits"
  assert expected in result.stderr
  assert configure.read_text() == changed
  assert _git(producer, "rev-parse", "HEAD") == before
