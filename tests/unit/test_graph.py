# CMN-C2-680 — Unit Tests: Cat 2 graph wiring (outer GraphNode + inner workflow)

import pytest

from src.graph.domain_workflow_graph import FeedbackTriageWorkflow
from src.graph.graph import (
    FeedbackTriageWorkflowGraphNode,
    Graph,
    HumanFeedbackTriageLearningLoopDesignAgent,
)
from src.schemas.state import State


class TestOuterGraph:
    def test_registry_alias(self):
        assert HumanFeedbackTriageLearningLoopDesignAgent is Graph

    def test_name_and_state_schema(self):
        g = Graph()
        assert g.name == "HumanFeedbackTriageLearningLoopDesignAgent"
        assert g.state_schema is State

    def test_main_slot_is_graphnode(self):
        g = Graph()
        g.register_nodes()
        assert isinstance(g._nodes["main"], FeedbackTriageWorkflowGraphNode)
        for slot in ("pre_process", "main", "post_process"):
            assert slot in g._nodes

    def test_error_strategy_propagate(self):
        assert FeedbackTriageWorkflowGraphNode.error_strategy == "propagate"

    def test_get_subgraph_is_cached(self):
        node = FeedbackTriageWorkflowGraphNode()
        assert node.get_subgraph() is node.get_subgraph()

    def test_extract_input_prefers_validated(self):
        node = FeedbackTriageWorkflowGraphNode()
        assert node.extract_input({"validated_input": "V", "user_input": "U"}) == "V"

    def test_merge_output_maps_fields(self):
        node = FeedbackTriageWorkflowGraphNode()
        merged = node.merge_output({}, {"output": '{"x":1}', "retrieval_hit_count": 3, "status": "success",
                                        "error_code": None})
        assert merged["result"] == '{"x":1}' and merged["retrieval_hit_count"] == 3


class TestInnerWorkflow:
    def test_inner_registers_three_nodes(self):
        wf = FeedbackTriageWorkflow(config={})
        wf.register_nodes()
        for slot in ("feedback_intent_classify", "pattern_retrieve", "design_synthesize"):
            assert slot in wf._nodes

    def test_inner_name_and_state_schema(self):
        wf = FeedbackTriageWorkflow(config={})
        assert wf.name == "FeedbackTriageWorkflow"
        assert wf.state_schema is State
        assert wf._validate_config() is None

    def test_route_zero_hit_to_synthesize(self):
        wf = FeedbackTriageWorkflow(config={})
        assert wf.route({"retrieval_hit_count": 0}) == "design_synthesize"

    def test_route_hits_to_retrieve(self):
        wf = FeedbackTriageWorkflow(config={})
        assert wf.route({"retrieval_hit_count": 2}) == "pattern_retrieve"

    def test_get_output_surfaces_result(self):
        wf = FeedbackTriageWorkflow(config={})
        out = wf.get_output({"result": "R", "status": "success", "retrieval_hit_count": 1})
        assert out["output"] == "R" and out["retrieval_hit_count"] == 1


class TestServerModule:
    def test_server_imports(self):
        try:
            import src.api.server as server
        except ModuleNotFoundError as exc:
            pytest.skip(f"platform module unavailable in the local stub env: {exc}")
        assert server.app is not None and server.agent is not None
