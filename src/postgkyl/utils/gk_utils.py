#
# Hardcoded parameters and auxiliary functions
# used in gyrokinetic functions.
#
import numpy as np
import os
import glob
from postgkyl.data import GInterpModal
from postgkyl.data import GData
from postgkyl.utils import verb_print
import postgkyl.utils.gkeyll_enums as gkenums

max_num_blocks = 10000 # Maximum number of blocks.

file_fmt = '.gkyl' # File format assumed.

# Labels used to identify boundary flux files.
edges = ["lower","upper"]
dirs = ["x","y","z"]
# Line styles.
line_styles = ['-','--',':','-.','None','None','None','None']
# Font sizes.
xy_label_font_size = 17
title_font_size = 17
tick_font_size = 14
legend_font_size = 14
colorbar_label_font_size = 17

def set_tick_font_size(axIn,fontSizeIn):
  # Set the font size of the ticks to a given size.
  axIn.tick_params(axis='both',labelsize=fontSizeIn)
  offset_txt = axIn.yaxis.get_offset_text() # Get the text object
  offset_txt.set_size(fontSizeIn) # Set the size.
  offset_txt = axIn.xaxis.get_offset_text() # Get the text object
  offset_txt.set_size(fontSizeIn) # Set the size.

def read_gfile(file_name, **kwargs):
  # Read a Gkeyll file.
  c2p_file = None
  if "mapc2p" in kwargs.keys():
    c2p_file = kwargs["mapc2p"]

  pgData = GData(file_name, mapc2p_name=c2p_file) # Read data with pgkyl.
  grid = pgData.get_grid() # Time stamps of the simulation.
  vals = pgData.get_values() # Data values.
  if isinstance(grid, np.ndarray):
    grid_out = np.squeeze(grid)
  else:
    grid_out = list()
    for d in range(len(grid)):
      grid_out.append(np.squeeze(grid[d]))

  return grid_out, np.squeeze(vals), pgData

def read_gfile_if_present(file_name, **kwargs):
  # Check if a Gkeyll file exists. If it does, read it and return
  # its grid, data and GData object. If it doesn't, return None.
  if os.path.exists(file_name):
    grid, vals, pgdat = read_gfile(file_name, kwargs)
    return True, np.squeeze(grid), np.squeeze(vals), pgdat
  else:
    verb_print(ctx, "  -> File "+file_name+" not found. Proceeding w/o it.")
    return False, None, None, None

def read_interp_gfile(file_name, poly_order, basis_type, comp=0):
  # Read a Gkeyll file and interpolate its DG dataset assuming it has a
  # polynomial basis of 'poly_order' order and basis type 'basis_type'.
  # Optional argument 'comp' requests a specific component if a file
  # contains multiple DG datasets.
  pgData = GData(file_name) # Read data with pgkyl.
  interp = GInterpModal(pgData,poly_order,basis_type)
  grid, vals = interp.interpolate(comp)
  if isinstance(grid, np.ndarray):
    grid_out = np.squeeze(grid)
  else:
    grid_out = list()
    for d in range(len(grid)):
      grid_out.append(np.squeeze(grid[d]))

  return grid_out, np.squeeze(vals), pgData

def parse_slice_string(value):
  # Parse a 'slice()' from string, like 'start:stop:step'.
  parts = value.split(':')
  # Convert parts to integers, replacing empty strings with None for slice defaults
  parsed_parts = []
  for p in parts:
    try:
      parsed_parts.append(int(p) if p else None)
    except ValueError:
      # Handle cases where the part might not be a number
      raise ValueError(f"Invalid slice part: {p}")
  # Create the slice object with the appropriate number of arguments
  return slice(*parsed_parts)

def get_block_indices(multib, file_path_name):
  # Return a list of the indices of the blocks in a multiblock simulation
  # to be processed.
  #   - multib: ="-10" single block.
  #             ="-1" will find all the blocks.
  #             =comma-separated list or slice of desired blocks to use.
  #   - file_path_name: path and file name used to find blocks, with block
  #                     index replaced by "*", e.g. "<sim_name>_b*-<species>_field_0.gkyl".
  def is_str_an_int(str_in):
    try:
      int(str_in)
      return True
    except ValueError:
      return False
    # end
  # end

  if multib == "-10":
    # Single block.
    blocks = [0]
  else:
    # Multi block.
    if multib == "-1":
      # Find and use all blocks.
      file_list = glob.glob(file_path_name)
      num_blocks = len(file_list)
      blocks = list(range(num_blocks))
    else:
      # Use specified blocks.
      if ',' in multib:
        blocks = multib.split(",")
        num_blocks = len(blocks)
        blocks = [int(blocks[i]) for i in range(num_blocks)]
      elif ':' in multib:
        slice_obj = parse_slice_string(multib)
        blocks = list(range(*slice_obj.indices(max_num_blocks)))
      elif is_str_an_int(multib): 
        blocks = [int(multib)]
      else:
        raise NameError("Blocks given to --multib -m must be a comma separated list or slice.")

  return blocks

