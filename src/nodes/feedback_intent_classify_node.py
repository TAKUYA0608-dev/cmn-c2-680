"""CMN-C2-680 — inner workflow step 1: feedback_intent_classify.

Classifies the feedback-design intent of the query into focus dimensions
{taxonomy, priority, review_routing, learning_loop, safety}. Classification is **deterministic**
(keyword / tag scoring — auditable, no LLM); the LLM is reserved for design-section *phrasing* only
(see docs/02 §Design Decision Record and src/services/service.py). Off-topic queries yield an empty
focus set which routes the workflow to the out-of-scope safe answer. Skips (no-op) on rejected input.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.services.service import DesignPatternKB
from src.utils.audit import emit_trace_event


class FeedbackIntentClassifyNode(FunctionNode):
    """Classify which feedback-design dimensions the query is asking about."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        scope = json.loads(state.get("validated_input") or state.get("user_input") or "{}")
        canonical = json.dumps(scope, ensure_ascii=False)
        if state.get("error_code") or not scope.get("query"):
            emit_trace_event(
                "feedback_intent_classify.skip", {"reason": state.get("error_code") or "empty_query"}, state
            )
            return {
                "validated_input": canonical,
                "feedback_intent": json.dumps({"focus_dimensions": [], "is_broad": False}, ensure_ascii=False),
                "status": AgentStatus.SUCCESS.value,
            }

        intent = DesignPatternKB.classify_intent(scope["query"])
        emit_trace_event(
            "feedback_intent_classify.complete",
            {"focus_dimensions": intent["focus_dimensions"], "is_broad": intent["is_broad"]},
            state,
        )
        return {
            "validated_input": canonical,
            "feedback_intent": json.dumps(intent, ensure_ascii=False),
            "status": AgentStatus.SUCCESS.value,
        }
