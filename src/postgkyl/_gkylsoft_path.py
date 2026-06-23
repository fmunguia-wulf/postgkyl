"""
Default gkylsoft path, baked in at install time or edited post-install.

Ways to specify gkylsoft path (from highest to lowest priority):
  1. Manually specified (alt_gkylsoft_dir argument).
  2. GKYLSOFT_DIR environment variable.
  3. GKYLSOFT_DIR=... in the config file (default ~/.postgkyl/gkylsoft_path,
     overridden by the POSTGKYL_CONFIG environment variable).
  4. GKYLSOFT_DIR below (set at install time, or edit this file directly).
"""

GKYLSOFT_DIR = ""

def default_config_path() -> str:
  """Return the config file path, respecting POSTGKYL_CONFIG if set."""
  import os
  return os.environ.get("POSTGKYL_CONFIG",
                        os.path.expanduser("~/.postgkyl/gkylsoft_path"))

def resolve_gkylsoft_path(alt_gkylsoft_dir: str | None = None) -> str | None:
  """Return the gkylsoft directory path, or None if not configured."""
  import os

  if alt_gkylsoft_dir:
    return alt_gkylsoft_dir

  env = os.environ.get("GKYLSOFT_DIR")
  if env:
    return env

  cfg = default_config_path()
  if os.path.isfile(cfg):
    text = open(cfg).read().strip()
    if text:
      return text.split("=")[1]

  return GKYLSOFT_DIR if GKYLSOFT_DIR else None
