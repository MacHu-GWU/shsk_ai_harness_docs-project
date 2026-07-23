#!/usr/bin/env python3
"""Generate a fillable claude-code-messages.md template with numbered prompt slots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PLACEHOLDER = "PROMPT_HERE"


def _render_template(n: int, zfill: int) -> str:
    """Render n numbered '## NNNN' sections, each a blank code fence to fill in later."""
    lines = ["# Claude Code Messages", ""]
    for index in range(1, n + 1):
        lines.append(f"## {str(index).zfill(zfill)}")
        lines.append("")
        lines.append("```md")
        lines.append(PLACEHOLDER)
        lines.append("```")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _main(
    n: int,
    path: Path,
    overwrite: bool = False,
    zfill: int = 4,
) -> int:
    """Write a claude-code-messages.md template with n numbered, fillable prompt slots.

    Returns an exit code: 0 on success, 1 on failure.
    """
    if path.exists() and not overwrite:
        print(
            f"ERROR: {path} already exists, pass --overwrite to replace it",
            file=sys.stderr,
        )
        return 1

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_template(n=n, zfill=zfill), encoding="utf-8")
    print(f"Wrote {n} template entries to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gen_claude_code_message_md",
        description="Generate a fillable claude-code-messages.md template with numbered prompt slots.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=99,
        help="number of numbered template slots to generate",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).resolve().parent / "claude-code-messages.md",
        help="output path for the generated template",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite the output file if it already exists",
    )
    parser.add_argument(
        "--zfill",
        type=int,
        default=4,
        help="digit width to zero-pad each entry's heading number to",
    )
    args = parser.parse_args(argv)
    return _main(n=args.n, path=args.path, overwrite=args.overwrite, zfill=args.zfill)


if __name__ == "__main__":
    sys.exit(main())
