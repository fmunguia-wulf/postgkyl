"""Shared pytest configuration for the postgkyl test suite.

Session fixture
---------------
``generated_test_data`` runs once per pytest session and writes synthetic
.gkyl files to ``tests/test_data/generated/`` (gitignored — every test that
reads from that directory depends on this fixture via autouse). Without it,
a clean checkout (e.g. CI) has no fixtures to read; only a machine where
someone has run ``python tests/generate_test_data.py`` (or a prior pytest
session) before would happen to have them already on disk.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from generate_test_data import generate_all

GEN_DIR = Path(__file__).parent / "test_data" / "generated"


@pytest.fixture(scope="session", autouse=True)
def generated_test_data():
  """Write synthetic .gkyl test files before any test runs."""
  generate_all(GEN_DIR)
  return GEN_DIR
# end
