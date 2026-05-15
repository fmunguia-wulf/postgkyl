"""
# Postgkyl

Postgkyl is both Python library and command-line tool designed to provide unified access
to Gkeyll data together with a broad variety of analytical and visualization tools.
"""

__version__ = "1.7.5"

# import submodules
from postgkyl import data
from postgkyl import utils
from postgkyl import tools
from postgkyl import output

# import selected classes to the root
from postgkyl.data.gdata import GData
from postgkyl.data.dg import GInterpNodal
from postgkyl.data.dg import GInterpModal

# High-level simulation API
try:
    from postgkyl.sim import (
        Simulation, Frame, Species, TimeSerie,
        NumParam, PhysParam, GeomParam,
        GBsource, Source, IntegratedMoment, Normalization,
    )
    from postgkyl import sim
    from postgkyl import interfaces
    from postgkyl import configs
except Exception:
    pass

# Projections (optional — requires pyvista/matplotlib)
try:
    from postgkyl.output.projections import (
        PoloidalProjection, FluxSurfProjection, TorusProjection,
    )
except Exception:
    pass

# link the command line executable to the system
from postgkyl import pgkyl

