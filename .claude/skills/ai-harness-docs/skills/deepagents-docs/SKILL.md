---
name: deepagents-docs
description: Look up authoritative, up-to-date deepagents documentation — LangChain's Python/JavaScript framework for building deep agents (planning, subagents, virtual filesystem, long-horizon tasks). Covers quickstart, subagents (async/dynamic), backends & sandboxes, memory & skills, human-in-the-loop, MCP tools, models, streaming, frontend integration, the deepagents CLI (Deep Agents Code), and going to production. Use when the user asks how a deepagents feature works, what a parameter does, how to wire up subagents/backends/skills, when troubleshooting a deepagents error, or when you need to cite current official docs rather than rely on training-cutoff knowledge.
argument-hint: [topic or doc page]
allowed-tools: Bash(python3 *), Read, WebFetch
---

# deepagents Docs

Answers deepagents questions from the **official docs** (hosted on LangChain's docs site), not memory — deepagents ships frequently. A helper script builds a description-enriched index (cached per day) so you can triage precisely, then you fetch only the 1–3 pages you actually need as raw Markdown.

If the user passed an argument (`$ARGUMENTS`), treat it as the topic to look up. Otherwise infer the topic from the conversation.

## Why this skill needs its own index

deepagents docs live under `https://docs.langchain.com/oss/{python,javascript}/deepagents/`, but the site's `llms.txt` **does not list any deepagents pages**, and `llms-full.txt` is ~14 MB. So the builder discovers deepagents pages from the site **sitemap** and reads each page's frontmatter `description`. Do not try to use `llms.txt` for this skill.

## When to use this skill

Use it whenever the question is about the **deepagents** framework or anything in its docs scope:

- **Getting started**: overview, quickstart, comparison (vs plain agents / LangGraph)
- **Subagents**: subagents, async-subagents, dynamic-subagents
- **State & storage**: backends, sandboxes / remote-sandboxes, interpreters, memory, the virtual filesystem
- **Capabilities**: skills, tools, MCP tools, models, multimodal, RAG, deep-research, human-in-the-loop, permissions, context-engineering, streaming / event-streaming, fault-tolerance
- **Frontend**: `frontend/` pages (overview, sandbox, subagent-streaming, todo-list)
- **deepagents CLI / "Deep Agents Code"**: the `code/` pages (cli-reference, config-file, configuration, approval-modes, hooks, providers, credentials, plugins, remote-sandboxes, …)
- **Production**: going-to-production, profiles, customization

## Procedure

Search parameters: **page_size = 3** (pages per fetch batch), **max_items = 9** (hard cap across all batches).

### 1. Build / load the index, then read it

Run the builder — it prints the path of the cached index on its last stdout line. It reuses today's cache (near-instant) and only rebuilds when the date rolls over (first build fetches ~94 pages, ~5s):

```
Bash: python3 "${CLAUDE_SKILL_DIR}/scripts/build_index.py"
```

Then **Read that file**. It is a description-enriched list `- [Title](url): description  (short/path)`, split into `## python` and `## javascript` sections. Every entry has a real one-line description drawn from the page's frontmatter.

### 2. Pick the right page(s)

Match the user's question against the **description** first, then title + path. Sub-areas: `deepagents/…` core, `deepagents/code/…` = the CLI (Deep Agents Code), `deepagents/frontend/…` = UI integration. Then:

- Pick **up to page_size (3) pages per batch**, not more.
- **Match the user's language** — read from the `## python` section by default, `## javascript` if the question is clearly JS/TS. Don't fetch both variants of a page unless the user wants a comparison.
- One specific feature ("how do subagents work?") → one page.
- Nothing matches → say so. Do not guess a slug that isn't in the index.

### 3. Fetch the batch (append `.md`)

The index lists the HTML page URLs. To read content, **append `.md`** (Mintlify raw-Markdown endpoint — ~40× smaller and cleaner than the HTML):

```
WebFetch url=<page URL from index>.md
        prompt="<a question that captures what the user actually needs, not 'summarize this page'>"
```

Each `.md` opens with a short "Documentation Index" note from the site — ignore it and read the content below.

### 4. Evaluate, then loop or answer

- **Enough** → answer, grounded in the fetched content. Cite the doc page (title + URL) for non-obvious facts.
- **Not enough** (answer lives on an unread page, or a page linked to another deepagents page) → return to step 2, pick the next batch, fetch as `.md`.
- Keep looping up to **max_items (9) pages total**. If 9 still don't answer it, stop and tell the user what you read, what's missing, and ask before reading more.

## Rules

- **Always start from the built index (step 1).** deepagents pages get added and renamed; the sitemap-derived index is the source of truth.
- **Never invent a doc URL.** Only fetch pages that appear in the index. If it isn't there, it doesn't exist — say so.
- **Always fetch the `.md` variant**, not the HTML page.
- **Match the user's language** (python vs javascript). Default to python when unspecified.
- **Respect page_size / max_items.** Fetch 1–3, check, fetch more only if needed; ask before exceeding 9.
- **Ignore `llms.txt` / `llms-full.txt`.** The former omits deepagents; the latter is ~14 MB.
- **Pass through what the docs say.** Don't merge aggressively with prior knowledge.

If the builder ever fails (e.g. no network), fall back to discovering pages directly: `curl -s https://docs.langchain.com/sitemap.xml | grep -oE 'https://docs\.langchain\.com/oss/python/deepagents/[^<[:space:]]+' | sort -u`, then fetch chosen pages as `<url>.md`.
