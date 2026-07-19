from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from src.agents.team import build_team
from src.controller.self_org_controller import SelfOrgController
from src.controller.task_pool import load_tasks
from src.eval.code_eval import evaluate_code
from src.eval.metrics import asset_routing_rate, usage_metrics
from src.games.evaluator import score_public_goods, score_round, summarize_game_results
from src.utils.llm_client import MockLLMClient
from src.utils.logging import TrajectoryLogger


ROOT = Path(__file__).resolve().parents[1]


class ExperimentFeatureTests(unittest.TestCase):
    def test_semantic_splits_have_disjoint_repair_families(self) -> None:
        tasks = json.loads((ROOT / "data/tasks_code/semantic_code_repair.json").read_text(encoding="utf-8"))
        families = {
            split: {task["repair_family"] for task in tasks if task["split"] == split}
            for split in ("train", "test", "shifted_test")
        }
        self.assertEqual({split: len(items) for split, items in families.items()}, {
            "train": 5,
            "test": 5,
            "shifted_test": 5,
        })
        self.assertFalse(families["train"] & families["test"])
        self.assertFalse(families["train"] & families["shifted_test"])
        self.assertFalse(families["test"] & families["shifted_test"])

    def test_humaneval_splits_have_disjoint_public_sources(self) -> None:
        tasks = json.loads((ROOT / "data/tasks_code/humaneval_repair.json").read_text(encoding="utf-8"))
        sources = {
            split: {task["source_task_id"] for task in tasks if task["split"] == split}
            for split in ("train", "test", "shifted_test")
        }
        self.assertEqual({split: len(items) for split, items in sources.items()}, {
            "train": 15,
            "test": 15,
            "shifted_test": 15,
        })
        self.assertFalse(sources["train"] & sources["test"])
        self.assertFalse(sources["train"] & sources["shifted_test"])
        self.assertFalse(sources["test"] & sources["shifted_test"])

    def test_full_reuse_routes_from_role_assets(self) -> None:
        task = load_tasks(ROOT / "data/tasks_code/semantic_code_repair.json", limit=1, split="test")[0]
        assets = {
            "role_assets": [
                {"specialty": "localize", "agent_id": "A2"},
                {"specialty": "patch", "agent_id": "A3"},
                {"specialty": "review", "agent_id": "A4"},
            ]
        }
        tmp_root = ROOT / ".tmp_tests"
        tmp_root.mkdir(exist_ok=True)
        output_root = tmp_root / f"reuse_{uuid.uuid4().hex}"
        logger = TrajectoryLogger(output_root, "reuse")
        controller = SelfOrgController(
            build_team(4, MockLLMClient()),
            logger,
            loaded_assets=assets,
            reuse_strategy="full",
        )
        result = controller.run_code_task(task)
        events = [json.loads(line) for line in logger.events_path.read_text(encoding="utf-8").splitlines()]

        self.assertTrue(result["success"])
        assignments = [event for event in events if event["event_type"] == "subtask_completed"]
        self.assertEqual([event["agent_id"] for event in assignments], ["A2", "A3", "A4"])
        self.assertEqual(asset_routing_rate(events), 1.0)
        self.assertTrue(all(event["used_prompt_assets"] for event in assignments))

    def test_usage_metrics_aggregate_api_metadata(self) -> None:
        events = [
            {"event_type": "subtask_completed", "routing_source": "asset", "llm_metadata": {"usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}}},
            {"event_type": "subtask_completed", "routing_source": "free", "llm_metadata": {"usage": {"prompt_tokens": 2, "completion_tokens": 5, "total_tokens": 7}}},
        ]
        self.assertEqual(usage_metrics(events), {
            "llm_calls": 2,
            "prompt_tokens": 5,
            "completion_tokens": 9,
            "total_tokens": 14,
        })
        self.assertEqual(asset_routing_rate(events), 0.5)

    def test_code_evaluation_times_out(self) -> None:
        task = {
            "tests": ["assert loop() == 1"],
        }
        result = evaluate_code(task, "def loop():\n    while True:\n        pass\n", timeout_sec=0.1)
        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])

    def test_stdio_evaluation_normalizes_whitespace(self) -> None:
        task = {
            "evaluation_mode": "stdin_stdout",
            "inputs": ["2 3\n"],
            "outputs": ["5\n"],
        }
        result = evaluate_code(task, "a, b = map(int, input().split())\nprint(a + b)\n", timeout_sec=1)
        self.assertTrue(result["success"])

    def test_prisoners_dilemma_payoffs(self) -> None:
        task = {"game_type": "iterated_prisoners_dilemma"}
        result = score_round(task, {"A1": "C", "A2": "D"})
        self.assertEqual(result["payoffs"], {"A1": 0.0, "A2": 5.0})
        self.assertEqual(result["cooperative_actions"], 1)
        self.assertEqual(result["social_welfare"], 5.0)

    def test_public_goods_summary_metrics(self) -> None:
        task = {"game_type": "public_goods", "endowment": 10, "multiplier": 1.6}
        scores = score_public_goods(task, {
            "A1": "CONTRIBUTE",
            "A2": "CONTRIBUTE",
            "A3": "KEEP",
            "A4": "KEEP",
        })
        summary = summarize_game_results([{
            "rounds": [{"actions": {"A1": "CONTRIBUTE", "A2": "CONTRIBUTE", "A3": "KEEP", "A4": "KEEP"}, "scores": scores}]
        }])
        self.assertAlmostEqual(summary["cooperation_rate"], 0.5)
        self.assertAlmostEqual(summary["average_payoff"], 13.0)


if __name__ == "__main__":
    unittest.main()
