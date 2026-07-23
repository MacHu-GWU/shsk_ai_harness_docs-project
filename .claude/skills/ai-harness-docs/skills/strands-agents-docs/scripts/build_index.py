#!/usr/bin/env python3
r"""Build a description-enriched, cached docs index for the **Strands Agents** SDK.

This script is self-contained (stdlib only, no third-party deps) and belongs to
the `strands-agents-docs` skill. A sibling copy exists for `deepagents-docs`;
the two are intentionally kept separate and self-contained even though they
share small utility helpers.

WHAT IT PRODUCES
----------------
A single Markdown index file, one line per doc page:

    - [Title](https://strandsagents.com/docs/.../index.md): one-line description

grouped under the site's own section headings (Get Started, Build, Concepts,
Multi-agent, API Reference, Examples, Changelog, ...). The skill reads this file
to decide which 1-3 pages to fetch for a given question.

HUMAN-VERIFIABLE SOURCE URLS (open these in a browser to sanity-check)
----------------------------------------------------------------------
  * Index of titles + order + section tree (Astro/Starlight auto-generated):
        https://strandsagents.com/llms.txt
  * Full corpus, every page body concatenated and delimited by `Source: <url>`:
        https://strandsagents.com/llms-full.txt
  * A single page as raw Markdown (what the skill ultimately WebFetches):
        https://strandsagents.com/docs/user-guide/concepts/multi-agent/swarm/index.md

FETCH & PARSE LOGIC
-------------------
  1. Fetch llms.txt  -> gives every `- [Title](url)` line + the section headings
     and ordering. This is the skeleton of the index (titles + structure + URLs).
  2. Fetch llms-full.txt -> split it on `^Source: <url>$` lines. Each page's body
     appears *before* its Source line, so the text chunk preceding each Source
     URL is that page's body. Take its first real prose paragraph as the
     one-line description (skipping headings, tables, code fences, list items).
  3. Join: for each llms.txt entry, attach the description found for its URL.

     NOTE: llms-full.txt contains the narrative/user-guide docs but NOT the
     auto-generated API reference. So `strands.*` (Python) and the TypeScript
     API entries come out title-only *by design* — their module/class name is
     already the search signal. Everything conceptual gets a real description.

OUTPUT STRUCTURE (example, abbreviated)
---------------------------------------
    # Strands Agents — docs index (built 2026-07-23)
    # Format: - [Title](url): description   |   fetch a page as raw markdown

    ## Docs
    - Get Started
      - [overview](https://strandsagents.com/docs/user-guide/quickstart/overview/index.md): The Strands Agents SDK empowers developers to quickly build...
    - Concepts
      - [hooks](https://strandsagents.com/docs/user-guide/concepts/agents/hooks/index.md): Hooks are a composable extensibility mechanism...
      - [strands.agent.agent](https://strandsagents.com/docs/api/python/strands.agent.agent/index.md)   <- API entry, title only

WHERE THE INDEX IS STORED (fixed location under $HOME)
------------------------------------------------------
    ~/.cache/ai-harness-docs/strands-agents/<YYYY-MM-DD>/index.md

CACHING & EXPIRATION
--------------------
  * The cache key is TODAY's local date (YYYY-MM-DD).
  * If today's index.md already exists and is non-empty, it is reused with NO
    network access (fast path — a few milliseconds).
  * Otherwise the ENTIRE `strands-agents/` cache dir is deleted first (dropping
    all stale dates), then today's index is built fresh. So at most one date
    folder is ever kept, and the index self-refreshes once per calendar day.
  * `--force` rebuilds today's index even if it already exists.

CLI USAGE (for humans to test)
------------------------------
    # Build (or reuse today's cache); prints the index path on the LAST stdout line:
    python3 build_index.py

    # Force a fresh rebuild ignoring the cache:
    python3 build_index.py --force

    # Build, then eyeball the result:
    less "$(python3 build_index.py | tail -1)"

    # Verify descriptions were extracted:
    grep -c '): ' "$(python3 build_index.py | tail -1)"

Progress/diagnostics go to stderr; only the final index path goes to stdout.
"""

