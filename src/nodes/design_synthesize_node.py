"""CMN-C2-680 — inner workflow step 3: design_synthesize (TriageDesignSynthesize).

Composes the multi-dimensional **Feedback Triage & Learning-Loop Design Package** — a design section per
retrieved dimension (triage taxonomy → priority scoring → review routing → learning-loop → safety
guardrails) plus an aggregated validation checklist — grounded in the retrieved versioned patterns with
source+version citations. On the 0-hit / rejected branch it emits the out-of-scope safe answer; it never
fabricates a design that is not backed by a cited pattern.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.utils.audit import emit_trace_event

_OUT_OF_SCOPE = (
    "ご質問に対応する feedback triage / learning-loop の設計パターンが、バージョン管理された設計パターン KB "
    "（taxonomy / priority / review-routing / learning-loop / safety）に見つかりませんでした。"
    "設計したい関心（トリアージ分類・優先度・レビュー経路・安全な learning-loop 設計 など）を具体化のうえ再度ご質問ください。"
    "本エージェントは design-time の設計助言のみを行い、feedback 実データの処理・自律的な self-improvement は行いません。"
)


class DesignSynthesizeNode(FunctionNode):
    """Compose the Feedback Triage & Learning-Loop Design Package (or safe answer on 0-hit)."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        patterns = json.loads(state.get("retrieved_patterns") or "[]")
        if state.get("error_code") or not patterns:
            emit_trace_event("design_synthesize.safe", {"reason": state.get("error_code") or "no_pattern"}, state)
            report: dict[str, Any] = {
                "status_kind": "out_of_scope",
                "message": _OUT_OF_SCOPE,
                "sections": [],
                "validation_checklist": [],
                "citations": [],
            }
            return {"result": json.dumps(report, ensure_ascii=False), "status": AgentStatus.SUCCESS.value}

        sections: list[dict[str, Any]] = []
        citations: list[dict[str, str]] = []
        validation_checklist: list[dict[str, str]] = []
        for p in patterns:
            cite = {"pattern_id": p["pattern_id"], "source": p["source"], "version": p["version"]}
            sections.append(
                {
                    "dimension": p["dimension"],
                    "dimension_label": p["dimension_label"],
                    "title": p["name"],
                    "summary": p["summary"],
                    "guidance": p["guidance"],
                    "checklist": p["checklist"],
                    "citations": [cite],
                }
            )
            citations.append(cite)
            for item in p["checklist"]:
                validation_checklist.append({"dimension": p["dimension"], "item": item})

        scope = json.loads(state.get("validated_input") or "{}")
        product_context = str(scope.get("product_context") or "").strip() if isinstance(scope, dict) else ""
        report = {
            "status_kind": "design_package",
            "sections": sections,
            "validation_checklist": validation_checklist,
            "citations": citations,
            # Echo the product context the caller supplied and say how it was applied, so the
            # reader can see the package was built for this product and not a generic one.
            "product_context": product_context or None,
            "product_context_applied": ("retrieval query + pattern ranking" if product_context else "not supplied"),
        }
        emit_trace_event(
            "design_synthesize.complete",
            {
                "section_count": len(sections),
                "citation_count": len(citations),
                "checklist_items": len(validation_checklist),
            },
            state,
        )
        return {
            "result": json.dumps(report, ensure_ascii=False),
            "design_sections": json.dumps(sections, ensure_ascii=False),
            "status": AgentStatus.SUCCESS.value,
        }
