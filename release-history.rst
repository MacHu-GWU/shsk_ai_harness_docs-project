.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.1.1 (2026-07-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- First release of the ``ai-harness-docs`` Agent Skills plugin, which gives AI coding agents grounded, always-current documentation lookup for AI agent harness frameworks.
- Add the ``strands-agents-docs`` skill for looking up `Strands Agents <https://strandsagents.com/>`_ documentation.
- Add the ``deepagents-docs`` skill for looking up `deepagents <https://docs.langchain.com/oss/python/deepagents/overview>`_ documentation, discovered from the site sitemap since the framework is not listed in the published ``llms.txt``.
- Each skill builds a **description-enriched docs index**: a real one-line description is extracted for every page (from the page's front-matter or first paragraph), so the agent can triage precisely instead of guessing from titles alone.
- The index is **cached locally** under ``~/.cache/ai-harness-docs/<framework>/<YYYY-MM-DD>/index.md`` and rebuilt at most once per calendar day, with stale dates purged automatically, so lookups are fast and offline-friendly after the first build.
