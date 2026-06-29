from time import time
import typer

def verb_print(ctx: typer.Context, message: str) -> None:
  if ctx.obj["verbose"]:
    elapsed_time = time() - ctx.obj["start_time"]
    typer.echo(typer.style(f"[{elapsed_time:f}] {message:s}", fg="green"))
  # end
