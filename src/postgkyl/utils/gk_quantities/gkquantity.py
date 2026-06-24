class GkQuantity:
  """Class for a gyrokinetic quantity.

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

  def __init__(self, name, source, fetch_func, label, is_time_dep, is_species_dep, is_vector):
    self.name = name
    self.source = source
    self.fetch_func = fetch_func
    self.label = label 
    self.is_time_dep = is_time_dep
    self.is_species_dep = is_species_dep
    self.is_vector = is_vector

  def get_label(self, species=None, direction=None):
    """Get the label for the quantity, replacing %s with species name or direction."""
    if self.is_vector and direction is not None:
      return self.label % str(direction)
    elif self.is_species_dep and species is not None:
      return self.label % species[0]
    else:
      return self.label

class GkQuantityRegistry:
  """Registry of pre-named gyrokinetic quantities.

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
  