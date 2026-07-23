---
name: deepagents-docs
description: Look up authoritative, up-to-date deepagents documentation — LangChain's Python/JavaScript framework for building deep agents (planning, subagents, virtual filesystem, long-horizon tasks). Covers quickstart, subagents (async/dynamic), backends & sandboxes, memory & skills, human-in-the-loop, MCP tools, models, streaming, frontend integration, the deepagents CLI (`code/`), and going to production. Use when the user asks how a deepagents feature works, what a parameter does, how to wire up subagents/backends/skills, when troubleshooting a deepagents error, or when you need to cite current official docs rather than rely on training-cutoff knowledge.
argument-hint: [topic or doc page]
allowed-tools: WebFetch, Bash(curl *), Bash(grep *), Bash(sort *)
---

# deepagents Docs

Lazy-loads the official deepagents documentation (hosted on LangChain's docs site) by building a live index from the site sitemap, picking the most relevant page(s), and fetching each as raw Markdown on demand. Always prefer this skill over recalling docs from memory — deepagents ships frequently and the docs track it.

If the user passed an argument (`$ARGUMENTS`), treat it as the topic to look up. Otherwise infer the topic from the conversation.

## Why this skill is different from a normal `llms.txt` lookup

deepagents docs live under `https://docs.langchain.com/oss/{python,javascript}/deepagents/`, but:

- **The site's `llms.txt` does NOT list any deepagents pages** — do not use it for this skill.
- **`llms-full.txt` exists but is ~14 MB** — far too large to load; do not fetch it.
- **Do NOT ask WebFetch to filter the sitemap.** The sitemap has ~1500 URLs; WebFetch runs it through a small model that truncates and will wrongly report "no deepagents URLs." The index MUST be built with a deterministic `curl | grep` (step 1).
- **Every page is fetchable as raw Markdown** by appending `.md` to its URL (Mintlify convention), e.g. `.../deepagents/subagents.md`. Fetch the `.md`, never the HTML.

## When to use this skill

Use it whenever the question is about the **deepagents** framework or anything in its docs scope:

- **Getting started**: overview, quickstart, comparison (vs plain agents / LangGraph)
- **Subagents**: subagents, async-subagents, dynamic-subagents
- **State & storage**: backends, sandboxes / remote-sandboxes, interpreters, memory, the virtual filesystem
- **Capabilities**: skills, tools, MCP tools, models, multimodal, RAG, deep-research, human-in-the-loop, permissions, context-engineering, streaming / event-streaming, fault-tolerance
- **Frontend**: `frontend/` pages (overview, sandbox, subagent-streaming, todo-list)
- **deepagents CLI / "code"**: the `code/` pages (cli-reference, config-file, configuration, approval-modes, hooks, providers, credentials, plugins, remote-sandboxes, …)
- **Production**: going-to-production, profiles, customization

## Procedure

### 1. Build the index (deterministic — do not use WebFetch here)

Pick the language the user is working in. Default to **python** unless the question is clearly about JavaScript/TypeScript (then use `javascript`, or fetch both if unclear):

```bash
curl -s https://docs.langchain.com/sitemap.xml \
  | grep -oE 'https://docs\.langchain\.com/oss/python/deepagents/[^<[:space:]]+' \
  | sort -u
```

Swap `python` for `javascript` (or run both) as needed. This returns the complete, current list of deepagents page URLs (~45–50 per language). There are **no descriptions** — the URL **path segments are the triage signal** (e.g. `.../deepagents/code/cli-reference`, `.../deepagents/frontend/todo-list`).

### 2. Pick the right page(s)

Match the user's question against the path segments and the sub-areas (`deepagents/…` core, `deepagents/code/…` = the CLI, `deepagents/frontend/…` = UI integration). Then:

- Pick **1–3 pages per batch**, not more. The index is for triage, not bulk loading.
- One specific feature ("how do subagents work?") → one page (`.../deepagents/subagents`).
- Cross-concept question ("how do backends relate to sandboxes?") → fetch each relevant page.
- Keep to the user's language (python vs javascript). Don't fetch both variants of the same page unless the user asks to compare.
- Nothing in the index obviously matches → say so. Do not guess a slug.

### 3. Fetch the batch (append `.md`)

For each chosen page URL, append `.md` and WebFetch it:

```
WebFetch url=https://docs.langchain.com/oss/python/deepagents/<page>.md
        prompt="<a question that captures what the user actually needs, not 'summarize this page'>"
```

The `.md` endpoint returns clean Markdown (the HTML page is ~40× larger and noisy). Each page opens with a short "Documentation Index" note from the site — ignore it and read the content below.

### 4. Evaluate, then loop or answer

After each batch, judge whether the fetched pages actually answer the user's question:

- **Enough** → answer, grounded in the fetched content. Cite the doc page (title + URL) when stating non-obvious facts so the user can verify.
- **Not enough** (the answer lives on a page you haven't read, or a fetched page linked to another deepagents page) → go back to step 2, pick the next 1–3 pages from the index, and fetch again as `.md`.
- Keep looping until you can answer, up to a **default cap of 9 pages total** across all batches.
- **Still not enough at 9 pages** → stop. Tell the user honestly what you've read, what's still missing, and ask whether they want you to keep reading more pages. Don't silently blow past the cap or pad the answer with guesses.

## Rules

- **Build the index with `curl | grep` (step 1), never by asking WebFetch to filter the sitemap.** WebFetch will truncate the 1500-URL sitemap and falsely report no deepagents pages.
- **Never invent a doc URL.** Only fetch pages that appear in the step-1 index. If a page isn't there, it does not exist — say so instead of fabricating a slug.
- **Don't skip step 1**, even if you think you remember the right URL. deepagents pages get added and renamed; the sitemap is the source of truth.
- **Always fetch the `.md` variant**, not the HTML page.
- **Match the user's language.** Python pages live under `oss/python/deepagents/`, JavaScript under `oss/javascript/deepagents/`. Default to python when unspecified.
- **Loop in small batches, cap at 9 pages.** If 9 pages still don't answer it, ask before reading more.
- **Ignore `llms.txt` / `llms-full.txt` for this skill.** The former omits deepagents; the latter is ~14 MB.
- **Pass through what the docs say.** Don't merge aggressively with prior knowledge — the user wants current authoritative behavior, not a synthesis.
