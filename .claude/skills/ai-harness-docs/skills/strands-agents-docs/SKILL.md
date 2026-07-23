---
name: strands-agents-docs
description: Look up authoritative, up-to-date Strands Agents documentation — the Python/TypeScript SDK for building production AI agents. Covers the agent loop, tools, MCP, multi-agent (swarm/graph/agents-as-tools), sessions & state, hooks, streaming, model providers, sandboxes, plugins, deployment, and the full Python API reference. Use when the user asks how a Strands feature works, what a class/parameter does, how to wire up tools/MCP/multi-agent/sessions, when troubleshooting a Strands error, or when you need to cite current official docs rather than rely on training-cutoff knowledge.
argument-hint: [topic or doc title]
allowed-tools: WebFetch
---

# Strands Agents Docs

Lazy-loads the official Strands Agents documentation by reading the index at `https://strandsagents.com/llms.txt`, picking the most relevant page(s), and fetching them on demand. Always prefer this skill over recalling docs from memory — the SDK ships frequently and the docs track it.

If the user passed an argument (`$ARGUMENTS`), treat it as the topic to look up. Otherwise infer the topic from the conversation.

## When to use this skill

Use it whenever the question is about the Strands Agents SDK or anything in its docs scope:

- **User guide**: agent loop, prompts, state, sessions & snapshots, conversation/context management, hooks, retry strategies, interrupts, interventions (cedar-authorization, steering, human-in-the-loop)
- **Tools**: adding tools, custom tools, MCP tools, executors, community/vended tools
- **Multi-agent**: agent-to-agent, agents-as-tools, swarm, graph, workflow patterns
- **Streaming & realtime**: async iterators, callback handlers, bidirectional/voice streaming
- **Model providers, sandboxes, plugins** (skills, steering, context-offloader/injector, goal-loop), **structured output**, deployment
- **Python API reference**: modules under `strands.*` — classes, functions, parameters (e.g. `strands.agent.agent`, `strands.tools`, conversation managers)
- **Examples**: runnable sample implementations (Python & TypeScript)
- **Quickstart** (Python / TypeScript) and **changelog / release history**

## Procedure

### 1. Read the index

```
WebFetch url=https://strandsagents.com/llms.txt
        prompt="Return the raw markdown outline unmodified. I need every `- [Title](URL)` line and its section heading, verbatim, so I can pick pages to fetch."
```

The index is a large (~800-line) hierarchical outline, not a flat list. Entries look like `- [Title](https://strandsagents.com/docs/<path>/index.md)`, grouped under section headings (`Get Started`, `Build`, `Concepts`, `Multi-agent`, `API Reference`, `Examples`, `Changelog`, …). Most lines carry **no description** — the **section heading + title + URL path** are your triage signal. URLs end in `index.md` — the targets are raw Markdown, not HTML.

Because the index is long, WebFetch may compress it. If the outline comes back partial or a section you need is missing, re-fetch with a prompt scoped to that section, e.g. `"Return only the lines under the 'Multi-agent' / 'Tools' section, verbatim."`

### 2. Pick the right page(s)

Match the user's question against the **title and the URL path** (the path segments are meaningful, e.g. `.../concepts/multi-agent/swarm/index.md`), plus the **section heading** it sits under. Then:

- Pick **1–3 pages per batch**, not more. The index is for triage, not bulk loading.
- One specific feature ("how do hooks work?") → one page.
- Cross-concept question ("how does swarm compare to agents-as-tools?") → fetch each relevant page.
- **API reference** questions (a specific `strands.*` class/parameter) → go straight to that module's `docs/api/python/<module>/index.md` page.
- Nothing in the index obviously matches → say so. Do not guess a URL.

### 3. Fetch the batch

For each chosen URL:

```
WebFetch url=<URL from index>
        prompt="<a question that captures what the user actually needs, not 'summarize this page'>"
```

### 4. Evaluate, then loop or answer

After each batch, judge whether the fetched pages actually answer the user's question:

- **Enough** → answer, grounded in the fetched content. Cite the doc page (title + URL) when stating non-obvious facts so the user can verify.
- **Not enough** (the answer lives on a page you haven't read, or a fetched page linked to another `index.md`) → go back to step 2, pick the next 1–3 pages, and fetch again. In-page links use `/docs/.../index.md` paths — resolve them against `https://strandsagents.com`.
- Keep looping until you can answer, up to a **default cap of 9 pages total** across all batches.
- **Still not enough at 9 pages** → stop. Tell the user honestly what you've read, what's still missing, and ask whether they want you to keep reading more pages. Don't silently blow past the cap or pad the answer with guesses.

## Rules

- **Never invent a doc URL.** If a page isn't in the index, it does not exist — say so instead of fabricating a slug.
- **Don't skip step 1**, even if you think you remember the right URL. Doc paths get renamed and modules move; the index is the source of truth.
- **Loop in small batches, cap at 9 pages.** Fetch 1–3, check if that's enough, fetch more only if it isn't. If 9 pages still don't answer it, ask the user before reading more.
- **Stay in scope.** This skill covers `strandsagents.com/docs/*` (plus the site's `/changelog`). The three richest areas are `docs/user-guide/*`, `docs/api/python/*`, and `docs/examples/*`.
- **Pass through what the docs say.** Don't merge aggressively with prior knowledge — the user wants current authoritative behavior, not a synthesis.
- **Need many pages at once?** `https://strandsagents.com/llms-full.txt` inlines the full corpus in one file. It is very large (multi-MB) — only reach for it when a broad question genuinely needs it, and prefer targeted `index.md` fetches otherwise.
