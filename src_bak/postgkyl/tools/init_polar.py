import numpy as np


def init_polar(nkx, nky, nkz, kx, ky, kz, nkpolar):
  """Build a polar (k-perpendicular) binning of a Cartesian wavenumber grid.

  Constructs uniformly spaced polar bins in ``k = sqrt(kx**2 + ky**2 [+ kz**2])``
  and assigns each Cartesian wavenumber cell to a bin, for later isotropic
  (shell) averaging of spectra. Works for 2D grids (set ``nkz`` and ``kz`` to
  ``0``) and 3D grids.

  Args:
    nkx: int
      Number of grid points along the ``kx`` axis.
    nky: int
      Number of grid points along the ``ky`` axis.
    nkz: int
      Number of grid points along the ``kz`` axis; use ``0`` for 2D data.
    kx: array-like
      1D array of ``kx`` wavenumbers; ``kx[1]`` sets the spacing ``dkx``.
    ky: array-like
      1D array of ``ky`` wavenumbers; ``ky[1]`` sets the spacing ``dky``.
    kz: array-like
      1D array of ``kz`` wavenumbers; ``kz[1]`` sets the spacing ``dkz``. Use
      ``0`` for 2D data.
    nkpolar: int
      Number of polar (radial ``k_perp``) bins to create. If ``0``, no binning
      is performed and empty outputs are returned.

  Returns:
    tuple: ``(akp, nbin, polar_index, akplim)`` where ``akp`` is the array of
    polar bin centers (the ``k_perp`` grid), ``nbin`` is the count of Cartesian
    cells assigned to each bin, ``polar_index`` is an integer array (shape
    matching the Cartesian grid) giving the bin index of each cell, and
    ``akplim`` is the array of polar bin edges.
  """
  # if 2D, nkz and kz = 0

  if nkpolar == 0:
    akp = []
    nbin = 0
    polar_index = []
    akplim = []
  elif nkz == 0:
    nbin = np.zeros(nkpolar)  # Number of kx,ky in each polar bins
    polar_index = np.zeros((nkx, nky), dtype=int)  # Polar index to simplify binning
    if nkx == 1 & nky == 1:
      dkp = 0
    elif nkx == 1:
      dkp = ky[1]
    elif nky == 1:
      dkp = kx[1]
    else:
      dkp = max(kx[1], ky[1])
    akp = (np.linspace(1, nkpolar, nkpolar)) * dkp  # Kperp grid
    akplim = dkp / 2 + (np.linspace(0, nkpolar, nkpolar + 1))*dkp  # Bin limits
    # Re-written to avoid loops. Necessary for large grids.
    [kxg, kyg] = np.meshgrid(
        ky, kx
    )  # Deal with meshgrid weirdness (so do not have to transpose)
    kp = np.sqrt(kxg**2 + kyg**2)
    pn = np.where(kp >= akplim[nkpolar])
    polar_index[pn[0], pn[1]] = nkpolar - 1
    nbin[nkpolar - 1] = nbin[nkpolar - 1] + len(pn[0])
    for ik in range(0, nkpolar):
      pn = np.where((kp < akplim[ik + 1]) & (kp >= akplim[ik]))
      polar_index[pn[0], pn[1]] = ik
      nbin[ik] = nbin[ik] + len(pn[0])
  else:
    # 3D data
    nbin = np.zeros(nkpolar)
    polar_index = np.zeros((nkx, nky, nkz), dtype=int)
    if nkx == 1 & nky == 1 & nkz == 1:
      dkp = 0
    elif nkx == 1:
      dkp = max(ky[1], kz[1])
    elif nky == 1:
      dkp = max(kx[1], kz[1])
    elif nkz == 1:
      dkp = max(kx[1], ky[1])
    else:
      dkp = max(kx[1], ky[1], kz[1])
    akp = (np.linspace(1, nkpolar, nkpolar)) * dkp  # kperp grid
    akplim = dkp / 2 + (np.linspace(0, nkpolar, nkpolar + 1)) * dkp  # bin limits
    # Re-written to avoid loops
    [kxg, kyg, kzg] = np.meshgrid(ky, kx, kz)
    kp = np.sqrt(kxg**2 + kyg**2 + kzg**2)
    pn = np.where(kp >= akplim[nkpolar])
    polar_index[pn[0], pn[1], pn[2]] = nkpolar - 1
    nbin[nkpolar - 1] = nbin[nkpolar - 1] + len(pn[0])
    for ik in range(0, nkpolar):
      pn = np.where((kp < akplim[ik + 1]) & (kp >= akplim[ik]))
      polar_index[pn[0], pn[1], pn[2]] = ik
      nbin[ik] = nbin[ik] + len(pn[0])

  return akp, nbin, polar_index, akplim
