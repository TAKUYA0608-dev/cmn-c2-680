# Template Design Specification — CMN-C2-680

AI Agent Human Feedback Triage & Learning-Loop Design Q&A Agent (Cat 2).

## Position in AgentCore Architecture

- **Agent Class**: `HumanFeedbackTriageLearningLoopDesignAgent` (module-level alias of `Graph`)
- **L1 Base**: **AgentBaseGraph** (Cat 2 — outer 5-node backbone; direct L1 inheritance, no L2)
- **Category**: Cat 2 — a multi-step **design workflow** (validate → intent-classify → pattern-retrieve →
  design-synthesize → safety/citation gate) that produces a **Feedback Triage & Learning-Loop Design
  Package**; CMN industry (AI engineering infrastructure)
- **Three-Layer Separation**: State = flat TypedDict; Node = L1 inheritance (`execute` override only);
  Graph = outer `AgentBaseGraph` + **`GraphNode` in the `main` slot** wrapping an inner `BaseGraph`

> **Advisory-only scope (design commitment):** this template answers **design-time** questions about how a
> team should *design* feedback triage and a safe learning-loop. It does **not** process real feedback data,
> does **not** train a model, does **not** mutate a prompt/eval pipeline, and does **not** autonomously
> self-improve. This is what separates it from the No-Go self-improvement cluster.

## Architecture Overview

Cat 2 pattern — the `main` slot is a **`GraphNode`** (`FeedbackTriageWorkflowGraphNode`, **subgraph
cached**) that wraps the inner `FeedbackTriageWorkflow` (`BaseGraph`). Inner graph is a **static linear
backbone with per-node skip guards**. Grounded in a **versioned** triage & learning-loop design-pattern
KB; unsupported claims are rejected and every grounded section carries a citation.

### Node Configuration

| Node | Responsibility | Input State | Output State | Inherits/Overrides |
|------|---------------|-------------|--------------|-------------------|
| initialize | schema_version, session_id, trust_level | user_input | (framework) | InitializeNode (default) |
| pre_process | `PreProcessNode` (InputValidate) — S-1 NFKC normalize + PII/secret redaction of feedback examples + slot extraction | user_input | validated_input, input_format, enriched_context | FunctionNode.execute |
| main | `FeedbackTriageWorkflowGraphNode` (GraphNode) → inner workflow | validated_input | result, retrieval_hit_count | GraphNode |
| post_process | `PostProcessNode` (SafetyAndCitationGate) — S-3 sanitize + citation completeness + advisory disclaimer + S-4 audit | result | formatted_output, disclaimer, audit_logged | FunctionNode.execute |
| finalize | response_metadata, total_time_ms | | (framework) | FinalizeNode (default) |

**Inner workflow (`FeedbackTriageWorkflow` : BaseGraph):**

```
START → feedback_intent_classify → pattern_retrieve → design_synthesize → END
```

| Inner node | Responsibility |
|---|---|
| FeedbackIntentClassify | classify the feedback-design intent into focus dimensions {taxonomy, priority, review_routing, learning_loop, safety} (**deterministic** keyword/tag classifier — no LLM; the LLM is reserved for design-section *phrasing* only) |
| PatternRetrieve | **deterministic** BM25-lite retrieval over the versioned design-pattern KB; 0-hit → out-of-scope safe answer |
| DesignSynthesize | compose the multi-dimensional Design Package (taxonomy → priority → review routing → learning-loop → safety guardrails → validation checklist) grounded in retrieved patterns, with source+version citations |

### Data Flow

```
START → initialize → pre_process → main(GraphNode → inner linear workflow) → post_process → finalize → END
                                     ↓ (retry, max 3)
                                   pre_process
```

Rejected / 0-hit input sets `error_code` + `retrieval_hit_count=0`; the classifier/retriever no-op and
design_synthesize emits the out-of-scope safe answer — no fabricated design guidance.

### Security model (task-specific)

- **S-1 = input gate** at pre_process (NFKC + control-char strip + PII/secret redaction of feedback
  examples). **Prompt-injection markers, oversize, and empty input are all rejected as degraded
  `SUCCESS + error_code` paths inside `execute()`** (`INJECTION_REJECTED` / `INPUT_TOO_LONG` /
  `INPUT_REJECTED`): the untrusted body is discarded (`validated_input="{}"`) and never processed, so the
  0-hit branch yields the out-of-scope safe answer and post_process S-3/S-4 always run.
