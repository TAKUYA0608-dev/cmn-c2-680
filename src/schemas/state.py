"""CMN-C2-680 — Agent state (Human Feedback Triage & Learning-Loop Design Q&A, Cat 2).

ADR-005: State is a flat TypedDict — never a validation/BaseModel instance. Complex fields are stored
as JSON strings (``NotRequired[str]`` + ``# JSON:``); nodes ``json.dumps`` on write / ``json.loads`` on read.

Advisory-only / State Safety: this agent answers **design-time** questions about how to *design* a
feedback-triage taxonomy and a safe learning-loop. It never processes real feedback data, never trains a
model, never mutates a prompt/eval pipeline, and never autonomously self-improves. Any PII a caller
inadvertently pastes into a feedback *example* is redacted at pre_process before it is persisted to State.

All agent-specific fields are NotRequired (populated progressively; absent at empty-start invoke).
"""

from __future__ import annotations


from framework.schemas.agent_state import AgentState


class State(AgentState):
    """Agent state for the feedback-triage / learning-loop design workflow."""

    # ── pre_process (InputValidate, S-1 normalize + PII/secret redaction) ─────
    validated_input: str  # JSON: {query, design_intent_hint, product_context}
    input_format: str  # "json" | "text" | "empty"
    enriched_context: str  # JSON: {source, channel} (read-only caller context)

    # ── inner workflow (intent_classify → pattern_retrieve → design_synthesize) ─
    feedback_intent: str  # JSON: {focus_dimensions[], is_broad}
    retrieved_patterns: str  # JSON: [{pattern_id, name, dimension, source, version, score}]
    retrieval_hit_count: int  # design patterns retrieved (0 → out-of-scope safe answer)
    design_sections: str  # JSON: [{dimension, title, guidance[], checklist[], citations[]}]
    result: str  # JSON: assembled Feedback Triage & Learning-Loop Design Package

    # ── post_process (SafetyAndCitationGate: S-3 + S-4 audit) ─────────────────
    formatted_output: str  # JSON: final response envelope (design package + disclaimer)
    disclaimer: str  # mandatory advisory / "does not authorize self-improvement" note
    audit_logged: bool  # True once the terminal audit event is emitted

    # ── degraded-path signalling (SUCCESS + error_code, never status=ERROR) ──
    error_code: str  # INPUT_REJECTED | INPUT_TOO_LONG | NO_PATTERN
    error_message: str  # operator-facing detail
