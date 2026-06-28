"""The ``fft`` verb — Fourier transform / power spectral density."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.tools.fft import fft as _fft_arrays

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def fft(data: "GData", *, psd: bool = False, iso: bool = False,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Fourier transform of the data (1D).

  ``psd`` returns the power spectral density |FT|^2 over positive frequencies;
  ``iso`` bins the PSD into a 1D isotropic spectrum.
  """
  grid, values = _fft_arrays(data, psd=psd, iso=iso)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
