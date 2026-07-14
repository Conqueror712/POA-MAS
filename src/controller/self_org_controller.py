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
    ):
        self.agents = agents
        self.logger = logger
        self.mode = mode
        self.loaded_assets = loaded_assets or {}
        self.rng = random.Random(seed)
        self.fixed_roles = {
            "localize": "A1",
            "patch": "A2",
            "review": "A3",
        }

    def run_code_task(self, task: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = {
            "buggy_code": task["buggy_code"],
            "assets": self.loaded_assets,
        }
        subtask_outputs: dict[str, str] = {}
        assigned_agents: dict[str, Agent] = {}

        self.logger.log_event(
            {
                "event_type": "task_started",
                "task_id": task["task_id"],
                "task_family": task.get("task_family"),
                "mode": self.mode,
            }
        )

        for subtask_type in code_repair_subtasks():
            agent = choose_agent(
                self.agents,
                subtask_type,
                mode=self.mode,
                fixed_roles=self.fixed_roles,
                rng=self.rng,
            )
            output = agent.run_subtask(subtask_type, task, context)
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
                    "used_assets": bool(self.loaded_assets),
                }
            )

        candidate_code = subtask_outputs.get("patch", task["buggy_code"])
        eval_result = evaluate_code(task, candidate_code)
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
