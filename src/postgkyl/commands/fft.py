from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


def fft(
    ctx: typer.Context,
    psd: Annotated[bool, typer.Option("-p", "--psd", help="Limits output to positive frequencies and returns the power spectral density |FT|^2.")] = False,
    iso: Annotated[bool, typer.Option("-i", "--iso", help="Bins power spectral density |FT|^2, making 1D power spectra from multi-dimensional data.")] = False,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
):
  """Calculate the Fourier Transform or the power-spectral density of input data.

  Only works on 1D data at present.
  """
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting FFT")
  apply(ctx, ops.fft, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      psd=kwargs["psd"], iso=kwargs["iso"])
  verb_print(ctx, "Finishing FFT")
