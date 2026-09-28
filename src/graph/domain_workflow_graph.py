"""CMN-C2-680 — inner domain workflow graph (Cat 2).

Instantiated by FeedbackTriageWorkflowGraphNode.get_subgraph() in graph.py. Linear topology with per-node
skip guards (the portable Cat 2 form; conditional edges don't propagate across the subgraph boundary):

    START → feedback_intent_classify → pattern_retrieve → design_synthesize → END

On rejected / off-topic input, pattern_retrieve sets retrieval_hit_count=0 (+error_code); design_synthesize
emits the out-of-scope safe answer — no fabricated design guidance.
"""

from __future__ import annotations
from typing import Any

from langgraph.graph import END, START

from framework.graph.base_graph import BaseGraph
from framework.schemas.agent_state import AgentState

from src.nodes.design_synthesize_node import DesignSynthesizeNode
from src.nodes.feedback_intent_classify_node import FeedbackIntentClassifyNode
from src.nodes.pattern_retrieve_node import PatternRetrieveNode
from src.schemas.state import State


class FeedbackTriageWorkflow(BaseGraph):
    """Inner graph: intent_classify → pattern_retrieve → design_synthesize."""

    @property
    def name(self) -> str:
        return "FeedbackTriageWorkflow"

    @property
    def state_schema(self) -> type:
        return State

    def _validate_config(self) -> None:
        pass

    def register_nodes(self) -> None:
        # No super() — BaseGraph.register_nodes() is abstract.
        self._nodes["feedback_intent_classify"] = FeedbackIntentClassifyNode()
        self._nodes["pattern_retrieve"] = PatternRetrieveNode()
        self._nodes["design_synthesize"] = DesignSynthesizeNode()

    def add_edges(self) -> None:
        # Static linear backbone; the 0-hit / rejected skip is handled by per-node guards.
        self._sg.add_edge(START, "feedback_intent_classify")
        self._sg.add_edge("feedback_intent_classify", "pattern_retrieve")
        self._sg.add_edge("pattern_retrieve", "design_synthesize")
        self._sg.add_edge("design_synthesize", END)

    def route(self, state: AgentState) -> str:
        """Required by the BaseGraph ABC. Linear topology → not wired to a conditional edge."""
        if state.get("error_code") or state.get("retrieval_hit_count", 0) == 0:
            return "design_synthesize"
        return "pattern_retrieve"

    def get_output(self, state: AgentState) -> dict[str, Any]:
        return {
            "output": state.get("result"),
            "status": state.get("status"),
            "retrieval_hit_count": state.get("retrieval_hit_count", 0),
            "error_code": state.get("error_code"),
            "trace_id": state.get("trace_id"),
            "correlation_id": state.get("correlation_id"),
            "node_history": state.get("node_history", []),
        }
