"""Shared pytest configuration and helper utilities for the postgkyl test suite.

Session fixture
---------------
``generated_test_data`` runs once per pytest session and writes synthetic
.gkyl files to ``tests/test_data/generated/``.  All tests that reference
those files depend on this fixture automatically (autouse=True).

Shared helpers
--------------
``make_gdata``, ``ctx_with_datasets``, and ``GRID1D`` are plain functions /
constants; import them directly in test modules::

    from conftest import make_gdata, ctx_with_datasets, GRID1D
"""
from __future__ import annotations

from pathlib import Path

import click
import numpy as np
import pytest

import postgkyl.commands as cmd
from postgkyl.commands.state import AppState
from postgkyl.data.gdata import GData
from postgkyl.pgkyl import cli

from generate_test_data import generate_all

# Directory where generated files are written (gitignored)
GEN_DIR = Path(__file__).parent / "test_data" / "generated"


# ---------------------------------------------------------------------------
# Session fixture: generate synthetic test files once per run
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def generated_test_data():
    """Write synthetic .gkyl test files before any test runs."""
    generate_all(GEN_DIR)
    return GEN_DIR


# ---------------------------------------------------------------------------
# Shared in-memory GData factory
# ---------------------------------------------------------------------------

GRID1D: list[np.ndarray] = [np.array([0.0, 1.0])]


def make_gdata(grid, values, tag: str = "default", ctx_extra: dict | None = None) -> GData:
    """Return a GData loaded from numpy arrays."""
    d = GData(tag=tag)
    d.push(grid, values)
    if ctx_extra:
        d.ctx.update(ctx_extra)
    return d


# ---------------------------------------------------------------------------
# Shared Click context factory (used by CLI command tests)
# ---------------------------------------------------------------------------

def ctx_with_datasets(*datasets: GData) -> click.core.Context:
    """Return a minimal Click context with *datasets* pre-loaded."""
    ctx = click.core.Context(cli)
    data = cmd.DataSpace()
    for dat in datasets:
        data.add(dat)
    ctx.obj = AppState(data=data, compgrid=None)
    return ctx
