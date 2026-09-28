"""CMN-C2-680 — post_process node: SafetyAndCitationGate (S-3 output gate + S-4 audit).

This is where the **injection / grounding defense lives** (pre_process does normalization only): the node
(1) neutralizes any residual prompt-injection marker that survived into the synthesized output, (2) verifies
citation completeness — a grounded design package must cite a versioned source for every section, dropping
any unsupported section — and (3) appends the mandatory advisory disclaimer stating the design does NOT
authorize autonomous self-improvement. S-4 emits an audit event (dimensions / counts only — no PII). Runs on
both the full design package and the out-of-scope safe branch.
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.utils.audit import emit_trace_event

_DISCLAIMER = (
    "本パッケージは公開された feedback triage / learning-loop 設計パターンに基づく design-time の参考"
    "ガイダンス（advisory）であり、最終的な triage 基準・レビュー経路・learning-loop の採否は各プロダクト"
    "／組織の責任者が人手レビューのうえ決定してください。本エージェントは設計助言のみを行い、feedback 実データの"
    "処理・モデル/プロンプト/評価パイプラインの変更・自律的な self-improvement は一切行いません（does not "
    "authorize autonomous self-improvement）。"
)
# Injection markers neutralized if they survive into synthesized output (grounding defense at S-3).
_INJECTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "disregard the above",
    "system prompt",
    "you are now",
    "###system",
    "<|im_start|>",
)


def _neutralize(text: str) -> str:
    """Strip prompt-injection markers from an output string (case-insensitive)."""
    for marker in _INJECTION_MARKERS:
        text = re.sub(re.escape(marker), "[neutralized]", text, flags=re.IGNORECASE)
    return text


class PostProcessNode(FunctionNode):
    """Sanitize + verify citations, append advisory disclaimer, emit audit."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """S-3 preservation check: advisory / no-self-improvement disclaimer present in the envelope.

        SDK 1.0.0 contract: receives the **result dict from `execute()`**; returns the (possibly filtered)
        result. MAY raise to block an output missing the mandatory disclaimer.
        """
        out = result.get("formatted_output", "")
        if out and "advisory" not in out and "self-improvement" not in out:
            raise ValueError("S-3: advisory / no-self-improvement disclaimer missing from output")
        return dict(result)

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        report: dict[str, Any] = json.loads(state.get("result", "{}") or "{}")

        # S-3 grounding defense: drop any section without a citation (unsupported claim).
        grounded = report.get("status_kind") == "design_package"
        raw_sections = report.get("sections", [])
        sections = [s for s in raw_sections if s.get("citations")] if grounded else raw_sections
        dropped = len(raw_sections) - len(sections)
        citations = report.get("citations", [])
        citation_complete = (not grounded) or bool(sections)

        formatted = {
            "status_kind": report.get("status_kind"),
            "sections": sections,
            "validation_checklist": report.get("validation_checklist", []),
            "product_context": report.get("product_context"),
            "product_context_applied": report.get("product_context_applied"),
            "citations": citations,
            "citation_complete": citation_complete,
            "message": report.get("message"),
            "disclaimer": _DISCLAIMER,
        }
        # S-3 injection defense: neutralize any residual marker in the serialized envelope.
        serialized = _neutralize(json.dumps(formatted, ensure_ascii=False))

        emit_trace_event(
            "safety_citation_gate.complete",
            {
                "status_kind": report.get("status_kind"),
                "section_count": len(sections),
                "sections_dropped_unsupported": dropped,
                "citation_complete": citation_complete,
                "error_code": state.get("error_code"),
            },
            state,
        )
        return {
            "formatted_output": serialized,
            "disclaimer": _DISCLAIMER,
            "audit_logged": True,
            "status": AgentStatus.SUCCESS.value,
        }
