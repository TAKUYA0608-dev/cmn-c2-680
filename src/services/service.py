"""CMN-C2-680 — deterministic domain services (no framework imports).

`DesignPatternKB`: a **versioned** knowledge base of human-feedback triage & learning-loop *design*
patterns across five dimensions — taxonomy / priority / review-routing / learning-loop / safety — each
record sourced from publicly citable practice guidance (advisory-only: no real feedback data, no PII).
Intent classification + retrieval are deterministic (keyword/tag scoring + dimension matching) and
auditable; a production deployment reserves the LLM for design-section phrasing only.
"""

from __future__ import annotations

from typing import Any

# ── knowledge-base version (cited alongside every pattern) ────────────────────
KB_VERSION = "2026.07.1"

# ── the five feedback-design dimensions ───────────────────────────────────────
DIMENSIONS = ("taxonomy", "priority", "review_routing", "learning_loop", "safety")

_DIMENSION_LABEL = {
    "taxonomy": "Triage Taxonomy Design",
    "priority": "Priority Scoring Design",
    "review_routing": "Review Routing Design",
    "learning_loop": "Learning-Loop Design",
    "safety": "Safety Guardrail Design",
}

# ── versioned design-pattern KB (public practice guidance, no PII) ────────────
# Each record: {pattern_id, name, dimension, summary, guidance[], checklist[], tags[], source, version}
KB: list[dict[str, Any]] = [
    {
        "pattern_id": "FBT-TAX-001",
        "dimension": "taxonomy",
        "name": "Feedback Triage Taxonomy",
        "summary": "Sort each item of human feedback into one of four disjoint classes so that safety "
        "issues are never mixed with preference signals.",
        "guidance": [
            "Define four disjoint classes: safety_defect / factual_failure / ux_preference / training_signal_candidate.",
            "Give every class an operational definition + a positive/negative example so labels are reproducible.",
            "Require exactly one primary class per item; allow secondary tags but never two primary classes.",
        ],
        "checklist": [
            "Each class has an operational definition and worked examples.",
            "safety_defect is defined independently of ux_preference (no overlap).",
        ],
        "tags": [
            "taxonomy",
            "分類",
            "classify",
            "categor",
            "taxonom",
            "label",
            "ラベル",
            "safety defect",
            "preference",
            "factual",
            "class",
            "sort",
        ],
        "source": "Human-feedback triage practice guide — feedback taxonomy",
    },
    {
        "pattern_id": "FBT-PRI-002",
        "dimension": "priority",
        "name": "Priority Scoring Rubric",
        "summary": "Score triaged feedback by severity x frequency x safety-impact so the highest-risk "
        "items surface first, deterministically and auditably.",
        "guidance": [
            "Compute priority = severity x frequency, then apply a safety-impact multiplier for safety_defect items.",
            "Use a fixed ordinal scale (e.g. 1-5) per factor and document the rubric so scores are reproducible.",
            "Cap latency: any safety_defect above a threshold is auto-escalated regardless of frequency.",
        ],
        "checklist": [
            "Priority formula is documented and deterministic.",
            "safety_defect items cannot be de-prioritised below the escalation threshold by low frequency.",
        ],
        "tags": [
            "priorit",
            "優先",
            "severity",
            "重大度",
            "scoring",
            "スコア",
            "rank",
            "rubric",
            "score",
            "urgency",
            "緊急",
        ],
        "source": "Human-feedback triage practice guide — priority scoring",
    },
    {
        "pattern_id": "FBT-ROU-003",
        "dimension": "review_routing",
        "name": "HITL Review Routing",
        "summary": "Route each feedback class to the correct human reviewer with a mandatory "
        "human-in-the-loop gate before any downstream use.",
        "guidance": [
            "Route safety_defect -> safety/governance review; factual_failure -> QA; ux_preference -> product; "
            "training_signal_candidate -> ML owner.",
            "Insert a mandatory HITL gate: no feedback item advances to a learning-loop without a named human sign-off.",
            "Record the reviewer, decision, and timestamp for every routed item (auditability).",
        ],
        "checklist": [
            "Every feedback class maps to exactly one named review owner.",
            "A human sign-off is required before any item enters the learning-loop.",
        ],
        "tags": [
            "routing",
            "route",
            "経路",
            "review",
            "レビュー",
            "escalat",
            "エスカレ",
            "hitl",
            "human-in-the-loop",
            "human review",
            "reviewer",
            "sign-off",
            "承認",
        ],
        "source": "Human-feedback triage practice guide — review routing",
    },
    {
        "pattern_id": "FBT-LOOP-004",
        "dimension": "learning_loop",
        "name": "Safe Learning-Loop Design",
        "summary": "Decide which feedback may inform evaluation vs. improvement, and gate every path with "
        "human review — the loop is a design, never an autonomous self-improver.",
        "guidance": [
            "Separate two sinks: an evaluation set (measures quality) and an improvement candidate set "
            "(may inform future training) — an item may feed eval without ever feeding improvement.",
            "Only human-reviewed, de-identified training_signal_candidate items may enter the improvement set.",
            "Keep the loop advisory: the design defines gates and owners; it does not auto-train or auto-deploy.",
        ],
        "checklist": [
            "Eval-only and improvement-candidate sinks are distinct.",
            "Every improvement-candidate item passed a human review gate.",
            "No path auto-updates a model/prompt without human approval.",
        ],
        "tags": [
            "learning loop",
            "learning-loop",
            "ラーニング",
            "ループ",
            "loop",
            "retrain",
            "training signal",
            "eval",
            "評価",
            "improvement",
            "改善",
            "training",
            "訓練",
            "dataset",
        ],
        "source": "Human-feedback triage practice guide — safe learning-loop",
    },
    {
        "pattern_id": "FBT-SAFE-005",
        "dimension": "safety",
        "name": "Safety-Defect vs Preference-Signal Separation",
        "summary": "Guardrails that keep a safety defect from being silently treated as a mere preference, "
        "and keep the loop from acting on unreviewed signals.",
        "guidance": [
            "When a safety_defect and a ux_preference conflict on the same item, the safety class wins.",
            "Redact PII from feedback examples before they are used in any design artefact or example set.",
            "Add an explicit disclaimer that the design does not authorize autonomous self-improvement.",
        ],
        "checklist": [
            "Safety class takes precedence over preference on conflict.",
            "PII is redacted from all feedback examples.",
            "Output states the design is advisory and does not authorize self-improvement.",
        ],
        "tags": [
            "safety",
            "安全",
            "guardrail",
            "ガードレール",
            "defect",
            "harm",
            "risk",
            "リスク",
            "separation",
            "切り分け",
            "conflict",
            "precedence",
        ],
        "source": "Human-feedback triage practice guide — safety guardrails",
    },
]

