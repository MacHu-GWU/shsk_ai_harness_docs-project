#!/usr/bin/env python3
r"""Build a description-enriched, cached docs index for **deepagents** (LangChain).

This script is self-contained (stdlib only, no third-party deps) and belongs to
the `deepagents-docs` skill. A sibling copy exists for `strands-agents-docs`;
the two are intentionally kept separate and self-contained even though they
share small utility helpers.

WHAT IT PRODUCES
----------------
A single Markdown index file, split into `## python` and `## javascript`
sections, one line per doc page:

    - [Title](https://docs.langchain.com/oss/python/deepagents/...): one-line description  (short/path)

The skill reads this file to decide which 1-3 pages to fetch for a question.

WHY THIS HARNESS NEEDS ITS OWN DISCOVERY
----------------------------------------
deepagents docs live on LangChain's Mintlify site under
`/oss/{python,javascript}/deepagents/`, but the site's `llms.txt` DOES NOT list
any deepagents pages, and `llms-full.txt` is ~14 MB. So we discover pages from
the site sitemap and read each page's frontmatter `description` directly.

HUMAN-VERIFIABLE SOURCE URLS (open these in a browser to sanity-check)
----------------------------------------------------------------------
  * Sitemap listing every page on the site (~1500 <loc> entries):
        https://docs.langchain.com/sitemap.xml
  * A single page as raw Markdown (append `.md` to any doc URL — Mintlify
    convention; ~40x smaller and cleaner than the HTML):
        https://docs.langchain.com/oss/python/deepagents/subagents.md
  * The same page as HTML (what humans read):
        https://docs.langchain.com/oss/python/deepagents/subagents

FETCH & PARSE LOGIC
-------------------
  1. Fetch sitemap.xml and keep only <loc> URLs containing
     `/oss/python/deepagents/` and `/oss/javascript/deepagents/`.
  2. For each page URL, fetch `<url>.md` (concurrently, small thread pool).
     Mintlify prepends a short "> ## Documentation Index" note block — strip it,
     then read:
         # <H1>              -> the page Title
         > <blockquote>      -> the frontmatter `description` (human-written)
     If a page has no blockquote, fall back to its first prose paragraph.
  3. Emit one line per page, grouped by language.

OUTPUT STRUCTURE (example, abbreviated)
---------------------------------------
    # deepagents (LangChain) — docs index (built 2026-07-23)
    # Format: - [Title](url): description   |   fetch a page as raw markdown (append .md)

    ## python
    - [Subagents](https://docs.langchain.com/oss/python/deepagents/subagents): Learn how to use subagents to delegate work and keep context clean  (oss/python/deepagents/subagents)
    - [Command reference](https://docs.langchain.com/oss/python/deepagents/code/cli-reference): Deep Agents Code command-line flags and management subcommands  (oss/python/deepagents/code/cli-reference)

    ## javascript
    - [Subagents](https://docs.langchain.com/oss/javascript/deepagents/subagents): ...

WHERE THE INDEX IS STORED (fixed location under $HOME)
------------------------------------------------------
    ~/.cache/ai-harness-docs/deepagents/<YYYY-MM-DD>/index.md

CACHING & EXPIRATION
--------------------
  * The cache key is TODAY's local date (YYYY-MM-DD).
  * If today's index.md already exists and is non-empty, it is reused with NO
    network access (fast path — a few milliseconds).
  * Otherwise the ENTIRE `deepagents/` cache dir is deleted first (dropping all
    stale dates), then today's index is built fresh (~5s cold: ~94 small page
    fetches via a thread pool). So at most one date folder is ever kept, and the
    index self-refreshes once per calendar day.
  * `--force` rebuilds today's index even if it already exists.

CLI USAGE (for humans to test)
------------------------------
    # Build (or reuse today's cache); prints the index path on the LAST stdout line:
    python3 build_index.py

    # Force a fresh rebuild ignoring the cache (watch the per-language counts on stderr):
    python3 build_index.py --force

    # Build, then eyeball the result:
    less "$(python3 build_index.py | tail -1)"

    # Every page should have a description:
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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# --- deepagents-specific configuration ----------------------------------- #
HARNESS = "deepagents"
TITLE = "deepagents (LangChain)"
BASE = "https://docs.langchain.com"
SITEMAP_URL = f"{BASE}/sitemap.xml"
LANGS = ["python", "javascript"]
PATH_TEMPLATE = "/oss/{lang}/deepagents/"

CACHE_ROOT = Path.home() / ".cache" / "ai-harness-docs"
UA = {"User-Agent": "ai-harness-docs-index-builder/1.0 (deepagents)"}
HTTP_TIMEOUT = 45
MAX_WORKERS = 8


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
def page_meta(page_url: str) -> tuple[str, str]:
    """Return (title, description) from a Mintlify page's `.md` rendering."""
    md = fetch(page_url + ".md")
    # strip the leading "> ## Documentation Index ..." note block Mintlify prepends
    body = re.sub(r"\A(?:>.*\n|\s*\n)+", "", md)
    m_title = re.search(r"(?m)^#\s+(.+)$", body)
    title = m_title.group(1).strip() if m_title else page_url.rsplit("/", 1)[-1]
    after = body[m_title.end():] if m_title else body
    m_desc = re.search(r"(?m)^>\s*(.+)$", after)
    if m_desc:
        return title, clean(m_desc.group(1))
    # fall back to first prose paragraph
    for para in re.split(r"\n\s*\n", after.strip()):
        p = para.strip()
        if p and not p.startswith(("#", ">", "```", "|", "-", "*")):
            return title, clean(p)
    return title, ""


def safe_meta(page_url: str) -> tuple[str, str]:
    try:
        return page_meta(page_url)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully per page
        log(f"    ! {page_url}: {exc}")
        return (page_url.rsplit("/", 1)[-1], "")


def build_index_text() -> str:
    sitemap = fetch(SITEMAP_URL)
    all_locs = re.findall(r"<loc>\s*(https?://[^<\s]+?)\s*</loc>", sitemap)

    sections: list[str] = []
    for lang in LANGS:
        frag = PATH_TEMPLATE.format(lang=lang)
        urls = sorted({u for u in all_locs if frag in u})
        if not urls:
            continue
        log(f"  {lang}: {len(urls)} pages")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            metas = dict(zip(urls, pool.map(safe_meta, urls)))
        sections.append(f"## {lang}")
        for url in urls:
            title, desc = metas[url]
            short = url.replace(BASE, "").lstrip("/")
            sections.append(
                f"- [{title}]({url}): {desc}  ({short})" if desc
                else f"- [{title}]({url})  ({short})"
            )
        sections.append("")
    return "\n".join(sections) + "\n"


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
        f"# Format: - [Title](url): description   |   fetch a page as raw markdown (append .md)\n\n"
    )
    target.write_text(header + body, encoding="utf-8")
    log(f"wrote {target} ({body.count(chr(10))} lines)")
    return target


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the deepagents docs index.")
    ap.add_argument("--force", action="store_true", help="rebuild even if today's cache exists")
    args = ap.parse_args()
    print(build(args.force))  # last stdout line = index path (the skill reads this)


if __name__ == "__main__":
    main()
