---
name: strands-agents-docs
description: Look up authoritative, up-to-date Strands Agents documentation — the Python/TypeScript SDK for building production AI agents. Covers the agent loop, tools, MCP, multi-agent (swarm/graph/agents-as-tools), sessions & state, hooks, streaming, model providers, sandboxes, plugins, deployment, and the full Python/TypeScript API reference. Use when the user asks how a Strands feature works, what a class/parameter does, how to wire up tools/MCP/multi-agent/sessions, when troubleshooting a Strands error, or when you need to cite current official docs rather than rely on training-cutoff knowledge.
argument-hint: [topic or doc title]
allowed-tools: Bash(python3 *), Read, WebFetch
---

# Strands Agents Docs

Answers Strands questions from the **official docs**, not memory — the SDK ships frequently and the docs track it. A helper script builds a description-enriched index (cached per day) so you can triage precisely, then you fetch only the 1–3 pages you actually need.

If the user passed an argument (`$ARGUMENTS`), treat it as the topic to look up. Otherwise infer the topic from the conversation.

## When to use this skill

Use it whenever the question is about the Strands Agents SDK or anything in its docs scope:

- **User guide**: agent loop, prompts, state, sessions & snapshots, conversation/context management, hooks, retry strategies, interrupts, interventions (cedar-authorization, steering, human-in-the-loop)
- **Tools**: adding tools, custom tools, MCP tools, executors, community/vended tools
- **Multi-agent**: agent-to-agent, agents-as-tools, swarm, graph, workflow patterns
- **Streaming & realtime**: async iterators, callback handlers, bidirectional/voice streaming
- **Model providers, sandboxes, plugins** (skills, steering, context-offloader/injector, goal-loop), **structured output**, deployment
- **API reference**: `strands.*` Python modules and the TypeScript API (classes, functions, parameters)
- **Examples**, **quickstart** (Python / TypeScript), and **changelog / release history**

## Procedure

Search parameters: **page_size = 3** (pages per fetch batch), **max_items = 9** (hard cap across all batches).

### 1. Build / load the index, then read it

Run the builder — it prints the path of the cached index on its last stdout line. It reuses today's cache (near-instant) and only rebuilds when the date rolls over:

```
Bash: python3 "${CLAUDE_SKILL_DIR}/scripts/build_index.py"
```

Then **Read that file**. It is a description-enriched outline: `- [Title](url): description`, grouped under the site's section headings (`Get Started`, `Build`, `Concepts`, `Multi-agent`, `API Reference`, `Examples`, `Changelog`, …). URLs end in `index.md` — they are raw Markdown.

> Note: narrative/user-guide entries carry a real one-line description. **API-reference entries are title-only by design** (their module/class name, e.g. `strands.agent.agent`, is the signal) — match those by name + path.

### 2. Pick the right page(s)

Match the user's question against the **description** first, then title + URL path + section heading. Then:

- Pick **up to page_size (3) pages per batch**, not more. The index is for triage, not bulk loading.
- One specific feature ("how do hooks work?") → one page.
- Cross-concept question ("swarm vs agents-as-tools?") → one page each.
- API question about a specific `strands.*` class/param → go straight to that module's `docs/api/python/<module>/index.md` entry.
- Nothing matches → say so. Do not guess a URL that isn't in the index.

### 3. Fetch the batch

For each chosen URL:

```
WebFetch url=<URL from index>
        prompt="<a question that captures what the user actually needs, not 'summarize this page'>"
```

### 4. Evaluate, then loop or answer

- **Enough** → answer, grounded in the fetched content. Cite the doc page (title + URL) for non-obvious facts.
- **Not enough** (answer lives on an unread page, or a page linked to another `index.md`) → return to step 2, pick the next batch. In-page links use `/docs/.../index.md` paths — resolve them against `https://strandsagents.com`.
- Keep looping up to **max_items (9) pages total**. If 9 still don't answer it, stop and tell the user what you read, what's missing, and ask before reading more. Don't blow past the cap or pad with guesses.

## Rules

- **Always start from the built index (step 1).** It is the source of truth for which pages exist; doc paths get renamed and modules move.
- **Never invent a doc URL.** If a page isn't in the index, say so instead of fabricating a slug.
- **Respect page_size / max_items.** Fetch 1–3, check, fetch more only if needed; ask the user before exceeding 9.
- **Stay in scope.** `strandsagents.com/docs/*` plus the site's `/changelog`.
- **Pass through what the docs say.** Don't merge aggressively with prior knowledge — the user wants current authoritative behavior.

If the builder ever fails (e.g. no network), fall back to WebFetching `https://strandsagents.com/llms.txt` directly as the index (title + URL only, no descriptions).
