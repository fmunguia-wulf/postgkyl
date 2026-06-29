import enum
import shutil

import typer
from typing import Annotated, Optional

from postgkyl.commands._apply import enum_value



class _Mode(str, enum.Enum):
  gkyl = "gkyl"
  bp = "bp"
  txt = "txt"
  npy = "npy"
  vts = "vts"


def write(
    ctx: typer.Context,
    filename: Annotated[str, typer.Argument()],
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    mode: Annotated[Optional[_Mode], typer.Option("-m", "--mode", help="Output file mode. One of `gkyl` (binary, default), `bp` (ADIOS BP file), `txt` (ASCII text file), `npy` (NumPy binary file), or `vts` (VTK structured grid with ParaView time-series sidecar).")] = _Mode.gkyl,
    single: Annotated[bool, typer.Option("-s", "--single", help="Write all dataset into one file")] = False,
    normalize_axes: Annotated[bool, typer.Option("--normalize-axes", "-n", help="Normalize VTK axes to [-1, 1] range before writing.")] = False,
):
  """Write active dataset to a file.

  The output file format can be set with ``--format``, and is Gkeyll's .gkyl by default.
  Files saved as .gkyl or .bp can be later loaded back into pgkyl to further manipulate
  or plot.
  """
  data = ctx.obj.data

  var_name = None
  append = False
  cleaning = True
  fn = filename
  mode = enum_value(mode)
  if len(fn.split(".")) > 1:
    mode = str(fn.split(".")[-1])
    fn = str(fn.split(".")[0])
  # end

  num_files = data.get_num_datasets(tag=use)
  for i, dat in data.iterator(tag=use, enum=True):
    out_name = f"{fn:s}.{mode:s}"
    if single:
      var_name = f"{dat.get_tag():s}_{i:d}"
      cleaning = False
    else:
      if num_files > 1:
        out_name = f"{fn:s}_{i:d}.{mode:s}"
      # end
    # end

    dat.write(out_name=out_name, mode=mode, append=append, var_name=var_name, cleaning=cleaning, norm_axes=normalize_axes)

    if single:
      append = True
    # end
  # end

  # Cleaning
  if not cleaning:
    shutil.move(f"{fn:s}.{mode:s}.dir/{fn:s}.{mode:s}.0", f"{fn:s}.{mode:s}")
    shutil.rmtree(f"{fn:s}.{mode:s}.dir")
  # end
