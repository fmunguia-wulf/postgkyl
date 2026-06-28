#
# A set of enums in gkeyll. They have to match those in the Gkeyll source code.
#

# Identifiers for specific geometry types
gkyl_geometry_id = [
  "GKYL_GEOMETRY_NONE", # No geometry, use Cartesian.
  "GKYL_GEOMETRY_TOKAMAK", # Tokamak Geometry from Efit.
  "GKYL_GEOMETRY_MIRROR", # Mirror Geometry from Efit.
  "GKYL_GEOMETRY_MAPC2P", # General geometry from user provided mapc2p.
  "GKYL_GEOMETRY_FROMFILE", # Geometry from file.
]

gkyl_basis_type = [
  "GKYL_BASIS_MODAL_SERENDIPITY",
  "GKYL_BASIS_MODAL_TENSOR",
  "GKYL_BASIS_MODAL_HYBRID",
  "GKYL_BASIS_MODAL_GKHYBRID",
  "GKYL_BASIS_MODAL_GKHYBRID_VEL",
]

pgkyl_basis_type = [
  "serendipity",
  "tensor",
  "hybrid",
  "gkhybrid",
  "gkhybrid_vel",
]

def enum_idx_to_key(enum, idx):
  # Given an enum list, return the string corresponding to the index idx
  # provided.
  return enum[idx];

def enum_key_to_idx(enum, key):
  # Given an enum list, return the index of the string key provided.
  return enum.index(key);

def basis_type_gkyl_to_pgkyl(gkyl_basis_type_in):
  # Convert the basis type given as a gkeyll enum int or string,
  # to the string used the rest of postgkyl.
  if isinstance(gkyl_basis_type_in, int):
    return pgkyl_basis_type[gkyl_basis_type_in]
  elif isinstance(gkyl_basis_type_in, str):
    return pgkyl_basis_type[enum_key_to_idx(gkyl_basis_type,gkyl_basis_type_in)]
  else:
    ValueError("Wrong input to basis_type_gkyl_to_pgkyl.")
