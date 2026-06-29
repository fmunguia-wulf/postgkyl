"""The ``fft`` verb — Fourier transform / power spectral density."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.fft import fft as _fft_arrays

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def fft(data: "GData", *, psd: bool = False, iso: bool = False,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Fourier transform of the data.

  Wraps the scipy FFT, transforming each component over the spatial axes
  (dummy axes of length <= 2 are squeezed out first). Supports 1D, 2D, and 3D
  data. By default returns the complex transform over the full frequency
  range.

  Args:
    data: GData
      The dataset to transform.
    psd: bool
      When True, return the power spectral density ``|FT|^2`` over the
      positive frequencies only.
    iso: bool
      When True (only meaningful for 2D/3D data with ``psd=True``), bin the
      PSD into a 1D isotropic spectrum over the polar wavenumber magnitude.
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData whose grid is the frequency/wavenumber axis (or axes) and whose
    values are the transform, PSD, or isotropic spectrum (or the mutated input
    when inplace=True).

  Raises:
    ValueError: If isotropic binning is requested for data that is not 2D or
      3D.
  """
  grid, values = _fft_arrays(data, psd=psd, iso=iso)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
