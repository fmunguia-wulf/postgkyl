"""Animation: ``FuncAnimation`` / saved frames / ffmpeg movie compile.

Isolated from ``matplotlib.py`` because it owns the one external-process
dependency in this layer -- ``ffmpeg`` -- reached through Matplotlib's
``FFMpegWriter``/``Animation.save``. Every entry point that needs it probes
``shutil.which("ffmpeg")`` up front and raises a clear ``RuntimeError``
instead of failing deep inside the writer.
"""

from __future__ import annotations

import os.path
import shutil
from typing import TYPE_CHECKING

import numpy as np

from postgkyl.core.state import GDataState

from . import matplotlib as backend

if TYPE_CHECKING:
  from matplotlib.figure import Figure
# end

# Formats written through ffmpeg; PIL handles the rest (gif/webp/apng).
_VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv")


def _require_ffmpeg() -> None:
  if shutil.which("ffmpeg") is None:
    raise RuntimeError(
        "animate: saving to a video container requires ffmpeg on PATH "
        "(not found). Install ffmpeg, or pass 'saveframes' to write PNGs "
        "without compiling a movie.")
  # end


def _normalize_frames(data) -> list[list["GDataState"]]:
  """One frame per item; a bare dataset becomes a single-dataset frame."""
  frames = [[item] if isinstance(item, GDataState) else list(item)
            for item in data]
  if not frames:
    raise ValueError("animate: no datasets to animate.")
  # end
  return frames


def _frame_value_range(frames: list[list["GDataState"]],
    cutoff: float | None = None) -> tuple[float, float]:
  """Value range spanning every dataset in every frame.

  With ``cutoff`` (a central fraction in ``(0, 1]``), the range is clipped
  to that percentile band of the per-dataset extrema instead of the true
  min/max -- useful when a few outlier frames would otherwise wash out the
  color/y-axis scale for the rest of the animation.
  """
  extrema = np.array([
      bound for frame in frames for dat in frame
      for bound in (np.nanmin(dat.values), np.nanmax(dat.values))
  ])
  vmin, vmax = float(extrema.min()), float(extrema.max())
  if cutoff:
    boundary = 100.0 * (1.0 - cutoff) / 2.0
    vmax = float(np.percentile(extrema, 100.0 - boundary))
    vmin = float(np.percentile(extrema, boundary))
  # end
  return vmin, vmax


def _render_frame(index: int, frames: list[list["GDataState"]],
    fig: "Figure", plot_kwargs: dict):
  """Redraw ``frames[index]`` onto ``fig`` (the ``FuncAnimation``/frame-dump
  callback). The per-frame title is taken from the first dataset's ``ctx``
  (frame index and time) unless ``plot_kwargs['notitle']`` is set."""
  kwargs = dict(plot_kwargs)
  notitle = kwargs.pop("notitle", False)
  frame = frames[index]
  if not notitle:
    dat0 = frame[0]
    parts = []
    if dat0.ctx.get("frame") is not None:
      parts.append(f"frame: {dat0.ctx['frame']:d}")
    # end
    if dat0.ctx.get("time") is not None:
      parts.append(f"time: {dat0.ctx['time']:.4e}")
    # end
    kwargs["title"] = " ".join(parts)
  # end
  return backend.plot(*frame, fig=fig, show=False, **kwargs)


def _save_frames(frames: list[list["GDataState"]], prefix: str, *,
    dpi: int | None = None, figsize=None, plot_kwargs: dict | None = None
    ) -> list[str]:
  """Write ``<prefix>_<i>.png`` for every frame, reusing one figure."""
  import matplotlib.pyplot as plt

  fig = plt.figure(figsize=figsize)
  paths = []
  try:
    for i in range(len(frames)):
      _render_frame(i, frames, fig, plot_kwargs or {})
      path = f"{prefix}_{i}.png"
      fig.savefig(path, dpi=dpi)
      paths.append(path)
    # end
  finally:
    plt.close(fig)
  # end
  return paths


