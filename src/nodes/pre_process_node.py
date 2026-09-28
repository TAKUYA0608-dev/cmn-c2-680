"""CMN-C2-680 — pre_process node: InputValidate (S-1 normalize + injection reject + PII/secret redaction).

Accepts a structured JSON request or NL text, normalizes it (NFKC + control-char strip) and applies the
S-1 input gate. **Prompt-injection markers, oversize, and empty input are all handled as degraded
``status=SUCCESS + error_code`` paths inside ``execute()``** (``INJECTION_REJECTED`` / ``INPUT_TOO_LONG`` /
``INPUT_REJECTED``): the untrusted body is discarded (``validated_input="{}"``) and never processed, and
the request flows to the out-of-scope safe answer so that main / post_process (disclaimer / redaction /
audit) always run. It is **never ``status=ERROR``**, which would short-circuit ``__call__`` and skip main /
post_process. The S-2 input hook (`_extra_security_gate_input`) is a pass-through — it
never raises. Post-process retains a residual-marker neutralization pass as S-3 defense-in-depth.

Any PII a caller inadvertently pastes into a feedback *example* (email / phone / credential-like token) is
redacted before the query is persisted to State (`validated_input`) — advisory-only, no real feedback data.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel

from src.utils.audit import emit_trace_event

_MAX_INPUT = 20_000
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
# Prompt-injection markers rejected at the S-1 input gate (degraded SUCCESS + INJECTION_REJECTED — the
# untrusted body is discarded, never processed). S-3 output gate keeps a residual-marker neutralization
# pass as defense-in-depth.
_INJECTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "disregard the above",
    "system prompt",
    "you are now",
    "###system",
    "<|im_start|>",
)

# Defense-in-depth redaction of PII / secrets that may appear inside a pasted feedback example.
_EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,4}")
_PHONE = re.compile(r"(?<![\d.])(?:\+?\d[\d\-\s()]{8,17}\d)(?![\d.])")
# Credential-like tokens (kept as split fragments so no literal secret is committed — S-5).
_SECRET = re.compile(r"\b(?:sk-[A-Za-z0-9]{6,}|AKIA[A-Z0-9]{10,}|eyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_.-]{6,})\b")
_MASKS = ((_EMAIL, "[EMAIL-REDACTED]"), (_PHONE, "[PHONE-REDACTED]"), (_SECRET, "[SECRET-REDACTED]"))


def _nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def _sanitize(text: str) -> str:
    """Strip control chars (S-1) and redact PII / secrets before the query is written to State."""
    clean = _CONTROL.sub("", text)
    # Redact secrets first, then phone, then email (order avoids masking overlap surprises).
    clean = _SECRET.sub("[SECRET-REDACTED]", clean)
    clean = _EMAIL.sub("[EMAIL-REDACTED]", clean)
    clean = _PHONE.sub("[PHONE-REDACTED]", clean)
    return clean


class PreProcessNode(FunctionNode):
    """Validate the request and extract the feedback-design slots."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_input(self, state: dict[str, Any]) -> dict[str, Any]:
        """S-2 input hook — pass-through (no hard reject).

        SDK 1.0.0 contract: MUST NOT raise. Prompt-injection / oversize / empty input are handled as
        degraded `status=SUCCESS + error_code` paths in `execute()` (the untrusted body is discarded and
        never processed) so main / post_process S-3/S-4 always run. A `status=ERROR` here would
        short-circuit `__call__` and skip main / post_process (disclaimer / redaction / audit). The
        framework default S-2 PII masking still applies. Returns state unchanged.
        """
        return dict(state)

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        raw = state.get("user_input", "") or ""
        input_context = state.get("input_context", {})  # read-only [C1]
        enriched = json.dumps(
            {
                "source": "HumanFeedbackTriageLearningLoopDesignAgent",
                "channel": input_context.get("channel", "unknown"),
            },
            ensure_ascii=False,
        )
        normalized = _nfkc(raw).strip()

        # Prompt-injection -> degraded SUCCESS + error_code (never processed). NOT status=ERROR: ERROR
        # short-circuits __call__ so main / post_process (disclaimer / redaction / audit) would be
        # skipped. The untrusted body is discarded; the out-of-scope safe answer runs.
        if any(marker in normalized.lower() for marker in _INJECTION_MARKERS):
            emit_trace_event("input_validate.rejected", {"reason": "prompt_injection"}, state)
            return {
                "validated_input": "{}",
                "input_format": "rejected",
                "enriched_context": enriched,
                "error_code": "INJECTION_REJECTED",
                "error_message": "prompt-injection marker detected; input not processed",
                "status": AgentStatus.SUCCESS.value,
            }

        # Oversize -> degraded SUCCESS + error_code; the body is discarded (validated_input="{}") and
        # never processed. NOT status=ERROR: ERROR short-circuits __call__, so main / post_process
        # (disclaimer / redaction / audit) would be skipped. The out-of-scope safe
        # answer + S-3/S-4 always run.
        if len(raw) > _MAX_INPUT:
            emit_trace_event("input_validate.rejected", {"reason": "input_too_long"}, state)
            return {
                "validated_input": "{}",
                "input_format": "oversize",
                "enriched_context": enriched,
                "error_code": "INPUT_TOO_LONG",
                "error_message": f"input exceeds {_MAX_INPUT} chars",
                "status": AgentStatus.SUCCESS.value,
            }

        if not raw.strip():
            emit_trace_event("input_validate.rejected", {"reason": "empty_input"}, state)
            return {
                "validated_input": "{}",
                "input_format": "empty",
                "enriched_context": enriched,
                "error_code": "INPUT_REJECTED",
                "status": AgentStatus.SUCCESS.value,
            }

        scope, fmt = self._parse(normalized)
        emit_trace_event(
            "input_validate.validated",
            {"input_format": fmt, "has_product_context": bool(scope.get("product_context"))},
            state,
        )
        return {
            "validated_input": json.dumps(scope, ensure_ascii=False),
            "input_format": fmt,
            "enriched_context": enriched,
            "status": AgentStatus.SUCCESS.value,
        }

    def _parse(self, text: str) -> tuple[dict[str, Any], str]:
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                query = str(obj.get("query") or obj.get("question") or "")
                return {
                    "query": _sanitize(query),
                    "design_intent_hint": obj.get("design_intent_hint"),
                    "product_context": _sanitize(str(obj.get("product_context") or "")),
                }, "json"
        except (ValueError, TypeError):
            pass
        clean = _sanitize(text)
        return {"query": clean, "design_intent_hint": None, "product_context": ""}, "text"
