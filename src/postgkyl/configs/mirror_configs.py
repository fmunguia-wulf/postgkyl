"""Configuration for Lorentzian magnetic mirror gyrokinetic simulations."""
import numpy as np

# Physical constants (CODATA 2018)
_EPS0 = 8.8541878128e-12  # [F/m]
_MU0  = 4 * np.pi * 1e-7  # [T·m/A]
_EV   = 1.602176634e-19   # [C]
_MP   = 1.67262192369e-27 # [kg]
_ME   = 9.1093837015e-31  # [kg]


class LorentzianMirrorConfig:
    """
    Configuration for a Lorentzian magnetic mirror gyrokinetic simulation.

    Encapsulates all physics, geometry, and grid parameters for a 1x2v or
    2x2v gyrokinetic simulation in a magnetic mirror machine whose on-axis
    field follows a Lorentzian profile:

        B(z) ≈ B_p * [ 1 + (z/mcB)^2 * gamma ]

    The class computes all derived quantities (Ti0, thermal speeds, velocity
    grid bounds, collision frequency) from the primary inputs, matching the
    logic in the Gkeyll C input file.

    Parameters
    ----------
    Te0_eV : float
        Electron temperature in eV.  Default: 940 eV.
    n0 : float
        Reference density in m^-3.  Default: 3e19.
    B_p : float
        Magnetic field magnitude at the midplane (z=0) in T.  Default: 0.53.
    beta : float
        Plasma beta.  Ion temperature is derived from pressure balance:
        ``Ti0 = Te0 * (B_p^2 * beta / (2*mu0*n0*Te0) - 1)``.  Default: 0.4.
    mi_amu : float
        Ion mass in atomic mass units.  Default: 2.014 (deuterium).
    Z_min, Z_max : float
        Axial domain boundaries in m.  Default: ±2.5 m.
    Z_m : float
        Axial position of the mirror throat (maximum B) in m.  Default: 0.98.
    mcB : float
        Lorentzian width parameter (controls how quickly B rises off-axis).
        Default: 3.691260.
    gamma : float
        Lorentzian asymmetry parameter.  Default: 0.226381.
    RatZeq0 : float
        Radius of the reference field line at z=0 in m (required for the 2x
        flux-surface coordinate).  Default: 0.10.
    dimensionality : str
        ``'1x2v'`` (field-line only, default) or ``'2x2v'`` (adds a radial
        coordinate for the flux-surface label ψ).
    Nz : int
        Number of axial cells.  Default: 400.
    Nvpar : int
        Number of ion parallel-velocity cells.  Default: 64.
    Nmu : int
        Number of ion magnetic-moment cells.  Default: 32.
    Npsi : int
        Number of radial (ψ) cells — only used when ``dimensionality='2x2v'``.
        Default: 4.
    Nvpar_elc : int
        Number of electron parallel-velocity cells.  Default: 8.
    Nmu_elc : int
        Number of electron magnetic-moment cells.  Default: 8.
    nuFrac : float
        Collision frequency multiplier (1.0 = physical).  Default: 1.0.
    poly_order : int
        DG polynomial order.  Default: 1.

    Examples
    --------
    >>> from postgkyl.configs import LorentzianMirrorConfig
    >>> cfg = LorentzianMirrorConfig(Te0_eV=940, n0=3e19, B_p=0.53, beta=0.4)
    >>> print(f"Ti0  = {cfg.Ti0 / cfg.eV:.1f} eV")
    >>> print(f"vti  = {cfg.vti:.3e} m/s")
    >>> print(f"R_m  = {cfg.mirror_ratio:.2f}")
    >>> print(f"theta_lc = {np.degrees(cfg.loss_cone_angle):.1f} deg")
    >>> sim = cfg.make_simulation()
    """

    def __init__(
        self,
        Te0_eV: float = 940.0,
        n0: float = 3e19,
        B_p: float = 0.53,
        beta: float = 0.4,
        mi_amu: float = 2.014,
        Z_min: float = -2.5,
        Z_max: float = 2.5,
        Z_m: float = 0.98,
        mcB: float = 3.691260,
        gamma: float = 0.226381,
        RatZeq0: float = 0.10,
        dimensionality: str = '1x2v',
        Nz: int = 400,
        Nvpar: int = 64,
        Nmu: int = 32,
        Npsi: int = 4,
        Nvpar_elc: int = 8,
        Nmu_elc: int = 8,
        nuFrac: float = 1.0,
        poly_order: int = 1,
    ):
        if dimensionality not in ('1x2v', '2x2v'):
            raise ValueError(
                f"dimensionality must be '1x2v' or '2x2v', got '{dimensionality}'"
            )

        self.dimensionality = dimensionality

        # Physical constants
        self.eps0    = _EPS0
        self.mu0     = _MU0
        self.eV      = _EV
        self.mp      = _MP
        self.me      = _ME
        self.mi      = mi_amu * _MP
        self.mi_amu  = mi_amu
        self.qi      =  _EV
        self.qe      = -_EV

        # Primary plasma parameters
        self.Te0  = Te0_eV * _EV
        self.n0   = n0
        self.B_p  = B_p
        self.beta = beta

        # Ion temperature from pressure balance (matches C create_ctx logic):
        #   tau = B_p^2 * beta / (2*mu0*n0*Te0) - 1
        #   Ti0 = tau * Te0
        self.tau  = (B_p**2 * beta) / (2.0 * _MU0 * n0 * self.Te0) - 1.0
        self.Ti0  = self.tau * self.Te0

        # Ion-ion collision frequency
        self.nuFrac = nuFrac
        logL = 6.6 - 0.5 * np.log(n0 / 1e20) + 1.5 * np.log(self.Ti0 / _EV)
        self.logLambdaIon = logL
        self.nuIon = (nuFrac * logL * _EV**4 * n0 /
                      (12.0 * np.pi**1.5 * _EPS0**2 *
                       np.sqrt(self.mi) * self.Ti0**1.5))

        # Thermal speeds
        self.vti = np.sqrt(self.Ti0 / self.mi)
        self.vte = np.sqrt(self.Te0 / self.me)

        # Velocity grid bounds (match C input file)
        self.vpar_max_ion = 16.0 * self.vti
        self.mu_max_ion   = self.mi * (3.0 * self.vti)**2 / (2.0 * B_p)
        self.vpar_max_elc = 4.0  * self.vte
        self.mu_max_elc   = self.me * (4.0 * self.vte)**2 / (2.0 * B_p)

        # Geometry
        self.RatZeq0 = RatZeq0
        self.Z_min   = Z_min
        self.Z_max   = Z_max
        self.Z_m     = Z_m
        self.mcB     = mcB
        self.gamma   = gamma

        # Grid resolution
        self.Nz        = Nz
        self.Npsi      = Npsi
        self.Nvpar     = Nvpar
        self.Nmu       = Nmu
        self.Nvpar_elc = Nvpar_elc
        self.Nmu_elc   = Nmu_elc
        self.poly_order = poly_order

    # ------------------------------------------------------------------
    # Derived geometry quantities
    # ------------------------------------------------------------------

    def B_of_z(self, z: float | np.ndarray) -> float | np.ndarray:
        """
        Analytic on-axis field magnitude at axial position *z*.

        Uses the Lorentzian profile from the simulation geometry:
        ``B(z) = B_p * (1 + (z / mcB)^2 * gamma_factor)``

        where ``gamma_factor`` is derived from ``mcB`` and ``gamma``.
        """
        return self.B_p * (1.0 + (z / self.mcB)**2 * self.gamma / self.mcB)

    @property
    def B_mirror(self) -> float:
        """Peak (mirror) magnetic field at the throat z = Z_m [T]."""
        return self.B_of_z(self.Z_m)

    @property
    def mirror_ratio(self) -> float:
        """Mirror ratio R_m = B_mirror / B_midplane."""
        return self.B_mirror / self.B_p

    @property
    def loss_cone_angle(self) -> float:
        """
        Loss-cone half-angle in radians.

        Defined by ``sin²(θ_lc) = 1 / R_m``, so particles with
        pitch angle inside the cone are lost to the sheath.
        """
        return np.arcsin(1.0 / np.sqrt(self.mirror_ratio))

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    def make_species(self):
        """
        Return ``(ion, elc)`` Species objects configured for this mirror.

        Gyromotion parameters (ω_c, ρ_L, μ₀) are computed at the midplane
        field *B_p*.

        Returns
        -------
        ion : postgkyl.sim.Species
        elc : postgkyl.sim.Species
        """
        from postgkyl.sim import Species

        ion = Species('ion', m=self.mi, q=self.qi,
                      T0=self.Ti0, n0=self.n0, Bref=self.B_p)
        elc = Species('elc', m=self.me, q=self.qe,
                      T0=self.Te0, n0=self.n0, Bref=self.B_p)
        return ion, elc

    def make_simulation(self):
        """
        Construct a :class:`~postgkyl.sim.Simulation` pre-populated with
        species and physical parameters.

        The returned ``Simulation`` has both ion and electron species added,
        gyromotion parameters set at the midplane field *B_p*, and a default
        :class:`~postgkyl.sim.Normalization` attached.  Because mirror
        geometry differs from tokamak geometry, the normalization defaults
        (which are tokamak-oriented) should be overridden via
        ``sim.normalization.change(...)`` before loading frames.

        Returns
        -------
        sim : postgkyl.sim.Simulation

        Examples
        --------
        >>> cfg = LorentzianMirrorConfig()
        >>> sim = cfg.make_simulation()
        >>> sim.set_data_param(simdir='/path/to/run/', fileprefix='run')
        """
        from postgkyl.sim import Simulation

        sim = Simulation(dimensionality=self.dimensionality,
                         porder=self.poly_order)
        sim.set_phys_param(eps0=self.eps0, eV=self.eV,
                           mp=self.mp, me=self.me)

        # Patch GeomParam with mirror-appropriate values so that add_species
        # (which calls set_gyromotion and Normalization) works without error.
        # GeomParam defaults are tokamak-oriented; we only override the fields
        # that are actually consumed by the Normalization initialiser.
        sim.geom_param.B0    = self.B_p        # midplane B [T]
        sim.geom_param.a_mid = self.Z_max      # use half-domain length as length scale
        sim.geom_param.x_LCFS = 0.0

        ion, elc = self.make_species()
        # ion must be added first: Normalization.__init__ accesses species['ion']
        sim.add_species(ion)
        sim.add_species(elc)

        return sim

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def info(self):
        """Print a human-readable summary of all configuration parameters."""
        eV = self.eV
        print(f"LorentzianMirrorConfig  [{self.dimensionality}]")
        print(f"  Plasma")
        print(f"    n0    = {self.n0:.2e} m⁻³")
        print(f"    Te0   = {self.Te0/eV:.1f} eV")
        print(f"    Ti0   = {self.Ti0/eV:.1f} eV   (tau = {self.tau:.3f})")
        print(f"    B_p   = {self.B_p:.3f} T    (beta = {self.beta:.2f})")
        print(f"  Species  (ion: {self.mi_amu:.3f} amu)")
        print(f"    vti   = {self.vti:.3e} m/s")
        print(f"    vte   = {self.vte:.3e} m/s")
        print(f"    nuIon = {self.nuIon:.3e} s⁻¹")
        print(f"  Geometry")
        print(f"    Z ∈ [{self.Z_min}, {self.Z_max}] m,  Z_m = {self.Z_m} m")
        print(f"    Mirror ratio  ≈ {self.mirror_ratio:.3f}")
        print(f"    Loss-cone     ≈ {np.degrees(self.loss_cone_angle):.1f}°")
        print(f"  Grid")
        if self.dimensionality == '2x2v':
            print(f"    Npsi={self.Npsi}  Nz={self.Nz}  "
                  f"Nvpar={self.Nvpar}  Nmu={self.Nmu}")
        else:
            print(f"    Nz={self.Nz}  Nvpar={self.Nvpar}  Nmu={self.Nmu}")
        print(f"    Electrons: Nvpar={self.Nvpar_elc}  Nmu={self.Nmu_elc}")
        print(f"  Velocity bounds")
        print(f"    ion: vpar_max={self.vpar_max_ion:.3e} m/s  "
              f"mu_max={self.mu_max_ion:.3e} J/T")
        print(f"    elc: vpar_max={self.vpar_max_elc:.3e} m/s  "
              f"mu_max={self.mu_max_elc:.3e} J/T")