def _compile_movie(frame_files: list[str], output_file: str, *,
    fps: int | None = None, duration: float = 100.0) -> None:
  """Compile PNG frames into an animation: PIL for gif/webp/apng, the
  Matplotlib ffmpeg writer for video containers. ``duration`` is the
  per-frame time in milliseconds, used when ``fps`` is not given."""
  from PIL import Image

  ext = os.path.splitext(output_file)[1].lower()
  if ext in (".gif", ".webp", ".apng"):
    images = [Image.open(f) for f in frame_files]
    images[0].save(output_file, save_all=True, append_images=images[1:],
        duration=duration, loop=0, optimize=False)
    return
  # end
  if ext in _VIDEO_EXTS:
    _require_ffmpeg()
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter

    movie_fps = fps if fps else 1.0e3 / duration
    writer = FFMpegWriter(fps=movie_fps)
    first = Image.open(frame_files[0])
    dpi = 100
    fig = plt.figure(figsize=(first.width / dpi, first.height / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    try:
      with writer.saving(fig, output_file, dpi):
        for frame_file in frame_files:
          ax.clear()
          ax.axis("off")
          ax.imshow(Image.open(frame_file))
          writer.grab_frame()
        # end
      # end
    finally:
      plt.close(fig)
    # end
    return
  # end
  raise ValueError(f"animate: unsupported output format {ext!r}")


def animate(data, *, interval: int = 100, fixed_range: bool = True,
    cutoffglobalrange: float | None = None, notitle: bool = False,
    show: bool = False, save: bool = False, saveas: str | None = None,
    fps: int | None = None, dpi: int | None = None,
    saveframes: str | None = None, figsize=None, **plot_kwargs):
  """Animate a sequence of frames, one frame per dataset (or dataset group).

  Args:
    data: a flat iterable of datasets (each becomes a single-dataset frame),
      or an iterable of frames where each frame is itself a list of
      datasets drawn together (overlaid, as in ``matplotlib.plot``).
    interval: live-animation delay between frames, in milliseconds.
    fixed_range: hold a constant value/color scale across every frame
      (``ymin``/``ymax``/``zmin``/``zmax``, unless already given in
      ``plot_kwargs``).
    cutoffglobalrange: clip the fixed range to this central percentile band
      (see ``_frame_value_range``); ``None`` uses the true min/max.
    notitle: suppress the per-frame frame/time title.
    show: open a live window (the ``FuncAnimation`` path only).
    save: write to ``saveas`` (or ``anim.mp4``) after building the frames.
    saveas: output path; its extension selects the writer (``.gif``/
      ``.webp``/``.apng`` via PIL, ``.mp4``/``.mov``/``.avi``/``.mkv`` via
      ffmpeg).
    fps: frames per second for the saved movie; defaults from ``interval``.
    dpi: resolution for saved frames/movies.
    saveframes: when given, write ``<saveframes>_<i>.png`` for every frame
      instead of building a live ``FuncAnimation``.
    figsize: figure size in inches, forwarded to ``matplotlib.plot``.
    **plot_kwargs: forwarded to ``matplotlib.plot`` for every frame.

  Returns:
    The list of written frame paths when ``saveframes`` is set; otherwise
    the ``FuncAnimation`` (keep a reference -- Matplotlib does not keep the
    live animation alive for you).

  Raises:
    ValueError: no datasets to animate, or an unsupported ``saveas``
      extension.
    RuntimeError: saving to a video container without ffmpeg on ``PATH``.
  """
  frames = _normalize_frames(data)
  plot_kwargs["notitle"] = notitle

  if fixed_range:
    vmin, vmax = _frame_value_range(frames, cutoffglobalrange)
    # Applied as both the 1-D y-limits (ymin/ymax) and the 2-D color range
    # (zmin/zmax) -- whichever the frame's dimensionality actually uses.
    plot_kwargs.setdefault("ymin", vmin)
    plot_kwargs.setdefault("ymax", vmax)
    plot_kwargs.setdefault("zmin", vmin)
    plot_kwargs.setdefault("zmax", vmax)
  # end

  num_frames = len(frames)
  duration = 1.0e3 / fps if fps else float(interval)
  out_file = saveas or "anim.mp4"

  if saveframes:
    frame_files = _save_frames(frames, saveframes, dpi=dpi, figsize=figsize,
        plot_kwargs=plot_kwargs)
    if save or saveas:
      _compile_movie(frame_files, out_file, fps=fps, duration=duration)
    # end
    return frame_files
  # end

  import matplotlib.pyplot as plt
  from matplotlib.animation import FuncAnimation

  fig = plt.figure(figsize=figsize)
  anim = FuncAnimation(fig, _render_frame, num_frames,
      fargs=(frames, fig, plot_kwargs), interval=interval, blit=False)
  if save or saveas:
    _require_ffmpeg()
    anim.save(out_file, writer="ffmpeg", fps=fps, dpi=dpi)
  # end
  if show:
    plt.show()
  # end
  return anim
