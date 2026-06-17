"""Default gkylsoft path, baked in at install time or edited post-install.

Resolution order (highest priority wins):
  1. --gkylsoft CLI flag (per invocation)
  2. GKYLSOFT environment variable
  3. ~/.postgkyl/gkylsoft_path  (one-line text file, easy to change without reinstalling)
  4. GKYLSOFT_PATH below        (set at install time, or edit this file directly)
"""

GKYLSOFT_PATH = ""

def resolve_gkylsoft_path(cli_override: str | None = None) -> str | None:
  """Return the gkylsoft directory path, or None if not configured."""
  import os

  if cli_override:
    return cli_override

  env = os.environ.get("GKYLSOFT")
  if env:
    return env

  cfg = os.path.expanduser("~/.postgkyl/gkylsoft_path")
  if os.path.isfile(cfg):
    text = open(cfg).read().strip()
    if text:
      return text

  return GKYLSOFT_PATH if GKYLSOFT_PATH else None
