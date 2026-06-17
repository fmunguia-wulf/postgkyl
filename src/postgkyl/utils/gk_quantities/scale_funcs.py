"""Default scaling functions for gk_quantities registry."""

from postgkyl.utils.gkeyll_const as gkconst

def scale_disabled(gdata_in):
  """Return values unchanged (no scaling)."""
# end

def scale_massDe(gdata_in):
  """Multiply by the mass and divide by the elementary charge"""
  mass = gdata_in.ctx["mass"]
  eV = gkconst.GKYL_ELEMENTARY_CHARGE
  fac = mass/eV

  gdata_in.set_values(fac * gdata_in.get_values())
# end
