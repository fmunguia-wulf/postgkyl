import glob
import os

from postgkyl.data import GData

class GkQuantity:
  """
  Class for a gyrokinetic quantity.

  Attributes:
    name: Name of the quantity.
    source: List of file combinations to try.
    fetch_func: Corresponding fetch function for each file combo.
    label: LaTeX format label for matplotlib (use %s for species name or direction).
    is_time_dep: If the quantity is time-dependent (i.e. written in frames).
    is_species_dep: If the quantity is species-dependent.
    is_vector: If the quantity is a vector (i.e. has multiple components).
  """
  name = None
  source = None
  fetch_func = None
  label = None
  is_time_dep = None
  is_species_dep = None
  is_vector = None
  is_tensor = None
  is_integrated = None
  is_geo = None

  def __init__(self, name : str, source : list, fetch_func : callable, label : str,
               is_time_dep : bool = False, is_species_dep : bool = False, is_vector : bool = False,
               is_tensor : bool = False, is_integrated : bool = False, is_geo : bool = False):
    self.name = name
    self.source = source
    self.fetch_func = fetch_func
    self.label = label
    self.is_time_dep = is_time_dep
    self.is_species_dep = is_species_dep
    self.is_vector = is_vector
    self.is_tensor = is_tensor
    self.is_integrated = is_integrated
    self.is_geo = is_geo

  # Internal methods.

  def _src_stem(self, path : str, name : str, species : str, src : str) -> str:
    """
    Stem of the file name for a string source, including the trailing
    separator before the frame number (geo files have no frame, so no separator).
    """
    if self.is_geo:
      return os.path.join(path, f"{name}-{src}")
    elif self.is_species_dep:
      return os.path.join(path, f"{name}-{species}_{src}_")
    else:
      return os.path.join(path, f"{name}-{src}_")

  def _src_file_name(self, path : str, name : str, species : str, src : str,
                    frame : int | None) -> str:
    """Full file name for a string source at the given frame."""
    if self.is_geo:
      return f"{self._src_stem(path, name, species, src)}.gkyl"
    else:
      return f"{self._src_stem(path, name, species, src)}{frame}.gkyl"

  def _avail_frames_src(self, path : str, name : str, species : str, src : str,
                       frames : list[int] | None = None) -> set[int]:
    """
    Set of available frames for a string source's file <stem><frame>.gkyl.
    Optionally restrict the search to the given list of frames.
    """
    frames_avail : set[int] = set()
    stem = self._src_stem(path, name, species, src)

    if frames:
      candidates = (f"{stem}{f}.gkyl" for f in frames if os.path.isfile(f"{stem}{f}.gkyl"))
    else:
      candidates = glob.glob(f"{glob.escape(stem)}*.gkyl")

    for f in candidates:
      suffix = f[len(stem):-5]
      if suffix.isdigit():
        frames_avail.add(int(suffix))
    return frames_avail

  def _avail_combo_frames(self, path : str, name : str, species : str,
                         frames : list[int] | None = None) -> tuple[int, set[int]]:
    """
    Find the first source combination whose files all exist and share the
    same set of available frames. Returns (combo index, available frames).
    A combination made up only of geo files is flagged with {-1}.
    """
    frames_avail : set[int] = set()
    combo_idx = 0
    # Check each combination of sources.
    for cidx, combo in enumerate(self.source):
      # Check each source for this combo.
      for src in combo:
        if isinstance(src, str) and self.is_geo:
          # Geo files have no frame number; just check the file exists.
          if not os.path.isfile(os.path.join(path, f"{name}-{src}.gkyl")):
            frames_avail = set()
            break
          continue

        if isinstance(src, str):
          frames_avail_q = self._avail_frames_src(path, name, species, src, frames)
        else:
          _, frames_avail_q = src._avail_combo_frames(path, name, species, frames)

        if frames_avail_q == {-1}:
          # Source is a geo-only quantity: doesn't constrain frames, just needs to exist.
          combo_idx = cidx
          continue

        if frames_avail_q:
          if not frames_avail:
            frames_avail = set(frames_avail_q)
          elif frames_avail_q != frames_avail:
            # This source has different frames than previously checked files in
            # this combo, so go to the next combo.
            frames_avail = set()
            break
          combo_idx = cidx
        else:
          break
      else:
        # If all sources were geo files, frames_avail is still empty.
        # Mark the combo as valid with {-1}.
        if not frames_avail:
          frames_avail = {-1}
          combo_idx = cidx

      if frames_avail:
        break

    return combo_idx, frames_avail

  # Public methods.

  def get_label(self, species : str | None = None, direction : str | None = None) -> str:
    """Get the label for the quantity, replacing %s with species name or direction."""
    print(f"get_label: species={species}, direction={direction}")
    print(f"self.label={self.label}, self.is_vector={self.is_vector}, self.is_species_dep={self.is_species_dep}")
    if self.is_vector:
      if direction is not None:
        return self.label % str(direction)
      else:
        return self.label % 'i'
    elif self.is_species_dep:
      if species is not None:
        return self.label % str(species[0])
      else:
        return self.label % 's'
    else:
      return self.label

  def get_avail_source(self, path : str, name : str, species : str,
                    frame_inp : str | None) -> tuple[int, list[int | None]]:
    """
    Identify the source combination and list of frames needed to get this
    quantity. frame_inp may be a single frame, a comma-separated list, or a
    'start:stop[:step]' range (None or ':' means all available frames).
    """
    frame_list : list[int] = []
    if frame_inp is not None:
      frame_inp = frame_inp.strip()
      if "," in frame_inp:
        frame_list = [int(f.strip()) for f in frame_inp.split(",")]
      elif ":" not in frame_inp:
        frame_list = [int(frame_inp)]

    # Discover available frames from any of the possible source combinations.
    combo_idx, frames_avail = self._avail_combo_frames(path, name, species, frame_list)

    if not frames_avail:
      raise FileNotFoundError(f"No files found for the requested quantity "
                              f"(path='{path}', name='{name}').")

    # Geo-only quantities have no frame number; return a single None sentinel.
    if frames_avail == {-1}:
      return combo_idx, [None]

    # Expand a range request against the available frames.
    if len(frame_list) == 0:
      frames_avail_sorted = sorted(frames_avail)
      parts = frame_inp.split(":") if frame_inp else [""]
      lower = int(parts[0]) if parts[0] else frames_avail_sorted[0]
      upper = int(parts[1]) if len(parts) > 1 and parts[1] else frames_avail_sorted[-1] + 1
      step  = int(parts[2]) if len(parts) == 3 and parts[2] else 1
      frame_list = [f for f in frames_avail_sorted if lower <= f < upper and (f - lower) % step == 0]

    return combo_idx, frame_list

  def get_src_gdata(self, src : "str | GkQuantity", path : str, name : str,
                    species : str, frame : int | None) -> GData:
    """
    Get the populated GData for a source, which is either a string (file
    name) or a GkQuantity (computed from its own sources).
    """
    if isinstance(src, str):
      return GData(self._src_file_name(path, name, species, src, frame))

    # src is a GkQuantity: resolve its own source combination and compute it.
    combo_idx, _ = src.get_avail_source(path, name, species, str(frame))
    combo = src.source[combo_idx]
    fetch_func = src.fetch_func[combo_idx]
    gdatas = [src.get_src_gdata(s, path, name, species, frame) for s in combo]
    return fetch_func(gdatas)

  def fetch(self, path : str, name : str, species : str, frame : int | None,
            combo_idx : int, **extra) -> GData:
    """
    Load this quantity's sources for the given combination and frame, then
    compute and return the resulting GData.
    """
    combo = self.source[combo_idx]
    fetch_func = self.fetch_func[combo_idx]
    gdatas = [self.get_src_gdata(src, path, name, species, frame) for src in combo]
    return fetch_func(gdatas, **extra)


class GkQuantityRegistry:
  """
  Registry of pre-named gyrokinetic quantities.

  Attributes:
    registry: Dictionary mapping quantity names to GkQuantity objects.
  """
  def __init__(self):
    self.registry = {}

  def register(self, gk_quantity: GkQuantity):
    """Register a new gyrokinetic quantity."""
    self.registry[gk_quantity.name] = gk_quantity

  def get(self, name: str) -> GkQuantity:
    """Get a registered gyrokinetic quantity by name."""
    return self.registry.get(name)

  def list(self) -> list:
    """Get a list of all registered gyrokinetic quantity names."""
    return sorted(list(self.registry.keys()))

  def has(self, name: str) -> bool:
    """Check if a quantity is registered."""
    return name in self.registry
