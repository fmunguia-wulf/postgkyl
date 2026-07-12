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

from .group import DatasetGroup


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

  def save(self, out_name: str = "", extension: str = "gkyl") -> str:
    """Write this dataset to disk (see ``io.save``)."""
    return io.save(self, out_name=out_name, extension=extension)

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

  def integrate_axis(self, axis: int | tuple | str | None = None, *,
      inplace: bool = False, tag: str | None = None,
      label: str | None = None) -> "GData":
    """Trapezoidal integral over one or more axes of point-value data
    (see ``ops.integrate_axis``); a new (reduced) dataset, like ``.sel()``.

    Works on already-interpolated (NumPy) data or a native nodal/quad
    representation; raw modal DG coefficients raise -- convert explicitly
    first (``.interp()``/``.to_nodal()``/``.to_quad()``).
    """
    return ops.integrate_axis(self, axis, inplace=inplace, tag=tag, label=label)

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

  # ------------------------------------------------- field-domain analysis
  # Equation-blind core verbs from layers 07-09 (``ops/__init__.py``), each a
  # one-line delegation to its matching ``ops`` function.
  def fft(self, *, psd: bool = False, iso: bool = False, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Fourier transform / power spectral density (see ``ops.fft``)."""
    return ops.fft(self, psd=psd, iso=iso, inplace=inplace, tag=tag, label=label)

  def magsq(self, *, coords: str = "0:3", inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Magnitude squared of a vector field (see ``ops.magsq``)."""
    return ops.magsq(self, coords=coords, inplace=inplace, tag=tag, label=label)

  def mask(self, mask_data: "GData | None" = None, *, lower: float | None = None,
      upper: float | None = None, inplace: bool = False, tag: str | None = None,
      label: str | None = None) -> "GData":
    """Mask values by a mask dataset or numeric thresholds (see ``ops.mask``)."""
    return ops.mask(self, mask_data, lower=lower, upper=upper, inplace=inplace,
        tag=tag, label=label)

  def val2coord(self, *, x: str, y: str, periodic: bool = False,
      tag: str | None = None, label: str | None = None) -> "DatasetGroup":
    """Build new (x, y) datasets from DynVector columns (see ``ops.val2coord``).

    Wraps the ``ops`` verb's (verb-less) ``core.DatasetGroup`` result in a
    fluent :class:`~postgkyl.api.group.DatasetGroup` so the chain keeps going,
    e.g. ``d.val2coord(x='0', y='1:3')[0].plot()``.
    """
    return DatasetGroup(ops.val2coord(self, x=x, y=y, periodic=periodic,
        tag=tag, label=label))

  def extract_input(self) -> str:
    """Decode the input file embedded in ``ctx`` (see ``ops.extract_input``);
    a terminal verb returning a plain ``str`` (``""`` if none is embedded)."""
    return ops.extract_input(self)

  def fit(self, fit_type: str, *, guess=None, window: bool = False,
      min_n: int | None = None, inplace: bool = False, tag: str | None = None,
      label: str | None = None) -> "GData":
    """Fit a model to this dataset (see ``ops.fit``).

    ``window=True`` fits only the best-scoring leading window of a 1D
    series -- the growth-rate use case, e.g. ``d.fit('exp2', window=True)``.
    """
    return ops.fit(self, fit_type, guess=guess, window=window, min_n=min_n,
        inplace=inplace, tag=tag, label=label)

  def differentiate(self, *, direction: int | None = None, inplace: bool = False,
      tag: str | None = None, label: str | None = None) -> "GData":
    """Numerical gradient of field-domain data (see ``ops.differentiate``)."""
    return ops.differentiate(self, direction=direction, inplace=inplace, tag=tag,
        label=label)

  def map(self, mapping: "str | GData", *, space: str = "conf",
      inplace: bool = False, tag: str | None = None,
      label: str | None = None) -> "GData":
    """Deform this dataset's grid by evaluating a coordinate map (see ``ops.map``)."""
    return ops.map(self, mapping, space=space, inplace=inplace, tag=tag,
        label=label)

  # Note: no fluent ``grid`` method. ``GData.grid`` (inherited from
  # GDataState) is the axis-edge-array property that most of ``ops`` reads
  # via plain attribute access (``data.grid``); a same-named verb method
  # would shadow it for every GData instance and silently break every other
  # verb. ``ops.grid`` (the "turn a dataset's grid into a dataset of
  # coordinates" verb) is reachable as ``postgkyl.ops.grid(data, ...)`` --
  # src_bak's GData carried the identical exception with the identical
  # reasoning (src_bak/postgkyl/data/gdata.py:1258-1259).

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
  def __pos__(self): return self.clone()

  # --------------------------------------------------------- NumPy interop
  __array_priority__ = 100  # ndarray defers to us in mixed ndarray·GData ops

  def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
    """Make ``np.sqrt``/``np.add``/... return a GData carrying the grid/ctx."""
    return ops.arithmetic.apply_ufunc(ufunc, method, *inputs, **kwargs)
