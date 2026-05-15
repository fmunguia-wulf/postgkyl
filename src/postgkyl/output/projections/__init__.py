try:
    from postgkyl.output.projections.poloidalprojection import PoloidalProjection
    from postgkyl.output.projections.fluxsurfprojection import FluxSurfProjection
    from postgkyl.output.projections.torusprojection import TorusProjection
    __all__ = ['PoloidalProjection', 'FluxSurfProjection', 'TorusProjection']
except ImportError:
    __all__ = []
