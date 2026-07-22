#!/usr/bin/env python3
"""Insert `# end` marker comments after every indented block.

For every compound statement that opens an indented suite (for/while/if/
elif/else/try/except/finally/with/def/class/match/case/...), insert a
`# end` comment line -- indented to match the *opening* statement, not the
body -- immediately after the last line of that suite. Idempotent: a block
that already has the right `# end` line is left untouched.

Usage:
    python scripts/insert_end_comments.py [paths...] [--write]

By default this is a dry run that only reports what it would change; pass
--write to actually modify files on disk.
"""
import argparse
import io
import sys
import tokenize
from pathlib import Path

DEFAULT_EXCLUDE_DIRS = {
    ".git", ".pytest_cache", ".vscode", "__pycache__", ".venv", "venv",
    "build", "dist", "node_modules",
    "gkeyll",  # vendored Gkeyll checkout, not ours to reformat
    "main",    # untracked mirror checkout, not the working tree
}


def find_python_files(paths):
    for base in paths:
        base = Path(base)
        if base.is_file():
            if base.suffix == ".py":
                yield base
            continue
        for p in sorted(base.rglob("*.py")):
            if any(part in DEFAULT_EXCLUDE_DIRS or part.endswith(".egg-info")
                   for part in p.parts):
                continue
            yield p


def _is_blank_or_comment(line):
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def plan_insertions(source):
    """Return (lines, insertions) where `insertions` maps a 0-indexed
    source line number to the list of '# end' lines to splice in right
    after it (innermost block first)."""
    newline = "\r\n" if "\r\n" in source else "\n"
    lines = source.splitlines(keepends=True)

    indent_stack = []       # header indentation strings, one per open block
    last_stmt_indent = ""   # indent of the most recently *completed* statement
    pending_indent = ""     # indent of the statement currently being scanned
    at_line_start = True
    insertions = {}

    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.INDENT:
            indent_stack.append(last_stmt_indent)
        elif tok.type == tokenize.DEDENT:
            if not indent_stack:
                continue
            header_indent = indent_stack.pop()
            boundary_line = tok.start[0]  # 1-indexed line the dedent lands on
            expected = header_indent + "# end"

            # The whole run of blank/comment-only lines between the block's
            # last real statement and the next real statement -- scan back
            # over it (so a trailing '# end' is recognized regardless of
            # blank lines around it, and so unrelated comments -- e.g. a
            # section header for the next block -- never get straddled).
            gap_indices = []
            idx = boundary_line - 2
            while idx >= 0 and _is_blank_or_comment(lines[idx]):
                gap_indices.append(idx)
                idx -= 1
            content_idx = idx  # last real code line of the block (0-indexed)

            already_present = any(
                lines[i].rstrip("\r\n") == expected for i in gap_indices
            ) or any(
                e.rstrip("\r\n") == expected
                for e in insertions.get(content_idx, [])
            )
            if not already_present:
                insertions.setdefault(content_idx, []).append(expected + newline)
        elif tok.type == tokenize.NEWLINE:
            last_stmt_indent = pending_indent
            at_line_start = True
        elif tok.type not in (tokenize.NL, tokenize.COMMENT,
                               tokenize.ENCODING, tokenize.ENDMARKER):
            if at_line_start:
                pending_indent = tok.line[:tok.start[1]]
                at_line_start = False

    return lines, insertions


def apply_insertions(lines, insertions):
    out = []
    for idx, line in enumerate(lines):
        out.append(line)
        out.extend(insertions.get(idx, []))
    return out


def process_file(path, write):
    source = path.read_text()
    try:
        lines, insertions = plan_insertions(source)
    except (tokenize.TokenizeError, SyntaxError, IndentationError) as exc:
        print(f"SKIP {path}: {exc}", file=sys.stderr)
        return 0

    n = sum(len(v) for v in insertions.values())
    if n == 0:
        return 0

    new_source = "".join(apply_insertions(lines, insertions))
    if write:
        path.write_text(new_source)
    print(f"{'WROTE' if write else 'WOULD EDIT'} {path}: +{n} '# end' line(s)")
    return n


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", default=["."],
                         help="files or directories to scan (default: repo root)")
    parser.add_argument("--write", action="store_true",
                         help="modify files in place (default: dry run)")
    args = parser.parse_args()

    files_changed = 0
    lines_added = 0
    for path in find_python_files(args.paths):
        n = process_file(path, args.write)
        if n:
            files_changed += 1
            lines_added += n

    verb = "Modified" if args.write else "Would modify"
    print(f"\n{verb} {files_changed} file(s), {lines_added} '# end' line(s) total.")
    if not args.write and files_changed:
        print("Re-run with --write to apply.")


if __name__ == "__main__":
    main()
