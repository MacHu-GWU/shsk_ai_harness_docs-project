
.. image:: https://readthedocs.org/projects/shsk-ai-harness-docs/badge/?version=latest
    :target: https://shsk-ai-harness-docs.readthedocs.io/en/latest/
    :alt: Documentation Status

.. .. image:: https://github.com/MacHu-GWU/shsk_ai_harness_docs-project/actions/workflows/main.yml/badge.svg
    :target: https://github.com/MacHu-GWU/shsk_ai_harness_docs-project/actions?query=workflow:CI

.. .. image:: https://codecov.io/gh/MacHu-GWU/shsk_ai_harness_docs-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/shsk_ai_harness_docs-project

.. .. image:: https://img.shields.io/pypi/v/shsk-ai-harness-docs.svg
    :target: https://pypi.python.org/pypi/shsk-ai-harness-docs

.. .. image:: https://img.shields.io/pypi/l/shsk-ai-harness-docs.svg
    :target: https://pypi.python.org/pypi/shsk-ai-harness-docs

.. .. image:: https://img.shields.io/pypi/pyversions/shsk-ai-harness-docs.svg
    :target: https://pypi.python.org/pypi/shsk-ai-harness-docs

.. image:: https://img.shields.io/badge/✍️_Release_History!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/shsk_ai_harness_docs-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/⭐_Star_me_on_GitHub!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/shsk_ai_harness_docs-project

------

.. .. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://shsk-ai-harness-docs.readthedocs.io/en/latest/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/shsk_ai_harness_docs-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/shsk_ai_harness_docs-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/shsk_ai_harness_docs-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/shsk-ai-harness-docs#files


Welcome to ``shsk_ai_harness_docs`` Documentation
==============================================================================
.. image:: https://shsk-ai-harness-docs.readthedocs.io/en/latest/_static/shsk_ai_harness_docs-logo.png
    :target: https://shsk-ai-harness-docs.readthedocs.io/en/latest/

Documentation for ``shsk_ai_harness_docs``.

This project ships a set of `Agent Skills <https://agentskills.io>`_ that give AI
coding agents (Claude Code and compatible tools) grounded, always-current
documentation lookup for popular **AI agent harness frameworks**. Each skill
turns a "guess from training data" question into a precise, cited answer read
from the framework's *official* docs.


Supported Harness Frameworks
------------------------------------------------------------------------------

**Why this project exists.** Most frameworks publish a machine-readable index
(an ``llms.txt``) so that LLMs can discover their documentation. In practice
these indexes are a weak foundation for agentic search: they list a *title* and
a *URL* per page but **no description** — and some frameworks are missing from
the published index entirely. With only titles to go on, an LLM has to *guess*
which URL holds the answer, and it guesses wrong often enough to hurt.

Our skills fix this. For each framework we build a **description-enriched
index**: a real one-line description is extracted for every page (from the
page's own front-matter or first paragraph), so the agent can triage precisely
before fetching anything. The index is **cached locally** under
``~/.cache/ai-harness-docs/<framework>/<YYYY-MM-DD>/index.md`` and rebuilt at
most once per calendar day (stale dates are purged automatically), so lookups
are fast and offline-friendly after the first build. At query time the agent
reads the cached index, picks the 1–3 most relevant pages, fetches only those as
raw Markdown, and loops until it can answer. The per-framework sections below
describe how each index is sourced.

All skills live under `.claude/skills/ai-harness-docs/
<https://github.com/MacHu-GWU/shsk_ai_harness_docs-project/tree/main/.claude/skills/ai-harness-docs>`_,
one subdirectory per framework (each with its own ``SKILL.md`` and index builder).


Strands Agents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Skill name:** ``strands-agents-docs``

`Strands Agents <https://strandsagents.com/>`_ publishes an ``llms.txt`` that
gives us page titles, ordering, and the section tree — but, like most sites, no
per-page descriptions. We enrich it from the companion ``llms-full.txt`` (the
full corpus, one ``Source: <url>`` block per page) by extracting each page's
first prose paragraph as its description. This covers all of the conceptual
user-guide docs; the auto-generated API reference (the ``strands.*`` modules and
the TypeScript API) stays title-only by design, since the module/class name is
already the search signal.

**Why this matters.** The published ``llms.txt`` gives an agent only a title and
a URL — no way to tell what the page actually covers:

.. code-block:: text

    # Before (official llms.txt — title + URL only, no description)
    - [swarm](https://strandsagents.com/docs/user-guide/concepts/multi-agent/swarm/index.md)

    # After (our cached index — a real description the agent can match against)
    - [swarm](https://strandsagents.com/docs/user-guide/concepts/multi-agent/swarm/index.md): A Swarm is a collaborative agent orchestration system where multiple agents work together as a team to solve complex tasks. Unlike traditional sequential or hierarchical multi-agent systems, a Swarm…


deepagents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Skill name:** ``deepagents-docs``

`deepagents <https://docs.langchain.com/oss/python/deepagents/overview>`_ is a
sharper example of the problem: it is **not listed in LangChain's ``llms.txt``
at all**, so a naive index-based lookup finds nothing. We instead discover every
deepagents page (Python and JavaScript) from the site's ``sitemap.xml``, then
read each page as raw Markdown and lift its front-matter ``description`` (the
one-line blurb the authors wrote). The result is a fully described index for a
framework that had no usable machine index to begin with.

**Why this matters.** Here the official index is not just description-less — it
omits deepagents entirely, so an ``llms.txt``-only agent finds nothing:

.. code-block:: text

    # Before (official llms.txt — deepagents is absent; zero matching lines)
    (nothing — deepagents pages do not appear in https://docs.langchain.com/llms.txt)

    # After (our cached index — discovered from the sitemap, with a real description)
    - [Subagents](https://docs.langchain.com/oss/python/deepagents/subagents): Learn how to use subagents to delegate work and keep context clean


.. _install:

Install
------------------------------------------------------------------------------

``shsk_ai_harness_docs`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install shsk-ai-harness-docs

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade shsk-ai-harness-docs
