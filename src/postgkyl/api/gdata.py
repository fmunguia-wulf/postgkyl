"""``GData`` — the fluent surface (the FLUENT API layer).

A thin subclass of the verb-less :class:`~postgkyl.core.state.GDataState`
container that adds the fluent verb methods and the computing operators. Because
this module sits *above* ``ops``/``render``/``io``, it imports them with plain
top-level imports — there is **no import cycle and no lazy import anywhere**.

Inherited from the container (pure state readers): ``info``, ``__array__``,
``__repr__``/``__str__``, all shape properties, ``copy``/``_result``.
"""

from __future__ import annotations

import operator

import numpy as np

from postgkyl.core.state import GDataState
from postgkyl import ops, io


class GData(GDataState):
  """Fluent dataset: ``pg.load(...).interp().sel(z0=0.0).plot()``."""

  # ---------------------------------------------------------- fluent verbs
  def interp(self, *, basis: str | None = None, p: int | None = None,
      interp: int | None = None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Interpolate DG coefficients onto a uniform mesh (see ``ops.interpolate``)."""
    return ops.interpolate(self, basis=basis, p=p, interp=interp,
        inplace=inplace, tag=tag, label=label)

  # explicit long alias
  interpolate = interp

  def sel(self, *, comp=None, z0=None, z1=None, z2=None, z3=None, z4=None,
      z5=None, inplace: bool = False, tag: str | None = None,
      label: str | None = None) -> "GData":
    """Subselect coordinates/components (see ``ops.select``)."""
    return ops.select(self, comp=comp, z0=z0, z1=z1, z2=z2, z3=z3, z4=z4,
        z5=z5, inplace=inplace, tag=tag, label=label)

  select = sel

  def plot(self, **kwargs):
    """Render this dataset (terminal verb). Returns the matplotlib figure."""
    return ops.plot(self, **kwargs)

  def write(self, out_name: str = "", extension: str = "gkyl") -> str:
    """Write this dataset to disk (see ``io.write``)."""
    return io.write(self, out_name=out_name, extension=extension)

  # ``info`` is inherited from GDataState (a pure state reader).

  # ----------------------------------------------------------- modal verbs
  # Explicit spellings of the weak algebra (the * and / operators dispatch to
  # the same Gkeyll kernels when both operands are modal).
  def mul(self, other) -> "GData":
    """Weak (DG) multiply — runs inside Gkeyll on modal data."""
    return ops.arithmetic.binary(operator.mul, self, other)

  def div(self, other) -> "GData":
    """Weak (DG) divide — runs inside Gkeyll on modal data."""
    return ops.arithmetic.binary(operator.truediv, self, other)

  def integrate(self, *, op: str = "none"):
    """Grid integral of modal data via ``gkyl_array_integrate`` (terminal).

    ``op`` is ``"none"``, ``"abs"``, or ``"sq"``; returns a float (one field)
    or a NumPy array (one value per field)."""
    return ops.integrate(self, op=op)

  # --------------------------------------- representation changes (explicit)
  # Conversions never happen implicitly — these verbs are the only doorway
  # between the modal / nodal / quadrature representations (all gkyl-native).
  def to_modal(self, **kwargs) -> "GData":
    """Convert to modal coefficients (exact from nodal; projection from quad)."""
    return ops.represent(self, to="modal", **kwargs)

  def to_nodal(self, **kwargs) -> "GData":
    """Convert to values at the basis nodes (exact, invertible)."""
    return ops.represent(self, to="nodal", **kwargs)

  def to_quad(self, num_quad: int | None = None, **kwargs) -> "GData":
    """Convert to values at Gauss–Legendre points (default ``p+1`` per dim)."""
    return ops.represent(self, to="quad", num_quad=num_quad, **kwargs)

  def apply(self, fn, *, num_quad: int | None = None, **kwargs) -> "GData":
    """Pointwise ``fn`` via quadrature (modal -> quad -> fn -> modal), e.g.
    ``d.apply(np.sqrt)``. The explicit spelling of nonlinear pointwise math
    on DG data; raise ``num_quad`` to de-alias."""
    return ops.apply(self, fn, num_quad=num_quad, **kwargs)

  # ------------------------------------------------------ binary operators
  def __add__(self, o):      return ops.arithmetic.binary(operator.add, self, o)
  def __sub__(self, o):      return ops.arithmetic.binary(operator.sub, self, o)
  def __mul__(self, o):      return ops.arithmetic.binary(operator.mul, self, o)
  def __truediv__(self, o):  return ops.arithmetic.binary(operator.truediv, self, o)
  def __pow__(self, o):      return ops.arithmetic.binary(operator.pow, self, o)

  def __radd__(self, o):     return ops.arithmetic.binary(operator.add, o, self)
  def __rsub__(self, o):     return ops.arithmetic.binary(operator.sub, o, self)
  def __rmul__(self, o):     return ops.arithmetic.binary(operator.mul, o, self)
  def __rtruediv__(self, o): return ops.arithmetic.binary(operator.truediv, o, self)
  def __rpow__(self, o):     return ops.arithmetic.binary(operator.pow, o, self)

  # ----------------------------------------------------------------- unary
  def __neg__(self): return ops.arithmetic.binary(operator.mul, self, -1.0)
  def __abs__(self): return ops.arithmetic.apply_ufunc(np.absolute, "__call__", self)
  def __pos__(self): return self.copy()

  # --------------------------------------------------------- NumPy interop
  __array_priority__ = 100  # ndarray defers to us in mixed ndarray·GData ops

  def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
    """Make ``np.sqrt``/``np.add``/... return a GData carrying the grid/ctx."""
    return ops.arithmetic.apply_ufunc(ufunc, method, *inputs, **kwargs)
