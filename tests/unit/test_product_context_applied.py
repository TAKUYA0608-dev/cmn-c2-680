"""product_context is an input-contract field: it must change retrieval and be visible in the package."""

import json

from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel

from src.graph.graph import Graph

QUERY = "feedback の triage taxonomy・優先度・review routing・safe learning-loop をどう設計する?"


def _run(product_context):
    payload = {"query": QUERY}
    if product_context is not None:
        payload["product_context"] = product_context
    agent = Graph()
    agent.compile()
    out = agent.invoke(
        json.dumps(payload, ensure_ascii=False),
        ctx=InvocationContext(caller_id="t", caller_trust_level=TrustLevel.VERIFIED_EXTERNAL),
    )
    o = out["output"]
    return json.loads(o) if isinstance(o, str) else o


def test_package_echoes_and_declares_the_product_context():
    pkg = _run("社内 RAG assistant")
    assert pkg["status_kind"] == "design_package"
    assert pkg["product_context"] == "社内 RAG assistant"
    assert pkg["product_context_applied"] == "retrieval query + pattern ranking"
    none = _run(None)
    assert none["product_context"] is None and none["product_context_applied"] == "not supplied"


def test_product_context_terms_reach_retrieval():
    # A product context naming a KB pattern dimension term must be able to change the ranking:
    # the retrieval query with and without it must differ (observed through the pattern order/set).
    with_ctx = [s["title"] for s in _run("retrieval routing safety")["sections"]]
    without = [s["title"] for s in _run(None)["sections"]]
    assert with_ctx != without, (with_ctx, without)
