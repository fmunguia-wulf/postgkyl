"""Postgkyl module for pressure tensor diagnostics.

Diagnostics include:
	Pressure parallel to the magnetic field
	Pressure perpendicular to the magnetic field
	Agyrotropy (either Frobenius or Swisdak measure)
	Firehose instability threshold
"""

from __future__ import annotations

from typing import Tuple, TYPE_CHECKING
import numpy as np

from postgkyl.tools.prim_vars import get_pij
from postgkyl.tools.mag_sq import mag_sq
from postgkyl.utils import input_parser
if TYPE_CHECKING:
  from postgkyl import GData
#end


def _get_pb(p_in: GData | Tuple[list, np.ndarray],
    b_in: GData | Tuple[list, np.ndarray]) -> Tuple[list, np.ndarray]:
  _, p_values = input_parser(p_in)
  _, b_values = input_parser(b_in)

  p_xx = p_values[..., 0, np.newaxis]
  p_xy = p_values[..., 1, np.newaxis]
  p_xz = p_values[..., 2, np.newaxis]
  p_yy = p_values[..., 3, np.newaxis]
  p_yz = p_values[..., 4, np.newaxis]
  p_zz = p_values[..., 5, np.newaxis]

  b_x = b_values[..., 0, np.newaxis]
  b_y = b_values[..., 1, np.newaxis]
  b_z = b_values[..., 2, np.newaxis]

  return p_xx, p_xy, p_xz, p_yy, p_yz, p_zz, b_x, b_y, b_z


def _get_sf(species: GData | Tuple[list, np.ndarray],
    field: GData | Tuple[list, np.ndarray]) -> Tuple[list, np.ndarray]:
  p_grid, p_values = get_pij(species)
  _, field_values = input_parser(field)

  b_grid = p_grid
  b_values = field_values[..., 3:6]
  return p_grid, p_values, b_grid, b_values


def get_p_par(p_in: GData | Tuple[list, np.ndarray],
    b_in: GData | Tuple[list, np.ndarray]) -> Tuple[list, np.ndarray]:
  """Compute the pressure parallel to the magnetic field.

  Projects the pressure tensor onto the magnetic-field direction:
  ``p_par = (b . P . b) / |B|**2``.

  Args:
    p_in: GData | Tuple[list, np.ndarray]
      Pressure-tensor data with six components in the order
      ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``, as a ``GData`` object or a
      ``(grid, values)`` tuple.
    b_in: GData | Tuple[list, np.ndarray]
      Magnetic-field data with three components ``(Bx, By, Bz)``, as a
      ``GData`` object or a ``(grid, values)`` tuple.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the parallel pressure field.
  """
  _, p_values = input_parser(p_in)
  _, b_values = input_parser(b_in)

  p_xx = p_values[..., 0, np.newaxis]
  p_xy = p_values[..., 1, np.newaxis]
  p_xz = p_values[..., 2, np.newaxis]
  p_yy = p_values[..., 3, np.newaxis]
  p_yz = p_values[..., 4, np.newaxis]
  p_zz = p_values[..., 5, np.newaxis]

  b_x = b_values[..., 0, np.newaxis]
  b_y = b_values[..., 1, np.newaxis]
  b_z = b_values[..., 2, np.newaxis]

  grid, mag_b_sq = mag_sq(b_in)

  out = (b_x*b_x*p_xx + b_y*b_y*p_yy + b_z*b_z*p_zz
      + 2.0*(b_x*b_y*p_xy + b_x*b_z*p_xz + b_y*b_z*p_yz)) / mag_b_sq
  return grid, out


