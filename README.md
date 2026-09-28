# CMN-C2-680 — AI Agent Human Feedback Triage & Learning-Loop Design Q&A Agent

> **Category**: Cat 2 (domain workflow (a job to be done))
> **Industry**: Common (industry-agnostic)

## Overview

Design-time question-answering about how to triage human feedback on an AI agent and run a safe learning loop. Given a JSON request with a question and optional product context, the agent redacts personal data and secrets, classifies the intent into focus dimensions (taxonomy, priority, who handles each item, learning loop, safety), retrieves matching entries from a versioned design-pattern knowledge base with a BM25-style scorer, and composes a design package — one section per dimension with guidance, a checklist and source-plus-version citations — plus an overall validation checklist. The pipeline is deterministic with no LLM step. It is advisory only: it files no feedback, trains nothing and changes nothing; unmatched questions get an explicit out-of-scope answer instead of invented guidance, sections without a supporting citation are dropped, and empty, over-long or injection-like input is rejected with a named error code. The pattern knowledge base shipped here is a seeded sample of five patterns — replace it with your own operating model.

This is an agent template built with the **AGENTIC STAR** development platform and the
**AgentCore Framework**. It is intended to be taken as a starting point: fork it, adapt it to
your own data and policies, and run it inside your own AGENTIC STAR deployment.

## Requirements

**This template does not run standalone.** It requires:

| Requirement | Notes |
|---|---|
| **AGENTIC STAR platform** | The agent connects to the platform at start-up. Without it, start-up fails immediately (see *Behaviour without the platform* below). Deployment guides and API documentation: [AGENTIC STAR Developers](https://developers.fd.agenticstar.tm.softbank.jp/) |
| **AgentCore Framework** (`agenticstar-agentcore`) | Installed from PyPI as a dependency. |
| Python | 3.11 or later (`requires-python = ">=3.11"`) |

```bash
pip install -e .
```

### Behaviour without the platform

The framework is designed to run **only** on AGENTIC STAR. There is no fallback or degraded
mode. If the platform is unreachable or the SDK version does not match, the agent raises
`PlatformRequired` during graph compile / start-up preflight rather than starting in a partially
working state. This is intentional — a half-running agent is worse than one that refuses to start.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Tests run without a platform connection. Running the agent itself does not.

## Project Structure

```
src/          agent implementation (nodes, services, schemas)
tests/        unit, integration and boundary tests
config/       agent configuration
docs/         design and operational documentation
```

See `docs/02_design.md` for the design and `docs/03_test_spec.md` for the test specification.

## Customising

1. Adjust `config/` for your own environment and policies.
2. Replace the knowledge sources and sample data with your own.
3. Review the node implementations under `src/nodes/` for domain-specific logic.
4. Re-run the test suite.

## License

MIT — see [LICENSE](LICENSE).

## Status of this repository

This template is published **as is**, by its individual author, under the MIT license. It carries
**no warranty and no support commitment**, and no organisation stands behind its behaviour or
fitness for any purpose. Issues and pull requests may or may not receive a response; that is at
the sole discretion of the repository owner.