- **S-2 input hook = pass-through** (never a hard reject / never raises). Rejections are surfaced via the
  degraded paths above — it is **never `status=ERROR`** — ERROR short-circuits `__call__`, sending
  `route()` straight to `finalize`, so main / post_process (disclaimer / redaction / audit) would never run.
- **Injection defense-in-depth = S-3 output gate** at post_process: neutralize any residual injection
  marker that survives into the synthesized output, drop unsupported claims, and require the advisory
  disclaimer.

### State Definition

| Field | Type | Purpose |
|-------|------|---------|
| validated_input | str (JSON) | `{query, design_intent_hint, product_context}` (feedback examples redacted) |
| feedback_intent | str (JSON) | `{focus_dimensions[], is_broad}` |
| retrieved_patterns / retrieval_hit_count | str/int | versioned KB matches / 0 → out-of-scope safe answer |
| design_sections | str (JSON) | `[{dimension, title, guidance[], checklist[], citations[]}]` |
| result / formatted_output | str (JSON) | inner design-package report / final envelope |
| disclaimer / audit_logged | str/bool | mandatory advisory disclaimer + terminal audit |
| error_code / error_message | str | degraded path (SUCCESS + error_code, never status=ERROR) |

**State Constraints:** flat TypedDict; JSON strings for complex fields; **no real feedback data / no PII
persisted** (advisory-only); `enriched_context` is a JSON string (ADR-005).

## Framework Utilization

- [x] **GraphNode-in-main** (Cat 2 composition, criterion #9) — `error_strategy="propagate"`, `propagate_hitl=False`, **subgraph cached** (`self._subgraph`)
- [x] S-1 `required_trust_level=VERIFIED_EXTERNAL` on all FunctionNode subclasses (pre / post / 3 inner)
- [x] S-2 `_extra_security_gate_input()` (pre) — **pass-through, never raises** (SDK 1.0.0); **injection / oversize / empty are degraded `SUCCESS + error_code` (`INJECTION_REJECTED` / `INPUT_TOO_LONG` / `INPUT_REJECTED`) in `execute()`, never `status=ERROR`** (ERROR would short-circuit `__call__` and skip main / post_process); S-3 keeps residual-marker neutralization as defense-in-depth
- [x] S-3 `_extra_security_gate_output()` (post) — advisory-disclaimer preservation; **may raise** (SDK 1.0.0)
- [x] S-4 `emit_trace_event()` in every `execute()` (dimensions / counts only — no PII); terminal audit always fires

## Import Isolation Confirmation
- [x] No `agenticstar` SDK (Level 0) import — PB-4
- [x] Import targets: `framework/`, `langgraph`, and `src.` only

## Design Decision Record

| Decision | Chosen | Rationale |
|----------|--------|-----------|
| L1 base type | AgentBaseGraph | Fixed pipeline, no autonomous loop |
| Composition | **GraphNode-in-main + inner BaseGraph (cached)** | Cat 2 multi-step design workflow |
| Inner topology | **Linear + per-node skip guards** | Conditional edges don't propagate across the subgraph boundary |
| Intent classify + retrieval | **Deterministic (no LLM in template)** | Auditable dimension routing + BM25-lite; production reserves LLM for synthesis phrasing |
| Injection handling | **Degraded reject at S-1 input + S-3 output neutralization (defense-in-depth)** | Consistent with sibling Cat 2 templates; untrusted body discarded before the workflow, residual markers neutralized at output |
| PII / feedback data | **Advisory-only — none processed** | Design guidance only; feedback examples redacted; never files/trains/self-improves |
| Rejection signalling | SUCCESS + error_code | Guarantees post_process S-3/S-4 always run (SDK 1.0.0) |

## Open Items (Stage ③ implementation MR)
- Node implementations + inner workflow graph (shipped in the implementation MR).
- Seeded versioned `DesignPatternKB` (patterns across taxonomy / priority / review-routing / learning-loop / safety).
- Unit + integration + PB tests; coverage ≥ 80%.


### 追記 (2026-09-14): product_context の適用

`product_context` は入力契約のフィールドであり、結果に影響しなければならない。pattern_retrieve は `query + product_context` を検索語に用いてプロダクト固有のパターンを上位に出し、design_package は `product_context`（echo）と `product_context_applied`（"retrieval query + pattern ranking" / "not supplied"）を持つ。プロダクト種別ごとの追加フィードバック分類（例: RAG の retrieval miss / stale index / citation failure）は出典付きの KB パターンとして別途追加する。
