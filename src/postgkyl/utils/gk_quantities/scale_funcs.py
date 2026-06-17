"""Default scaling functions for gk_quantities registry."""

import postgkyl.utils.gkeyll_const as gkc

def scale_disabled(gdata_in):
  """Return values unchanged (no scaling)."""
# end

def scale_massDev(gdata_in):
  """Multiply by the mass and divide by the elementary charge"""
  mass = gdata_in.ctx["mass"]
  eV = gkc.GKYL_ELEMENTARY_CHARGE
  fac = mass/eV

  gdata_in.set_values(fac * gdata_in.get_values())
# end