from __future__ import annotations

import argparse
import datetime
import re
import shutil
import sys
import urllib.request
from pathlib import Path

# --- Strands-specific configuration -------------------------------------- #
HARNESS = "strands-agents"
TITLE = "Strands Agents"
LLMS_TXT_URL = "https://strandsagents.com/llms.txt"
LLMS_FULL_URL = "https://strandsagents.com/llms-full.txt"

CACHE_ROOT = Path.home() / ".cache" / "ai-harness-docs"
UA = {"User-Agent": "ai-harness-docs-index-builder/1.0 (strands-agents)"}
HTTP_TIMEOUT = 45


# --- small self-contained utils ------------------------------------------ #
def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return resp.read().decode("utf-8", "replace")


def clean(text: str, limit: int = 200) -> str:
    """Collapse whitespace and trim a paragraph down to a one-line description."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


def today() -> str:
    return datetime.date.today().isoformat()


# --- build logic ---------------------------------------------------------- #
def descriptions_from_llms_full(llms_full: str) -> dict[str, str]:
    """Map page URL -> first prose paragraph, parsed from llms-full.txt.

    Pages are concatenated; each body is followed by a `Source: <url>` line,
    so the text *before* each Source line is that page's body.
    """
    parts = re.split(r"(?m)^Source:\s*(\S+)\s*$", llms_full)
    # parts = [body0, url1, body1, url2, body2, ...]; body(i-1) precedes url(i)
    bodies = parts[0::2]
    urls = parts[1::2]
    out: dict[str, str] = {}
    for url, body in zip(urls, bodies):
        desc = ""
        for para in re.split(r"\n\s*\n", body.strip()):
            p = para.strip()
            if not p or p.startswith(("#", "---", "|", "```", ".main", "-   ", "- ", "*")):
                continue
            desc = clean(p)
            break
        out[url] = desc
    return out


def build_index_text() -> str:
    llms = fetch(LLMS_TXT_URL)
    desc_by_url = descriptions_from_llms_full(fetch(LLMS_FULL_URL))

    link_re = re.compile(r"^(\s*)-\s*\[([^\]]+)\]\((https?://\S+?)\)\s*(?::\s*(.*))?$")
    lines: list[str] = []
    for raw in llms.splitlines():
        m = link_re.match(raw)
        if not m:
            # keep section headings / structural lines verbatim; drop blockquotes
            stripped = raw.strip()
            if stripped and not stripped.startswith(">"):
                lines.append(raw.rstrip())
            continue
        indent, title, url, inline_desc = m.groups()
        desc = (inline_desc or "").strip() or desc_by_url.get(url, "")
        lines.append(f"{indent}- [{title}]({url}): {desc}" if desc else f"{indent}- [{title}]({url})")
    return "\n".join(lines) + "\n"


def build(force: bool) -> Path:
    day = today()
    target = CACHE_ROOT / HARNESS / day / "index.md"

    if target.exists() and target.stat().st_size > 0 and not force:
        log(f"cache hit: {target}")
        return target

    log(f"building index for '{HARNESS}' ...")
    body = build_index_text()

    hdir = CACHE_ROOT / HARNESS
    if hdir.exists():
        shutil.rmtree(hdir)  # drop all stale dates
    target.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# {TITLE} — docs index (built {day})\n"
        f"# Format: - [Title](url): description   |   fetch a page as raw markdown\n\n"
    )
    target.write_text(header + body, encoding="utf-8")
    log(f"wrote {target} ({body.count(chr(10))} lines)")
    return target


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the Strands Agents docs index.")
    ap.add_argument("--force", action="store_true", help="rebuild even if today's cache exists")
    args = ap.parse_args()
    print(build(args.force))  # last stdout line = index path (the skill reads this)


if __name__ == "__main__":
    main()
