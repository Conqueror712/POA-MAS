from __future__ import annotations

from collections import Counter, defaultdict
from math import log
from typing import Any


def success_rate(results: list[dict[str, Any]]) -> float:
    if not results:
        return 0.0
    return sum(1 for item in results if item.get("success")) / len(results)


def specialization_index(events: list[dict[str, Any]]) -> float:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    subtask_types: set[str] = set()
    for event in events:
        if event.get("event_type") != "subtask_completed":
            continue
        agent_id = event["agent_id"]
        subtask_type = event["subtask_type"]
        counts[agent_id][subtask_type] += 1
        subtask_types.add(subtask_type)

    if not counts or len(subtask_types) <= 1:
        return 0.0

    max_entropy = log(len(subtask_types))
    scores: list[float] = []
    for sub_counts in counts.values():
        total = sum(sub_counts.values())
        entropy = 0.0
        for value in sub_counts.values():
            p = value / total
            entropy -= p * log(p)
        scores.append(1 - entropy / max_entropy)
    return sum(scores) / len(scores)


def task_overlap_rate(events: list[dict[str, Any]], num_agents: int) -> float:
    agents_by_subtask: dict[str, set[str]] = defaultdict(set)
    for event in events:
        if event.get("event_type") == "subtask_completed":
            agents_by_subtask[event["subtask_type"]].add(event["agent_id"])

    if not agents_by_subtask or num_agents <= 1:
        return 0.0

    overlaps = [(len(agent_ids) - 1) / (num_agents - 1) for agent_ids in agents_by_subtask.values()]
    return sum(overlaps) / len(overlaps)


def usage_metrics(events: list[dict[str, Any]]) -> dict[str, int]:
    subtask_events = [event for event in events if event.get("event_type") == "subtask_completed"]
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    for event in subtask_events:
        usage = event.get("llm_metadata", {}).get("usage", {})
        prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
        completion_tokens += int(usage.get("completion_tokens", 0) or 0)
        total_tokens += int(usage.get("total_tokens", 0) or 0)
    return {
        "llm_calls": len(subtask_events),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def asset_routing_rate(events: list[dict[str, Any]]) -> float:
    subtask_events = [event for event in events if event.get("event_type") == "subtask_completed"]
    if not subtask_events:
        return 0.0
    return sum(event.get("routing_source") == "asset" for event in subtask_events) / len(subtask_events)