def get_gkyl_10m_p_par(species: GData | Tuple[list, np.ndarray],
    field: GData | Tuple[list, np.ndarray]) -> Tuple[list, np.ndarray]:
  """Compute the parallel pressure directly from Gkeyll 10-moment data.

  Convenience wrapper that builds the pressure tensor from raw 10-moment
  species data and extracts the magnetic field (components 3:6) from the EM
  field data before calling :func:`get_p_par`.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Raw 10-moment species data, as a ``GData`` object or a
      ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data whose components 3:6 are ``(Bx, By, Bz)``, as
      a ``GData`` object or a ``(grid, values)`` tuple.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the parallel pressure field.
  """
  p_grid, p_values = get_pij(species)
  field_grid, field_values = input_parser(field)
  b_values = field_values[..., 3:6]

  return get_p_par((p_grid, p_values), (field_grid, b_values))


def get_p_perp(p_in: GData | Tuple[list, np.ndarray],
    b_in: GData | Tuple[list, np.ndarray]) -> Tuple[list, np.ndarray]:
  """Compute the pressure perpendicular to the magnetic field.

  Uses the trace of the pressure tensor and the parallel pressure:
  ``p_perp = (P_xx + P_yy + P_zz - p_par) / 2``.

  Args:
    p_in: GData | Tuple[list, np.ndarray]
      Pressure-tensor data with six components in the order
      ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``, as a ``GData`` object or a
      ``(grid, values)`` tuple.
    b_in: GData | Tuple[list, np.ndarray]
      Magnetic-field data with three components ``(Bx, By, Bz)``, used to
      compute the parallel pressure, as a ``GData`` object or a
      ``(grid, values)`` tuple.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the perpendicular pressure field.
  """
  _, p_values = input_parser(p_in)

  p_xx = p_values[..., 0, np.newaxis]
  p_yy = p_values[..., 3, np.newaxis]
  p_zz = p_values[..., 5, np.newaxis]

  grid, p_par = get_p_par(p_in, b_in)

  out = (p_xx + p_yy + p_zz - p_par)/2.0
  return grid, out


def get_gkyl_10m_p_perp(species: GData | Tuple[list, np.ndarray],
    field: GData | Tuple[list, np.ndarray]) -> Tuple[list, np.ndarray]:
  """Compute the perpendicular pressure directly from Gkeyll 10-moment data.

  Convenience wrapper that builds the pressure tensor from raw 10-moment
  species data and extracts the magnetic field (components 3:6) from the EM
  field data before calling :func:`get_p_perp`.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Raw 10-moment species data, as a ``GData`` object or a
      ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data whose components 3:6 are ``(Bx, By, Bz)``, as
      a ``GData`` object or a ``(grid, values)`` tuple.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the perpendicular pressure field.
  """
  p_grid, p_values = get_pij(species)
  field_grid, field_values = input_parser(field)

  p_grid, p_values = get_pij(species)
  b_values = field_values[..., 3:6]

  return get_p_perp((p_grid, p_values), (field_grid, b_values))


