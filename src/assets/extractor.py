from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.assets.schema import OrganizationAsset, RoleAsset


def load_events(run_dir: str | Path) -> list[dict[str, Any]]:
    events_path = Path(run_dir) / "events.jsonl"
    events: list[dict[str, Any]] = []
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def extract_assets(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    successful_tasks = {
        event["task_id"]
        for event in events
        if event.get("event_type") == "task_finished" and event.get("success")
    }
    subtask_counts: dict[str, Counter[str]] = defaultdict(Counter)
    task_family_by_task: dict[str, str] = {}

    for event in events:
        if event.get("event_type") == "task_started":
            task_family_by_task[event["task_id"]] = event.get("task_family", "unknown")
        if event.get("event_type") != "subtask_completed":
            continue
        if event["task_id"] not in successful_tasks:
            continue
        subtask_counts[event["agent_id"]][event["subtask_type"]] += 1

    role_assets = []
    for agent_id, counts in subtask_counts.items():
        if not counts:
            continue
        specialty, count = counts.most_common(1)[0]
        confidence = count / sum(counts.values())
        role_assets.append(
            RoleAsset(
                asset_type="role",
                agent_id=agent_id,
                task_family="code_repair",
                specialty=specialty,
                trigger_condition=f"When a code repair task needs {specialty}.",
                recommended_actions=[
                    f"Prioritize {specialty} subtasks for {agent_id}.",
                    "Use successful prior traces as style examples.",
                ],
                failure_patterns=["Avoid broad rewrites unless tests require them."],
                evidence=sorted(successful_tasks),
                confidence=round(confidence, 4),
            ).to_dict()
        )

    org_assets = [
        OrganizationAsset(
            asset_type="organization",
            task_family="code_repair",
            decomposition=["localize", "patch", "review"],
            routing_rule=[
                "Route each subtask to the agent with the highest historical success rate.",
                "Keep review separate from patching when enough agents are available.",
            ],
            communication_protocol=[
                "Share localization before patching.",
                "Share candidate patch before review.",
            ],
            conflict_resolution=[
                "Prefer the candidate that passes executable tests.",
                "If no candidate passes, reopen localization.",
            ],
            evidence=sorted(successful_tasks),
            confidence=1.0 if successful_tasks else 0.0,
            metadata={"source": "phase-1 deterministic extractor"},
        ).to_dict()
    ]

    return role_assets, org_assets

