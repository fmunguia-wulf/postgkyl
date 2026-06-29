import enum
from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkyl import ops
from postgkyl.commands._apply import apply


class _Space(str, enum.Enum):
  conf = "conf"
  vel = "vel"


def map(
    ctx: typer.Context,
    file: Annotated[str, typer.Option("--file", "-f", help="Coordinate-mapping file (mapc2p / mc2nu / mapc2p_vel).")],
    space: Annotated[_Space, typer.Option("--space", "-s", help="Map the leading 'conf' axes or the trailing 'vel' axes.")] = _Space.conf,
    interp: Annotated[Optional[int], typer.Option("--interp", "-i", help="Interpolation points per cell for the mapping field (default: match the data).")] = None,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Deform the grid onto non-uniform mapped coordinates.

  Reads a coordinate-mapping field and replaces a block of grid axes with the
  resulting non-uniform coordinates. A configuration-space map (``-s conf``)
  deforms the leading axes (curvilinearly); a velocity-space map (``-s vel``)
  deforms the trailing ones. The mapping basis is inferred from the file. For a
  combined map, apply the command twice (once per space). Typically run after
  ``interpolate``.
  """
  apply(ctx, ops.map, use=use, tag=tag, label=label,
      mapping=file, space=space.value, interp=interp)