def get_agyro(p_in: GData | Tuple[list, np.ndarray], b_in: GData | Tuple[list, np.ndarray],
    measure: str = "swisdak") -> Tuple[list, np.ndarray]:
  """Compute the agyrotropy of the pressure tensor.

  The agyrotropy quantifies the departure of the pressure tensor from
  gyrotropy (symmetry about the magnetic field). Two scalar measures are
  supported. The ``'swisdak'`` measure uses the tensor invariants and parallel
  pressure as in Appendix A of Swisdak (2015). The ``'frobenius'`` measure is
  the Frobenius norm of the non-gyrotropic part of the pressure tensor,
  normalized by the gyrotropic part.

  Args:
    p_in: GData | Tuple[list, np.ndarray]
      Pressure-tensor data with six components in the order
      ``(P_xx, P_xy, P_xz, P_yy, P_yz, P_zz)``, as a ``GData`` object or a
      ``(grid, values)`` tuple.
    b_in: GData | Tuple[list, np.ndarray]
      Magnetic-field data with three components ``(Bx, By, Bz)``, as a
      ``GData`` object or a ``(grid, values)`` tuple.
    measure: str
      Agyrotropy measure to use, either ``'swisdak'`` (default) or
      ``'frobenius'`` (case-insensitive). Any other value raises a
      ``ValueError``.

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the agyrotropy field.
  """
  _, p_values = input_parser(p_in)
  _, b_values = input_parser(b_in)

  p_xx = p_values[..., 0, np.newaxis]
  p_xy = p_values[..., 1, np.newaxis]
  p_xz = p_values[..., 2, np.newaxis]
  p_yy = p_values[..., 3, np.newaxis]
  p_yz = p_values[..., 4, np.newaxis]
  p_zz = p_values[..., 5, np.newaxis]

  b_x = b_values[..., 0, np.newaxis]
  b_y = b_values[..., 1, np.newaxis]
  b_z = b_values[..., 2, np.newaxis]

  grid, mag_b_sq = mag_sq(b_in)
  _, p_par = get_p_par(p_in, b_in)
  _, p_perp = get_p_perp(p_in, b_in)

  if measure.lower() == "swisdak":
    I1 = p_xx + p_yy + p_zz
    I2 = (p_xx*p_yy + p_xx*p_zz + p_yy*p_zz
        - (p_xy*p_xy + p_xz*p_xz + p_yz*p_yz))

    # Note that this definition of Q uses the tensor algebra in
    # Appendix A of Swisdak 2015.
    out = np.sqrt(1 - 4 * I2 / ((I1 - p_par) * (I1 + 3 * p_par)))
  elif measure.lower() == "frobenius":
    p_ixx = p_xx - (p_par*b_x*b_x/mag_b_sq + p_perp*(1 - b_x*b_x/mag_b_sq))
    p_ixy = p_xy - (p_par*b_x*b_y/mag_b_sq + p_perp*(0 - b_x*b_y/mag_b_sq))
    p_ixz = p_xz - (p_par*b_x*b_z/mag_b_sq + p_perp*(0 - b_x*b_z/mag_b_sq))
    p_iyy = p_yy - (p_par*b_y*b_y/mag_b_sq + p_perp*(1 - b_y*b_y/mag_b_sq))
    p_iyz = p_yz - (p_par*b_y*b_z/mag_b_sq + p_perp*(0 - b_y*b_z/mag_b_sq))
    p_izz = p_zz - (p_par*b_z*b_z/mag_b_sq + p_perp*(1 - b_z*b_z/mag_b_sq))
    out = np.sqrt(p_ixx**2 + 2*p_ixy**2 + 2*p_ixz**2 + p_iyy**2 + 2*p_iyz**2 + p_izz**2) / np.sqrt(2*p_perp**2 + 4*p_par*p_perp)
  else:
    raise ValueError(f"Measure specified is {measure.lower():s}; it needs to be either 'swisdak' or 'frobenius'")
  # end
  return grid, out


def get_gkyl_10m_agyro(species: GData | Tuple[list, np.ndarray], field: GData | Tuple[list, np.ndarray],
    measure: str = "swisdak") -> Tuple[list, np.ndarray]:
  """Compute the agyrotropy directly from Gkeyll 10-moment data.

  Convenience wrapper that builds the pressure tensor from raw 10-moment
  species data and extracts the magnetic field (components 3:6) from the EM
  field data before calling :func:`get_agyro`.

  Args:
    species: GData | Tuple[list, np.ndarray]
      Raw 10-moment species data, as a ``GData`` object or a
      ``(grid, values)`` tuple.
    field: GData | Tuple[list, np.ndarray]
      Electromagnetic field data whose components 3:6 are ``(Bx, By, Bz)``, as
      a ``GData`` object or a ``(grid, values)`` tuple.
    measure: str
      Agyrotropy measure to use, either ``'swisdak'`` (default) or
      ``'frobenius'`` (case-insensitive).

  Returns:
    Tuple[list, np.ndarray]: A ``(grid, values)`` tuple holding the grid and
    the agyrotropy field.
  """
  p_grid, p_values = get_pij(species)
  field_grid, field_values = input_parser(field)
  b_values = field_values[..., 3:6]

  return get_agyro((p_grid, p_values), (field_grid, b_values), measure=measure)
