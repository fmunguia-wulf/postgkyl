import typer
from typing import Annotated, Optional

import postgkyl.tools as tools


class FitTypeParam:
  name = "fit_type"

  def fail(self, message, param=None, ctx=None):
    raise typer.BadParameter(message)

  def convert(self, value, param, ctx):
    choices = list(tools.FIT_FUNCTIONS.keys())
    if value in choices:
      return value
    matches = [c for c in choices if c.startswith(value)]
    if len(matches) == 1:
      return matches[0]
    if len(matches) > 1:
      self.fail(f"'{value}' is ambiguous: matches {', '.join(sorted(matches))}", param, ctx)
    # not a known type — accept if it looks like an RPN expression
    toks = set(value.split())
    if toks & (tools.RPN_OPERATORS | set(tools.RPN_FUNCTIONS)):
      return value
    self.fail(
        f"'{value}' does not match any known fit type ({', '.join(choices)}) "
        f"and is not a valid RPN expression (must contain at least one operator or function).",
        param, ctx,
    )

  def get_metavar(self, param, **_):
    return "{" + "|".join(tools.FIT_FUNCTIONS.keys()) + "|<rpn-expr>}"


def _print_result(fit_type, params, std, R2, param_names=None):
  p = params
  s = std
  if fit_type == "linear":
    typer.echo(
        f"Linear:      y = ({p[0]:.6e} ± {s[0]:.2e})*x"
        f" + ({p[1]:.6e} ± {s[1]:.2e})"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "quadratic":
    typer.echo(
        f"Quadratic:   y = ({p[0]:.6e} ± {s[0]:.2e})*x²"
        f" + ({p[1]:.6e} ± {s[1]:.2e})*x"
        f" + ({p[2]:.6e} ± {s[2]:.2e})"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "plane":
    typer.echo(
        f"Plane:       z = ({p[0]:.6e} ± {s[0]:.2e})*x"
        f" + ({p[1]:.6e} ± {s[1]:.2e})*y"
        f" + ({p[2]:.6e} ± {s[2]:.2e})"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "quadratic2d":
    typer.echo(
        f"2D quadratic: z = ({p[0]:.6e} ± {s[0]:.2e})*x²"
        f" + ({p[1]:.6e} ± {s[1]:.2e})*y²"
        f" + ({p[2]:.6e} ± {s[2]:.2e})*x*y"
        f" + ({p[3]:.6e} ± {s[3]:.2e})*x"
        f" + ({p[4]:.6e} ± {s[4]:.2e})*y"
        f" + ({p[5]:.6e} ± {s[5]:.2e})"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "exp_plateau":
    typer.echo(
        f"Exp plateau: y = ({p[0]:.6e} ± {s[0]:.2e})*exp(({p[1]:.6e} ± {s[1]:.2e})*x)"
        f" + ({p[2]:.6e} ± {s[2]:.2e})"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "gaussian":
    typer.echo(
        f"Gaussian:    y = ({p[0]:.6e} ± {s[0]:.2e})"
        f"*exp(-0.5*((x - ({p[1]:.6e} ± {s[1]:.2e}))/({p[2]:.6e} ± {s[2]:.2e}))²)"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "power":
    typer.echo(
        f"Power law:   y = ({p[0]:.6e} ± {s[0]:.2e})*x^({p[1]:.6e} ± {s[1]:.2e})"
        f" + ({p[2]:.6e} ± {s[2]:.2e})"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "sinusoid":
    typer.echo(
        f"Sinusoid:    y = ({p[0]:.6e} ± {s[0]:.2e})"
        f"*sin(({p[1]:.6e} ± {s[1]:.2e})*x + ({p[2]:.6e} ± {s[2]:.2e}))"
        f" + ({p[3]:.6e} ± {s[3]:.2e})"
        f"    R² = {R2:.6f}"
    )
  elif fit_type == "tanh_transition":
    typer.echo(
        f"Tanh:        y = ({p[0]:.6e} ± {s[0]:.2e})"
        f"*tanh((x - ({p[1]:.6e} ± {s[1]:.2e}))/({p[2]:.6e} ± {s[2]:.2e}))"
        f" + ({p[3]:.6e} ± {s[3]:.2e})"
        f"    R² = {R2:.6f}"
    )
  else:
    names = param_names or tools.rpn_param_names(fit_type)
    parts = "  ".join(f"{n} = {p[i]:.6e} ± {s[i]:.2e}" for i, n in enumerate(names))
    typer.echo(f"Custom ({fit_type}):  {parts}    R² = {R2:.6f}")


def fit(
    ctx: typer.Context,
    fit_type: Annotated[str, typer.Argument()],
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to. [default: all]")] = None,
    guess: Annotated[Optional[str], typer.Option("--guess", "-g", help="Comma-separated initial parameter guess.")] = None,
):
  """Fit data with a model and print parameters + R².

  Model types (prefix-matched, same mechanism as pgkyl commands):
    linear          -- y = a*x + b
    quadratic       -- y = a*x² + b*x + c
    plane           -- z = a*x + b*y + c  [2D]
    quadratic2d     -- z = a*x² + b*y² + c*x*y + d*x + e*y + f  [2D]
    exp_plateau     -- y = A*exp(b*x) + C
    gaussian        -- y = A*exp(-0.5*((x-mu)/sigma)²)
    power           -- y = a*x^n + b
    sinusoid        -- y = A*sin(omega*x + phi) + C
    tanh_transition -- y = A*tanh((x-x0)/w) + C

  A custom model can also be given as a Reverse Polish Notation expression.
  x (and y for 2D) are the spatial variables; all other identifiers are free
  parameters.  Supported operators: + - * / ** ^.  Supported functions:
  exp log ln log10 sin cos tan sqrt abs tanh.

  Example:  fit 'a x * b +'   fits y = a*x + b

  1D models require 1D data; 2D models require 2D data. Collapsed dimensions
  (e.g. after integrate) are automatically ignored. Adds the fitted curve as a
  new dataset on the stack (same tag, same nodal grid, values at cell centers).
  """
  from postgkeyll import ops

  data = ctx.obj.data
  fit_type = FitTypeParam().convert(fit_type, None, None)

  for dat in data.iterator(use):
    label = dat.get_label()
    tag = dat.get_tag()
    typer.echo(typer.style(f"{label} ({tag})" if label else tag, bold=True))

    try:
      res = ops.fit(dat, fit_type, guess=guess, tag=dat.get_tag() + "_fit")
    except ValueError as err:
      ctx.fail(str(err))
    # end

    params, stds, r2s = res.ctx["fit_params"], res.ctx["fit_std"], res.ctx["fit_R2"]
    for comp in range(len(params)):
      if len(params) > 1:
        typer.echo(f"  Component {comp}:")
      # end
      _print_result(fit_type, params[comp], stds[comp], r2s[comp])
    # end
    data.add(res)
