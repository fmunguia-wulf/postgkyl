"""Reusable Typer option aliases shared across pgkyl commands.

The coordinate cuts (``--z0``..``--z5``/``--component``), the ADIOS variable
name and the ``--compgrid`` flag are accepted both as *global* pre-options on
the root group (``pgkyl --z0 0 ...``) and as *local* options on the ``load``
command. Declaring each one once here keeps the flag spellings and help text in
lockstep between the two sites instead of being copy-pasted (and drifting).

These are plain :data:`typing.Annotated` aliases; use them directly as parameter
annotations, e.g. ``z0: opt.Z0 = None``.

Note: ``select`` deliberately does *not* reuse the cut aliases. Its cuts are a
different option (``--comp`` rather than ``--component``, they accept floats, and
they mean "indices to select" rather than "partial file load"), so they keep
their own declarations in ``select.py``.
"""

from __future__ import annotations

from typing import Annotated

import typer


# Coordinate cuts. Declared explicitly (rather than generated in a loop) so that
# static type checkers recognize each as a type alias usable as an annotation.
Z0 = Annotated[str | None, typer.Option("--z0", help="Partial file load: 0th coord (either int or slice).")]
Z1 = Annotated[str | None, typer.Option("--z1", help="Partial file load: 1st coord (either int or slice).")]
Z2 = Annotated[str | None, typer.Option("--z2", help="Partial file load: 2nd coord (either int or slice).")]
Z3 = Annotated[str | None, typer.Option("--z3", help="Partial file load: 3rd coord (either int or slice).")]
Z4 = Annotated[str | None, typer.Option("--z4", help="Partial file load: 4th coord (either int or slice).")]
Z5 = Annotated[str | None, typer.Option("--z5", help="Partial file load: 5th coord (either int or slice).")]

Component = Annotated[
    str | None,
    typer.Option("--component", "-c", help="Partial file load: comps (either int or slice)."),
]
VarName = Annotated[
    list[str] | None,
    typer.Option("--varname", "-d", help="Specify the Adios variable name (default is 'CartGridField')."),
]
CompGrid = Annotated[
    bool,
    typer.Option("--compgrid", help="Disregard the mapped grid information"),
]

# The transform-command triad. Shared by the many verbs that select active
# datasets (``--use``), tag their result (``--tag``) and label it (``--label``).
# The default value stays per-command (e.g. ``tag: opt.Tag = "rel_change"``);
# these aliases only fix the flags, type and help text.
Use = Annotated[
    str | None,
    typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags)."),
]
Tag = Annotated[
    str | None,
    typer.Option("--tag", "-t", help="Optional tag for the resulting array."),
]
Label = Annotated[
    str | None,
    typer.Option("--label", "-l", help="Custom label for the result."),
]
