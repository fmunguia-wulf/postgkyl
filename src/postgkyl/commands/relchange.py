import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command(help="Computes the relative change between two datasets")
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--index", "-i", type=click.INT, default=0, show_default=True,
    help="Dataset index for computing change relative to.")
@click.option("--comp", "-c", default=None, show_default=True,
    help="Dataset component to be compared to if user only wants to compare to a single component.")
@click.option("--tag", "-t", default="rel_change", show_default=True, help="Tag for the result.")
@click.option("--label", "-l", default="delta", show_default=True, help="Custom label for the result/")
@click.pass_context
def relchange(ctx, **kwargs):
  verb_print(ctx, "Starting relative change")

  data = ctx.obj["data"]
  for tag in data.tag_iterator(kwargs["use"]):
    reference = data.get_dataset(kwargs["index"], tag)
    for dat in data.iterator(tag):
      if kwargs["tag"]:
        out = ops.relchange(dat, reference, comp=kwargs["comp"], tag=kwargs["tag"])
        dat.deactivate()
        data.add(out)
      else:
        ops.relchange(dat, reference, comp=kwargs["comp"], inplace=True)
      # end
    # end
  # end
  verb_print(ctx, "Finishing relative change")
