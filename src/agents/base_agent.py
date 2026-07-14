from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.llm_client import DeepSeekClient, MockLLMClient


@dataclass
class Agent:
    agent_id: str
    llm_client: MockLLMClient | DeepSeekClient
    history: dict[str, list[bool]] = field(default_factory=dict)

    def success_rate(self, subtask_type: str) -> float:
        outcomes = self.history.get(subtask_type, [])
        if not outcomes:
            return 0.5
        return sum(outcomes) / len(outcomes)

    def run_subtask(self, subtask_type: str, task: dict[str, Any], context: dict[str, Any]) -> str:
        response = self.llm_client.complete(
            agent_id=self.agent_id,
            subtask_type=subtask_type,
            task=task,
            context=context,
        )
        return response.text

    def update_history(self, subtask_type: str, success: bool) -> None:
        self.history.setdefault(subtask_type, []).append(success)
