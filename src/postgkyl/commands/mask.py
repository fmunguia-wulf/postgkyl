import click

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


@click.command()
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--filename", "-f", type=click.STRING, help="Specify the file with a mask.")
@click.option("--lower", type=click.FLOAT,
    help="Specify the lower threshold; values below it are masked out.")
@click.option("--upper", type=click.FLOAT,
    help="Specify the upper threshold; values above it are masked out.")
@click.option("--tag", "-t", help="Optional tag for the resulting array.")
@click.option("--label", "-l", help="Custom label for the result.")
@click.pass_context
def mask(ctx, **kwargs):
  """Mask data with a Gkeyll mask file or by numeric thresholds."""
  verb_print(ctx, "Starting mask")
  apply(ctx, ops.mask, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      filename=kwargs["filename"], lower=kwargs["lower"], upper=kwargs["upper"])
  verb_print(ctx, "Finishing mask")
