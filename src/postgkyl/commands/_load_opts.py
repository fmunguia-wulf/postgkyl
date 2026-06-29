"""Resolve the CLI ``load`` command's options against the global pre-options.

``pgkyl`` accepts cuts (``--z0``..``--z5``/``-c``), variable names, and c2p
mapping files both as *global* pre-options on the root group and as *local*
options on the ``load`` command. The precedence rule is the same for every one
of them: a local value wins, but warns when it shadows a global value;
otherwise the global value (or a default) is used.

This module collects that single rule into one helper so the ``load`` command
is a thin shell instead of a dozen copy-pasted ``if/elif/elif`` blocks.
"""

from __future__ import annotations

from dataclasses import dataclass

import typer


@dataclass
class LoadOptions:
  """Resolved per-file load settings (after applying global/local precedence)."""

  cuts: tuple          # (z0, z1, z2, z3, z4, z5)
  comp: str | None     # component cut
  var_names: list      # ADIOS variable names to load
  mapc2p_name: str | None
  mapc2p_vel_name: str | None


def _pick(local, global_, name: str):
  """Return the local value if set (warning when it shadows a global), else the global."""
  if local and global_:
    typer.echo(typer.style(
        f"WARNING: The local '{name:s}' is overwriting the global '{name:s}'",
        fg="yellow"))
    return local
  # end
  return local if local else (global_ if global_ else None)


def resolve_load_options(ctx: typer.Context, *, z0=None, z1=None, z2=None,
    z3=None, z4=None, z5=None, component=None, varname=None,
    c2p=None, c2p_vel=None) -> LoadOptions:
  """Apply global/local precedence to the load options and package the result."""
  local_cuts = (z0, z1, z2, z3, z4, z5, component)
  global_cuts = ctx.obj["global_cuts"]
  names = [f"z{d:d}" for d in range(6)] + ["component"]
  resolved = [_pick(local_cuts[i], global_cuts[i], names[i]) for i in range(7)]

  var_names = _pick(varname, ctx.obj["global_var_names"], "varname") \
      or ["CartGridField"]
  if len(var_names) == 1:
    var_names = var_names[0].split(",")
  # end

  return LoadOptions(
      cuts=tuple(resolved[:6]),
      comp=resolved[6],
      var_names=var_names,
      mapc2p_name=_pick(c2p, ctx.obj["global_c2p"], "c2p"),
      mapc2p_vel_name=_pick(c2p_vel, ctx.obj["global_c2p_vel"], "c2p_vel"))
