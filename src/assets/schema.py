from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RoleAsset:
    asset_type: str
    agent_id: str
    task_family: str
    specialty: str
    trigger_condition: str
    recommended_actions: list[str]
    failure_patterns: list[str]
    evidence: list[str]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrganizationAsset:
    asset_type: str
    task_family: str
    decomposition: list[str]
    routing_rule: list[str]
    communication_protocol: list[str]
    conflict_resolution: list[str]
    evidence: list[str]
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

