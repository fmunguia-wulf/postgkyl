"""Composed diagnostics & workflows (L4) — built on the script API.

An *app* is a higher-level program that loads (often many) files, computes, and
produces a finished diagnostic (typically a figure). Apps are assembled from the
L0-L3 layers (``tools`` / ``data`` / ``ops`` / the fluent API) and never import
``commands``; the CLI commands are thin shells that drive them.

These modules are currently driven primarily through the CLI (each exposes a
Typer command function). Extracting a fully ``ctx``-free, script-callable
compute/plot function from each is the remaining decoupling step — see
``REFACTOR.md``.
"""

from postgkyl.apps.gk_energy_balance import gk_energy_balance
from postgkyl.apps.gk_particle_balance import gk_particle_balance
from postgkyl.apps.gk_nodes import gk_nodes
from postgkyl.apps.trajectory import trajectory

__all__ = [
    "gk_energy_balance",
    "gk_particle_balance",
    "gk_nodes",
    "trajectory",
]
