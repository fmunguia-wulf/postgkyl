from cycler import cycler
import typer

def load_style(ctx: typer.Context, fn: str) -> None:
  fh = open(fn, "r", encoding="utf-8")
  for line in fh.readlines():
    key = line.split(":")[0]
    key_len = int(len(key))
    key = key.strip()
    value = line[(key_len + 1) :].strip()
    if value[:6] == "cycler":
      arg = eval(value[16:-1])
      value = cycler(color=arg)
    # end
    ctx.obj.rcParams[key] = value
  # end
  fh.close()
