"""Minimal multi-hop planning helper for Week08.

This intentionally returns a plan, not an agent loop. Full iterative retrieval
belongs to a later production hardening step.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class MultiHopPlan:
    query: str
    max_hops: int
    steps: list[str]
    deferred_reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_multi_hop_plan(query: str, max_hops: int = 2) -> MultiHopPlan:
    return MultiHopPlan(
        query=query,
        max_hops=max_hops,
        steps=[
            "retrieve_initial_evidence",
            "evaluate_answerability",
            "rewrite_follow_up_if_needed",
        ][: max(1, min(max_hops + 1, 3))],
        deferred_reason="runtime_agent_loop_deferred_after_week08_student_core",
    )

