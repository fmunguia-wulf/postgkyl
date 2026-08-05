"""``gk_energy_balance`` -- plot a gyrokinetic simulation's energy balance."""

from __future__ import annotations

import click

import postgkyl as pg

from .._options import show_option


@click.command("gk_energy_balance")
@click.option("--name", "-n", required=True, help="Simulation name (also the file prefix).")
@click.option("--species", "-s", required=True, help="Comma-separated list of species names.")
@click.option("--path", "-p", default="./", help="Path to simulation data.")
@click.option("--relative-error", "-r", is_flag=True, default=False,
    help="Plot the relative error only.")
@click.option("--multib", "-m", default="-10",
    help="'-10' for a single block (default); '-1' to discover every block; "
         "otherwise a comma-separated list or 'start:stop[:step]' slice of block indices.")
@click.option("--field-dot-file", default=None, help="Field energy rate-of-change file override.")
@click.option("--apar-dot-file", default=None, help="Apar energy rate-of-change file override.")
@click.option("--fdot-file", default=None,
    help="Integrated Hamiltonian moments of df/dt file override.")
@click.option("--source-file", default=None, help="Integrated moments of the source(s) override.")
@click.option("--bflux-xlower-file", default=None, help="Boundary flux through lower x override.")
@click.option("--bflux-ylower-file", default=None, help="Boundary flux through lower y override.")
@click.option("--bflux-zlower-file", default=None, help="Boundary flux through lower z override.")
@click.option("--bflux-xupper-file", default=None, help="Boundary flux through upper x override.")
@click.option("--bflux-yupper-file", default=None, help="Boundary flux through upper y override.")
@click.option("--bflux-zupper-file", default=None, help="Boundary flux through upper z override.")
@click.option("--f-file", default=None, help="Integrated moments of f file override.")
@click.option("--field-file", default=None, help="Field energy file override.")
@click.option("--apar-file", default=None, help="Apar energy file override.")
@click.option("--dt-file", default=None, help="Time-step file override.")
@click.option("--logy", is_flag=True, default=False, help="Logarithmic scale for the y axis.")
@click.option("--absy", is_flag=True, default=False, help="Take the absolute value of every trace.")
@click.option("--xlabel", default="Time (s)", help="Label for the x axis.")
@click.option("--ylabel", default=None, help="Label for the y axis.")
@click.option("--title", default=None, help="Figure title.")
@click.option("--indent-left", type=float, default=0.0,
    help="Shift the left boundary of the axes (figure-fraction units).")
@click.option("--add-width", type=float, default=0.0,
    help="Widen the axes (figure-fraction units).")
@click.option("--saveas", default=None, help="Path to save the figure to.")
@show_option()
@click.pass_context
def command(ctx, name, species, path, relative_error, multib, field_dot_file, apar_dot_file,
    fdot_file, source_file, bflux_xlower_file, bflux_ylower_file, bflux_zlower_file,
    bflux_xupper_file, bflux_yupper_file, bflux_zupper_file, f_file, field_file, apar_file,
    dt_file, logy, absy, xlabel, ylabel, title, indent_left, add_width, saveas, show) -> None:
  """Gyrokinetics: plot the energy balance of a simulation.

  \b
  Requires, per species (named <name>-<species>): an
  '_fdot_integrated_moms.gkyl' file, and (only if the run had sources or
  non-periodic boundaries) '_source_integrated_moms.gkyl' and
  '_bflux_<direction><side>_integrated_HamiltonianMoments.gkyl' files. A
  '<name>-field_energy_dot.gkyl' file is required; '<name>-apar_energy_dot.
  gkyl' is read if present (electromagnetic simulations). If
  --relative-error is passed, the corresponding non-'_dot'
  ('_integrated_moms.gkyl'/'field_energy.gkyl'/'apar_energy.gkyl') and
  '<name>-dt.gkyl' files are also required.

  NOTE: this command cannot be combined with other pgkyl commands.
  """
  bflux_files = {
      "xlower": bflux_xlower_file, "ylower": bflux_ylower_file, "zlower": bflux_zlower_file,
      "xupper": bflux_xupper_file, "yupper": bflux_yupper_file, "zupper": bflux_zupper_file,
  }
  pg.diagnostics.gyrokinetics.gk_energy_balance(
      name, species.split(","), path=path, relative_error=relative_error, multib=multib,
      field_dot_file=field_dot_file, apar_dot_file=apar_dot_file, fdot_file=fdot_file,
      source_file=source_file, bflux_files=bflux_files, f_file=f_file, field_file=field_file,
      apar_file=apar_file, dt_file=dt_file, logy=logy, absy=absy, xlabel=xlabel, ylabel=ylabel,
      title=title, indent_left=indent_left, add_width=add_width, show=show, saveas=saveas)
# end
