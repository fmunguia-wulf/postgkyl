from glob import glob
import os
import click
import re

from postgkyl.utils import verb_print


def list_prefixes(path=".", extensions=("bp", "gkyl")):
  """Return the sorted unique simulation prefixes found in ``path``.

  A Gkeyll output file is named ``<prefix>-<name>_<frame>.<ext>``, so the prefix
  (the simulation name, e.g. ``gk_sheath_2x2v_p1``) is the text before the first
  '-'. Files without a '-' in their name are ignored. ``extensions`` may be a
  comma-separated string or any iterable of extensions.
  """
  if isinstance(extensions, str):
    extensions = extensions.split(",")
  prefixes = set()
  for ext in extensions:
    for fn in glob(os.path.join(path, f"*.{ext:s}")):
      base = os.path.basename(fn)
      if "-" in base:
        prefixes.add(base.split("-", 1)[0])
    # end
  # end
  return sorted(prefixes)


@click.command()
@click.option("--extensions", "-e", type=click.STRING,  default="bp,gkyl",
    show_default=True, help="Output file extension(s)")
@click.option("--path", "-p", type=click.Path(exists=True, file_okay=False),
    default=".", show_default=True, help="Path to search for outputs")
@click.option("--prefixes", is_flag=True, default=False,
    help="List unique simulation prefixes (the names before the first '-') "
         "instead of filename stems.")
@click.pass_context
def listoutputs(ctx, **kwargs):
  """List Gkeyll filename stems in the current directory."""
  verb_print(ctx, "Starting listoutputs")

  extensions = kwargs["extensions"].split(",")
  path = kwargs["path"]

  if kwargs["prefixes"]:
    prefixes = list_prefixes(path, extensions)
    if len(prefixes) > 0:
      click.echo("prefixes:")
    # end
    for p in prefixes:
      click.echo(f"- {p:s}")
    # end
    verb_print(ctx, "Finishing listoutputs")
    return
  # end

  for ext in extensions:
    files = glob(f"{path}/*.{ext:s}")
    unique = []
    for fn in files:
      # remove extension
      s = fn[: -(len(ext) + 1)]
      # strip "restart"
      if s.endswith("_restart"):
        s = s[:-8]
      # end
      # strip digits
      s = re.sub(r"_\d+$", "", s)
      if s not in unique:
        unique.append(s)
      # end
    # end
    if len(unique) > 0:
      click.echo(f"{ext:s}:")
    # end
    for s in sorted(unique):
      click.echo(f"- {s:s}")
    # end
  # end
  verb_print(ctx, "Finishing listoutputs")
