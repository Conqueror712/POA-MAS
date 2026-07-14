from __future__ import annotations

import random

from src.agents.base_agent import Agent


def choose_agent(
    agents: list[Agent],
    subtask_type: str,
    *,
    mode: str,
    fixed_roles: dict[str, str] | None = None,
    preferred_agent_id: str | None = None,
    rng: random.Random | None = None,
) -> Agent:
    if not agents:
        raise ValueError("Cannot choose agent from an empty team.")

    if preferred_agent_id:
        for agent in agents:
            if agent.agent_id == preferred_agent_id:
                return agent

    if mode == "manual" and fixed_roles:
        target_id = fixed_roles.get(subtask_type)
        for agent in agents:
            if agent.agent_id == target_id:
                return agent

    if mode == "random":
        if rng is None:
            rng = random.Random()
        return rng.choice(agents)

    best_rate = max(agent.success_rate(subtask_type) for agent in agents)
    candidates = [agent for agent in agents if agent.success_rate(subtask_type) == best_rate]
    candidates = sorted(candidates, key=lambda agent: agent.agent_id)
    if len(candidates) == 1:
        return candidates[0]

    # Stable tie-break: agents self-select different task types before history exists.
    tie_index = sum(ord(char) for char in subtask_type) % len(candidates)
    return candidates[tie_index]
