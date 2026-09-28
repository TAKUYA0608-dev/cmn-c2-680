"""CMN-C2-680 — inner workflow step 2: pattern_retrieve (VersionedKBRetrieve).

Deterministic BM25-lite retrieval over the **versioned** triage & learning-loop design-pattern KB, scored
by query tags + the classified focus dimensions. Sets `retrieval_hit_count`; **0 hits (rejected input or
off-topic) routes to the out-of-scope safe answer** — the agent never fabricates design guidance that is
not grounded in a cited, versioned pattern.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.services.service import DesignPatternKB
from src.utils.audit import emit_trace_event


class PatternRetrieveNode(FunctionNode):
    """Retrieve grounded, versioned design patterns for the query + focus dimensions."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        scope = json.loads(state.get("validated_input") or "{}")
        intent = json.loads(state.get("feedback_intent") or "{}")
        if state.get("error_code") or not scope.get("query"):
            emit_trace_event("pattern_retrieve.skip", {"reason": state.get("error_code") or "empty_query"}, state)
            return {
                "retrieved_patterns": "[]",
                "retrieval_hit_count": 0,
                "error_code": state.get("error_code") or "NO_PATTERN",
                "status": AgentStatus.SUCCESS.value,
            }

        # product_context is part of the input contract (validated_input) and must influence the
        # result: its terms join the retrieval query so product-specific patterns rank first
        # (found on the Marketplace, 2026-09-14: the package was byte-identical for any product).
        product_context = str(scope.get("product_context") or "").strip()
        retrieval_query = f'{scope["query"]} {product_context}'.strip()
        patterns = DesignPatternKB.retrieve(retrieval_query, intent.get("focus_dimensions", []))
        emit_trace_event(
            "pattern_retrieve.complete",
            {"hit_count": len(patterns), "kb_version": patterns[0]["version"] if patterns else None},
            state,
        )
        out = {
            "retrieved_patterns": json.dumps(patterns, ensure_ascii=False),
            "retrieval_hit_count": len(patterns),
            "status": AgentStatus.SUCCESS.value,
        }
        if not patterns:
            out["error_code"] = "NO_PATTERN"
        return out