def is_gdata_geo_mapc2p(gdata):
  # Determine whether the GData object, gdata, is from a simulation with MAPC2P
  # geometry. If geometry_type is missing from the metadata, default to true.
  gdata_meta = gdata.get_ctx()
  is_mapc2p = True
  if ("geometry_type" in gdata_meta):
    if "geometry_type" in gdata_meta.keys():
      mc2p_idx = gkenums.enum_key_to_idx(gkenums.gkyl_geometry_id,"GKYL_GEOMETRY_MAPC2P")
      is_mapc2p = mc2p_idx == gdata_meta["geometry_type"]
    # end
  #end
  return is_mapc2p

#quant_attributes = {
#  "den"    : {
#    "files"      : [["M0"],["MaxwellianMoments"],["BiMaxwellianMoments"],],
#    "fetch_func" : [fccq_get_c0, fccq_get_c0, fccq_get_c0,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$n_%s$ (m$^{-3}$)'
#  },
#  "upar"   : {
#    "files"      : [["MaxwellianMoments"],["BiMaxwellianMoments"],["M0","M1"],],
#    "fetch_func" : [fccq_get_c1, fccq_get_c1, fccq_get_f1Df0,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$u_{\parallel %s}$ (m$^{-3}$)'
#  },
#  "tpar"   : {
#    "files"      : [["BiMaxwellianMoments"],],
#    "fetch_func" : [fccq_get_c2,],
#    "scale_func" : [fccq_scale_mDe,],
#    "label"      : r'$T_{\parallel %s}$ (eV)'
#  },
#  "tperp"  : {
#    "files"      : [["BiMaxwellianMoments"],],
#    "fetch_func" : [fccq_get_c3, ],
#    "scale_func" : [fccq_scale_mDe,],
#    "label"      : r'$T_{\perp %s}$ (eV)'
#  },
#  "temp"   : {
#    "files"      : [["MaxwellianMoments"],["BiMaxwellianMoments"],],
#    "fetch_func" : [fccq_get_c2, fccq_2c3Pc2D3],
#    "scale_func" : [fccq_scale_mDe,],
#    "label"      : r'$T_{%s}$ (eV)'
#  },
#  "m0"     : {
#    "files"      : [["M0"],["M0M1M2"],["M0M1M2PARM2PERP"],["MaxwellianMoments"],["BiMaxwellianMoments"],],
#    "fetch_func" : [fccq_get_c0, fccq_get_c0, fccq_get_c0, fccq_get_c0, fccq_get_c0,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$M_{0 %s}$ (m$^{-3}$)'
#  },
#  "m1"     : {
#    "files"      : [["M1"],["M0M1M2"],["M0M1M2PARM2PERP"],],
#    "fetch_func" : [fccq_get_c0, fccq_get_c1, fccq_get_c1,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$M_{1 %s}$ (m$^{-2}$ s^{-1})'
#  },
#  "m2par"  : {
#    "files"      : [["M2PAR"],["M0M1M2PARM2PERP"],],
#    "fetch_func" : [fccq_get_c0, fccq_get_c2,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$M_{2\parallel %s}$ (m$^{-1}$ s^{-2})'
#  },
#  "m2perp" : {
#    "files"      : [["M2PERP"],["M0M1M2PARM2PERP"],],
#    "fetch_func" : [fccq_get_c0, fccq_get_c3,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$M_{2\perp %s}$ (m$^{-1}$ s^{-2})'
#  },
#  "m2"     : {
#    "files"      : [["M2"],["M0M1M2"],["M0M1M2PARM2PERP"],["M2PAR","M2PERP"],],
#    "fetch_func" : [fccq_get_c0, fccq_get_c2, fccq_get_c2Pc3, fccq_get_f0Pf1,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$M_{2 %s}$ (m$^{-1}$ s^{-2})'
#  },
#  "m3par"  : {
#    "files"      : [["M3PAR"],],
#    "fetch_func" : [fccq_get_c0,],
#    "scale_func" : [fccq_scale_disabled,],
#    "label"      : r'$M_{3\parallel %s}$ (s^{-3})'
#  },
#  "m3perp" : {
#    "files"      : [["M3PERP"],],
#    "fetch_func" : [fccq_get_c0,],
#    "scale_func" : [fccq_scale_disabled,],
#    "label"      : r'$M_{3\perp %s}$ (s^{-3})'
#  },
#  "m3"     : {
#    "files"      : [["M3"],["M3PAR","M3PERP"],],
#    "fetch_func" : [fccq_get_c0, fccq_get_f0Pf1,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$M_{3 %s}$ (s^{-3})'
#  },
#  "phi"    : {
#    "files"      : [["field"],],
#    "fetch_func" : [fccq_get_c0,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$\phi$ (V)'
#  },
#  "bmag"   : {
#    "files"      : [["bmag"],],
#    "fetch_func" : [fccq_get_c0,],
#    "scale_func" : [fccq_scale_disabled, fccq_scale_disabled, fccq_scale_disabled,],
#    "label"      : r'$B$ (T)'
#  },
#}

#
# End of hardcoded parameters and auxiliary functions.
#
