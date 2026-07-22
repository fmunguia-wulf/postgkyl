"""``fft`` -- Fourier transform / power spectral density of the working set."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("fft")
@click.option("--psd", "-p", is_flag=True, default=False,
    help="Positive frequencies only, returning the power spectral density |FT|^2.")
@click.option("--iso", "-i", is_flag=True, default=False,
    help="Bin the power spectral density into a 1D isotropic spectrum for multi-D data.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, psd, iso, use, tag, label) -> None:
  """Fourier transform (or PSD) of 1D interpolated data."""
  apply(ctx, lambda d: d.fft(psd=psd, iso=iso, tag=tag, label=label), use=use)
# end
