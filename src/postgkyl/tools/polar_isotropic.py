import numpy as np


def polar_isotropic(nkpolar, nkx, nky, nkz, polar_index, nbin, fft_matrix, kx, ky, kz):
  """Average a spectrum over polar (k-perpendicular) shells.

  Accumulates the values of ``fft_matrix`` into the polar bins defined by
  ``polar_index`` (as produced by :func:`init_polar`) and divides by the number
  of cells per bin to obtain the isotropic (shell-averaged) spectrum. Works for
  2D grids (set ``nkz`` and ``kz`` to ``0``) and 3D grids.

  Args:
    nkpolar: int
      Number of polar (radial ``k_perp``) bins.
    nkx: int
      Number of grid points along the ``kx`` axis.
    nky: int
      Number of grid points along the ``ky`` axis.
    nkz: int
      Number of grid points along the ``kz`` axis; use ``0`` for 2D data.
    polar_index: np.ndarray
      Integer array mapping each Cartesian wavenumber cell to its polar bin, as
      returned by :func:`init_polar`.
    nbin: np.ndarray
      Number of Cartesian cells in each polar bin, used as the averaging
      denominator.
    fft_matrix: np.ndarray
      Spectral quantity (e.g. spectral power) defined on the Cartesian
      wavenumber grid to be averaged over shells.
    kx: array-like
      1D array of ``kx`` wavenumbers (accepted for interface consistency).
    ky: array-like
      1D array of ``ky`` wavenumbers (accepted for interface consistency).
    kz: array-like
      1D array of ``kz`` wavenumbers (accepted for interface consistency).

  Returns:
    np.ndarray: The shell-averaged (isotropic) spectrum, one value per polar
    bin (shape ``(nkpolar,)``).
  """
  # if 2D, then nkz = kz = 0

  fft_isok = np.zeros(nkpolar)
  if nkz == 0:
    for i in range(0, nkx):
      for j in range(0, nky):
        fft_isok[polar_index[i, j]] = fft_isok[polar_index[i, j]] + fft_matrix[i, j]
  else:
    for i in range(0, nkx):
      for j in range(0, nky):
        for k in range(0, nkz):
          fft_isok[polar_index[i, j, k]] = fft_isok[polar_index[i, j, k]] + fft_matrix[i, j, k]

  fft_isok = fft_isok / nbin[:]
  return fft_isok
