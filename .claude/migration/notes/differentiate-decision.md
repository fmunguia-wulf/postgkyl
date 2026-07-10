# Differentiation strategy — investigation and decision (layer 03-dg)

## Question

Can `postgkyl.dg` differentiate modal DG data exactly, the way `dg/interp.py`
evaluates it exactly (basis math done by Gkeyll, NumPy only applies the
result)? Two candidate approaches were investigated per the layer instruction
file. Neither is clean enough to ship; **the decision is to defer** — no
`dg/deriv.py` is implemented in this layer.

## Approach A — expose the shim's own analytic gradient

`struct gkyl_basis` (`gkeyll/core/zero/gkyl_basis.h`) genuinely carries an
exact gradient evaluator as a function-pointer table, parallel to `eval`:

```c
/* gkeyll/core/zero/gkyl_basis.h */
double (*eval_grad_expand)(int dir, const double *z, const double *f);
```

and every basis, including hybrid/gkhybrid, ships a compiled kernel for it
(`gkeyll/core/zero/gkyl_cart_modal_hybrid_priv.h` lists
`eval_grad_expand_1x1v_hyb_p1` etc. right next to `eval_expand_*`). So Gkeyll
itself *can* do this exactly, for every basis, today.

But the compiled pg0 shim that `ffi/` talks to
(`gkeyll/core/zero/gkyl_pg0.h`, `ffi/csrc/_g0pymodule.c`) wraps only
`pg0_basis_eval` (the `eval` pointer) — there is no `pg0_basis_eval_grad` or
equivalent, confirmed by grepping both files for `grad`/`deriv` (no matches).
Wiring this up would mean adding a function to `gkyl_pg0.h`/`pg0.c` (in the
`gkeyll/` submodule) and to `ffi/csrc/_g0pymodule.c`, then rebuilding
`libg0core.so`/`_g0py.so` — all C sources and the submodule, explicitly out
of this layer's scope (rule 1). This is the right long-term path, but it is a
shim-extension task for whichever layer owns `ffi/`'s C surface, not this one.

## Approach B — exact Gauss-point polynomial fit (no shim change)

The instruction file's fallback: evaluate `eval_matrix` at Gauss-Legendre
points (already exact and already exposed, via `dg.rep.modal_to_quad`), then
differentiate the resulting per-cell polynomial exactly via a Lagrange
spectral-differentiation matrix (a basis-agnostic, purely numerical
construction — no Gkeyll struct knowledge, unlike the retired
`computeDerivativeMatrices`). Lagrange differentiation through `k` points is
*exact* for any polynomial of degree `≤ k-1` in that one variable, regardless
of which subspace of higher-dimensional polynomials it came from — so this
only works if `num_quad = poly_order + 1` points per axis actually bounds the
basis's degree in every direction.

That bound holds for **serendipity** and **tensor** (every term has degree
`≤ poly_order` in each variable, by construction) — but it does **not** hold
for **hybrid**/**gkhybrid**. Both are fixed at `poly_order = 1`, yet their
compiled kernels carry an extra quadratic term in the parallel-velocity
direction to represent the pressure moment exactly. Directly from the
generated kernel source:

```c
// gkeyll/core/ker/basis/basis_eval_hyb.c — eval_1x1v_hyb_p1 (z1 = vpar)
b[4] =  1.6770509831248424e+00*(z1*z1)-5.5901699437494745e-01;
b[5] =  2.9047375096555625e+00*(z1*z1)*z0 + ...;

// gkeyll/core/ker/basis/basis_eval_gkhyb.c — eval_1x2v_gkhyb_p1 (z1 = vpar, z2 = mu)
b[8]  =  1.1858541225631423e+00*(z1*z1) - 3.9528470752104744e-01;
b[9]  = -6.8465319688145765e-01*z0 + 2.0539595906443728e+00*z0*(z1*z1);
```

`z1` (vpar) appears squared while `poly_order = 1`, so the true per-axis
degree in that one direction is 2, not 1; the `mu` direction (`z2` in
gkhybrid) stays degree 1. `num_quad = poly_order + 1 = 2` uniform Gauss
points — the only tensor rule `ffi.basis.gauss_quad`/`modal_to_quad_matrix`
can build — would under-sample the vpar direction and silently produce a
*wrong* (non-exact) derivative there; only `mu` and the configuration axes
would be exact. Making this exact would require an anisotropic quadrature
(3 points in vpar, 2 elsewhere) plus a hand-derived, basis-and-axis-specific
"true polynomial degree per direction" table for hybrid/gkhybrid across every
supported `(cdim, vdim)` — new basis-specific knowledge on top of the
existing `_HYBRID_CDIM_VDIM`/`_MAX_POLY_ORDER` tables in `ffi/basis.py`, that
could not be verified against every kernel with the confidence a numerical
correctness claim needs in the time available for this layer. Serendipity
and tensor alone would be exact, but hybrid/gkhybrid are exactly the bases
the gyrokinetic/PKPM datasets this tool targets use (e.g.
`tests/test_data/rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl` is gkhybrid) — shipping
a "derivative" that is silently wrong for the tool's primary basis family is
worse than not shipping one.

## Decision

**Defer.** `dg/deriv.py` is not implemented. Layer 07 should add
differentiation as a **post-`interp()` verb using `np.gradient`** on the
plain NumPy field values (the "numpy" backend, where every basis subtlety
above is already resolved by `.interp()`'s own basis-exact evaluation and the
derivative only needs to be accurate on a uniform mesh, not exact on a modal
polynomial). This is a numerical, not exact, derivative, and should be
documented as such in that verb's docstring. If a future layer wants an exact
modal derivative, the correct route is Approach A: extend `gkyl_pg0.h`/`pg0.c`
and `ffi/csrc/_g0pymodule.c` with `pg0_basis_eval_grad` (wrapping
`eval_grad_expand`, which Gkeyll already compiles for every basis) and add a
thin `dg/deriv.py` orchestrator over it, mirroring `dg/interp.py`'s pattern
exactly.
