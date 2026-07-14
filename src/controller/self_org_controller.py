from __future__ import annotations

import random
from typing import Any

from src.agents.base_agent import Agent
from src.controller.routing import choose_agent
from src.controller.task_pool import code_repair_subtasks
from src.eval.code_eval import evaluate_code
from src.utils.logging import TrajectoryLogger


class SelfOrgController:
    def __init__(
        self,
        agents: list[Agent],
        logger: TrajectoryLogger,
        *,
        mode: str = "free",
        seed: int = 0,
        loaded_assets: dict[str, Any] | None = None,
        reuse_strategy: str = "none",
        evaluation_timeout_sec: float = 5.0,
    ):
        self.agents = agents
        self.logger = logger
        self.mode = mode
        self.loaded_assets = loaded_assets or {}
        if reuse_strategy not in {"none", "prompt", "routing", "full"}:
            raise ValueError(f"Unsupported reuse strategy: {reuse_strategy}")
        self.reuse_strategy = reuse_strategy
        self.evaluation_timeout_sec = evaluation_timeout_sec
        self.rng = random.Random(seed)
        self.fixed_roles = {
            "localize": "A1",
            "patch": "A2",
            "review": "A3",
        }
        self.asset_roles = {
            asset["specialty"]: asset["agent_id"]
            for asset in self.loaded_assets.get("role_assets", [])
            if asset.get("specialty") and asset.get("agent_id")
        }

    @property
    def uses_prompt_assets(self) -> bool:
        return self.reuse_strategy in {"prompt", "full"}

    @property
    def uses_asset_routing(self) -> bool:
        return self.reuse_strategy in {"routing", "full"}

    def run_code_task(self, task: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = {
            "buggy_code": task["buggy_code"],
            "assets": self.loaded_assets if self.uses_prompt_assets else {},
        }
        subtask_outputs: dict[str, str] = {}
        assigned_agents: dict[str, Agent] = {}

        self.logger.log_event(
            {
                "event_type": "task_started",
                "task_id": task["task_id"],
                "task_family": task.get("task_family"),
                "mode": self.mode,
                "reuse_strategy": self.reuse_strategy,
            }
        )

        for subtask_type in code_repair_subtasks():
            preferred_agent_id = self.asset_roles.get(subtask_type) if self.uses_asset_routing else None
            agent = choose_agent(
                self.agents,
                subtask_type,
                mode=self.mode,
                fixed_roles=self.fixed_roles,
                preferred_agent_id=preferred_agent_id,
                rng=self.rng,
            )
            response = agent.run_subtask(subtask_type, task, context)
            output = response.text
            assigned_agents[subtask_type] = agent
            subtask_outputs[subtask_type] = output
            context[subtask_type] = output
            if subtask_type == "patch":
                context["candidate_code"] = output

            self.logger.log_event(
                {
                    "event_type": "subtask_completed",
                    "task_id": task["task_id"],
                    "agent_id": agent.agent_id,
                    "subtask_type": subtask_type,
                    "output": output,
                    "mode": self.mode,
                    "reuse_strategy": self.reuse_strategy,
                    "routing_source": "asset" if preferred_agent_id == agent.agent_id else self.mode,
                    "used_prompt_assets": self.uses_prompt_assets and bool(self.loaded_assets),
                    "llm_metadata": response.metadata,
                }
            )

        candidate_code = subtask_outputs.get("patch", task["buggy_code"])
        eval_result = evaluate_code(task, candidate_code, timeout_sec=self.evaluation_timeout_sec)
        success = bool(eval_result["success"])

        for subtask_type, agent in assigned_agents.items():
            agent.update_history(subtask_type, success)

        result = {
            "task_id": task["task_id"],
            "success": success,
            "eval": eval_result,
            "subtask_outputs": subtask_outputs,
        }

        self.logger.log_event(
            {
                "event_type": "task_finished",
                "task_id": task["task_id"],
                "success": success,
                "eval": eval_result,
            }
        )
        return result
