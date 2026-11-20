"""Offline end-to-end demo using two deterministic simulators, not real LLMs."""
import json
from aeon_link import (
    LocalPolicy, as_a2a_data_part, as_mcp_tool_result, authorize_task,
    hello, make_ack_result, message, negotiate, verify_ack,
)

source = hello("agent-alpha", "agent-beta")
target = hello("agent-beta", "agent-alpha")
agreement = negotiate(source, target, required_features=["objective.ack.v1"])

task = message("task", "agent-alpha", "agent-beta", {
    "objective": {"id": "network-001", "text": "Assess the connectivity incident", "success_criteria": ["Identify evidence gaps"]},
    "constraints": {"read_only": True, "max_risk": "low"},
    "action": "observe",
    "claims": [
        {"id": "c1", "status": "fact", "text": "DNS query returned an answer", "evidence_ids": ["e1"]},
        {"id": "c2", "status": "hypothesis", "text": "Upstream routing problem", "evidence_ids": []},
    ],
    "evidence": [{"id": "e1", "source_uri": "urn:local:logs:dns-test-001"}],
})
authorize_task(task, LocalPolicy(frozenset({"observe", "propose"}), "agent-alpha"))
result = make_ack_result(task, "agent-beta")
assert verify_ack(task, result)
assert as_a2a_data_part(task)["data"]["aeon_link"] == task
assert as_mcp_tool_result(task)["structuredContent"]["aeon_link"] == task
print(json.dumps({
    "agreement": {"version": agreement.version, "ontology": agreement.ontology, "features": sorted(agreement.features)},
    "task_id": task["message_id"],
    "ack_matches": True,
    "status": result["body"]["status"],
    "network_calls": 0,
    "real_llm_calls": 0,
}, indent=2))
