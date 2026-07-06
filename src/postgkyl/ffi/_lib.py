"""Load the compiled ``_g0py`` extension — the single capability switch.

The foreign floor is the CPython extension ``postgkyl.ffi._g0py``, built by
``scripts/build_pg0.sh`` against ``gkyl_pg0.h`` — the pg0 shim, which lives
in the gkeyll repo (``core/zero/pg0.c``) and is compiled INTO
``libg0core.so`` by Gkeyll's own build (GKEYLL_C_SHIM.md). There are no
runtime signature declarations and no struct mirrors here: the contract is
enforced by the C compiler at the producer. The one runtime check left is
the ``PG0_API_VERSION`` handshake, which catches a stale ``_g0py.so`` paired
with a newer shim header (or vice versa).

If the extension is missing, :func:`available` returns False and
:func:`require` raises with build guidance; importing postgkyl never fails.
"""

from __future__ import annotations

import pathlib

try:
  from . import _g0py as _mod
  if _mod.api_version() != _mod.PG0_API_VERSION:
    raise ImportError(
        f"pg0 shim version mismatch: _g0py.so was built for API "
        f"{_mod.api_version()}, postgkyl expects {_mod.PG0_API_VERSION}; "
        "rebuild with scripts/build_pg0.sh")
  _ERROR = None
except ImportError as exc:
  _mod = None
  _ERROR = (f"{exc}\nBuild the compiled bridge with scripts/build_gkeyll.sh "
            "(or scripts/build_pg0.sh if libg0core.so already exists).")


def available() -> bool:
  """True when the compiled Gkeyll bridge is loaded (the capability switch)."""
  return _mod is not None


def require():
  """The ``_g0py`` module, or a RuntimeError explaining how to build it."""
  if _mod is None:
    raise RuntimeError(f"postgkyl's Gkeyll bridge is unavailable: {_ERROR}")
  return _mod


def lib_path() -> pathlib.Path | None:
  """Path of the loaded extension (which is rpath-bound to its libg0core)."""
  return pathlib.Path(_mod.__file__) if _mod is not None else None
