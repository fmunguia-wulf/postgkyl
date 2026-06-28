import click

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


@click.command()
@click.option("-p", "--psd", is_flag=True,
    help="Limits output to positive frequencies and returns the power spectral density |FT|^2.")
@click.option("-i", "--iso", is_flag=True,
    help="Bins power spectral density |FT|^2, making 1D power spectra from multi-dimensional data.")
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--tag", "-t", help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.pass_context
def fft(ctx, **kwargs):
  """Calculate the Fourier Transform or the power-spectral density of input data.

  Only works on 1D data at present.
  """
  verb_print(ctx, "Starting FFT")
  apply(ctx, ops.fft, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      psd=kwargs["psd"], iso=kwargs["iso"])
  verb_print(ctx, "Finishing FFT")
