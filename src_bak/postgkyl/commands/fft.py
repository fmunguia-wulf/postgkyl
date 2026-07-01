from typing import Annotated

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops
from postgkyl.commands._apply import apply


def fft(
    ctx: typer.Context,
    psd: Annotated[bool, typer.Option("-p", "--psd", help="Limits output to positive frequencies and returns the power spectral density |FT|^2.")] = False,
    iso: Annotated[bool, typer.Option("-i", "--iso", help="Bins power spectral density |FT|^2, making 1D power spectra from multi-dimensional data.")] = False,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Calculate the Fourier Transform or the power-spectral density of input data.

  Only works on 1D data at present.
  """
  apply(ctx, ops.fft, use=use, tag=tag, label=label,
      psd=psd, iso=iso)
