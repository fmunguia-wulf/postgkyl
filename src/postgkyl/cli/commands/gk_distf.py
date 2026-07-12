"""``gk_distf`` — build a gyrokinetic distribution function from saved Jf data."""

from __future__ import annotations

import click

import postgkyl as pg

from .._options import tag_option


@click.command("gk_distf")
@click.option("--name", "-n", required=True, help="Simulation name prefix.")
@click.option("--species", "-s", required=True, help="Species name.")
@click.option("--frame", "-f", required=True,
    help="Frame number, comma-separated list, or 'start:stop[:step]' range.")
@click.option("--suffix", default="",
    help="Use '<name>-<species>_<suffix>_<frame>.gkyl' as the input.")
@click.option("--interp", "-i", type=int, default=None,
    help="Interpolation points per cell (default: poly_order + 1).")
@click.option("--c2p-vel", "-v", "c2p_vel", is_flag=True, default=False,
    help="Convert velocity-space coordinates via the mapc2p_vel mapping.")
@click.option("--mc2nu", "-m", is_flag=True, default=False,
    help="Convert to field-aligned coordinates via the mc2nu mapping.")
@click.option("--mapc2p", "-p", is_flag=True, default=False,
    help="Convert position-space coordinates via the mapc2p mapping.")
@click.option("--block", "-b", type=int, default=None,
    help="Use block-specific files with a '_b<idx>' prefix.")
@click.option("--jf-file", default=None, help="Jf filename override.")
@click.option("--jacobvel-file", default=None, help="jacobvel filename override.")
@click.option("--jacobtot-inv-file", default=None, help="jacobtot_inv filename override.")
@click.option("--mc2nu-file", default=None, help="mc2nu filename override.")
@click.option("--mapc2p-file", default=None, help="mapc2p filename override.")
@click.option("--mapc2p-vel-file", default=None, help="mapc2p_vel filename override.")
@tag_option(default="f")
@click.pass_context
def command(ctx, name, species, frame, suffix, interp, c2p_vel, mc2nu, mapc2p,
    block, jf_file, jacobvel_file, jacobtot_inv_file, mc2nu_file, mapc2p_file,
    mapc2p_vel_file, tag) -> None:
  """Gyrokinetics: build f from a saved Jf-times-Jacobian(s) file."""
  frames = pg.diagnostics.gyrokinetics.resolve_frames(frame, name=name,
      species=species, suffix=suffix, block_idx=block)
  for f in frames:
    out = pg.load_gk_distf(name, species, f, tag=tag, suffix=suffix,
        use_c2p_vel=c2p_vel, use_mc2nu=mc2nu, use_mapc2p=mapc2p,
        block_idx=block, interp=interp, jf_file=jf_file,
        jacobvel_file=jacobvel_file, jacobtot_inv_file=jacobtot_inv_file,
        mc2nu_file=mc2nu_file, mapc2p_file=mapc2p_file,
        mapc2p_vel_file=mapc2p_vel_file)
    ctx.obj.datasets.append(out)
  # end