# Domain-relevance keywords: if a query contains NONE of these it is off-topic (out-of-scope).
_DOMAIN_KEYWORDS = (
    "feedback",
    "フィードバック",
    "triage",
    "トリアージ",
    "learning loop",
    "learning-loop",
    "ラーニングループ",
    "learning",
    "loop",
    "ループ",
    "improvement",
    "改善",
    "taxonomy",
    "分類",
    "review",
    "レビュー",
    "priorit",
    "優先",
    "safety",
    "安全",
    "signal",
    "eval",
    "評価",
    "user voice",
    "ユーザーの声",
    "voc",
)

# Dimension-specific keyword cues for intent classification.
_DIMENSION_CUES = {
    "taxonomy": (
        "taxonomy",
        "分類",
        "classify",
        "categor",
        "taxonom",
        "label",
        "ラベル",
        "safety defect",
        "preference",
        "factual",
        "class",
    ),
    "priority": ("priorit", "優先", "severity", "重大度", "scoring", "スコア", "rank", "urgency", "緊急"),
    "review_routing": (
        "routing",
        "route",
        "経路",
        "review",
        "レビュー",
        "escalat",
        "エスカレ",
        "hitl",
        "human-in-the-loop",
        "human review",
        "reviewer",
        "承認",
        "sign-off",
    ),
    "learning_loop": (
        "learning loop",
        "learning-loop",
        "ラーニング",
        "ループ",
        "retrain",
        "training signal",
        "training-signal",
        "eval",
        "評価",
        "improvement",
        "改善",
        "training",
    ),
    "safety": (
        "safety",
        "安全",
        "guardrail",
        "ガードレール",
        "defect",
        "harm",
        "risk",
        "リスク",
        "separation",
        "切り分け",
    ),
}


class DesignPatternKB:
    """Deterministic intent classification + retrieval over the versioned design-pattern KB."""

    @staticmethod
    def classify_intent(query: str) -> dict[str, Any]:
        """Classify the feedback-design intent into focus dimensions.

        Off-topic queries (no domain keyword) → empty focus_dimensions (routes to the safe answer).
        On-topic-but-general queries → all dimensions with is_broad=True.
        """
        low = (query or "").lower()
        if not any(kw in low for kw in _DOMAIN_KEYWORDS):
            return {"focus_dimensions": [], "is_broad": False}
        focus = [dim for dim in DIMENSIONS if any(cue in low for cue in _DIMENSION_CUES[dim])]
        if not focus:
            # On-topic but no specific dimension named → cover the whole package.
            return {"focus_dimensions": list(DIMENSIONS), "is_broad": True}
        return {"focus_dimensions": focus, "is_broad": len(focus) >= 4}

    @staticmethod
    def retrieve(query: str, focus_dimensions: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        """BM25-lite retrieval. [] when the query is off-topic and matches no pattern (out-of-scope)."""
        low = (query or "").lower()
        focus = set(focus_dimensions or [])
        scored: list[tuple[int, dict[str, Any]]] = []
        for rec in KB:
            score = sum(2 for t in rec["tags"] if t in low)
            if rec["name"].lower() in low:
                score += 4
            if rec["dimension"] in focus:
                score += 3
            if score:
                scored.append((score, rec))
        scored.sort(key=lambda x: (-x[0], DIMENSIONS.index(x[1]["dimension"])))
        out = []
        for score, rec in scored[:top_k]:
            out.append(
                {
                    "pattern_id": rec["pattern_id"],
                    "name": rec["name"],
                    "dimension": rec["dimension"],
                    "dimension_label": _DIMENSION_LABEL[rec["dimension"]],
                    "summary": rec["summary"],
                    "guidance": rec["guidance"],
                    "checklist": rec["checklist"],
                    "source": rec["source"],
                    "version": KB_VERSION,
                    "score": score,
                }
            )
        return out

    @staticmethod
    def dimension_label(dimension: str) -> str:
        return _DIMENSION_LABEL.get(dimension, dimension)
