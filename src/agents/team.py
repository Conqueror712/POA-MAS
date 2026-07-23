from __future__ import annotations

from src.agents.base_agent import Agent
from src.utils.llm_client import LLMClient


def build_team(num_agents: int, llm_client: LLMClient) -> list[Agent]:
    return [Agent(agent_id=f"A{i + 1}", llm_client=llm_client) for i in range(num_agents)]
