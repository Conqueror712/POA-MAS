from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_game_summaries(run_dirs: list[str | Path]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        path = Path(run_dir) / "summary.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing game summary: {path}")
        summary = json.loads(path.read_text(encoding="utf-8"))
        if summary.get("domain") == "game_theory":
            summaries.append(summary)
    return summaries


def extract_game_strategy_assets(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Heuristically distill strategy assets from cooperative source runs."""

    by_game: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        if summary.get("task_split") != "train":
            continue
        by_game[str(summary.get("game_type"))].append(summary)

    assets: list[dict[str, Any]] = []
    for game_type, group in sorted(by_game.items()):
        total_coop = 0.0
        total_invalid = 0.0
        evidence: list[str] = []
        first_round_coop = 0
        first_round_total = 0
        reciprocal_rounds = 0
        reciprocal_total = 0

        for summary in group:
            evidence.append(f"{summary.get('run_name')}:{summary.get('task_id')}")
            metrics = summary.get("metrics", {})
            total_coop += float(metrics.get("cooperation_rate", 0.0))
            total_invalid += float(metrics.get("invalid_action_rate", 0.0))
            rounds = summary.get("result", {}).get("rounds", [])
            if rounds:
                first_actions = list(rounds[0].get("actions", {}).values())
                first_round_total += len(first_actions)
                first_round_coop += sum(1 for action in first_actions if is_cooperative(game_type, action))
            for prev_round, cur_round in zip(rounds, rounds[1:]):
                prev_actions = prev_round.get("actions", {})
                cur_actions = cur_round.get("actions", {})
                for agent_id, action in cur_actions.items():
                    peer_actions = [
                        peer_action for peer_id, peer_action in prev_actions.items()
                        if peer_id != agent_id
                    ]
                    if not peer_actions:
                        continue
                    peer_coop_rate = sum(1 for peer_action in peer_actions if is_cooperative(game_type, peer_action)) / len(peer_actions)
                    if peer_coop_rate >= 0.5:
                        reciprocal_total += 1
                        reciprocal_rounds += int(is_cooperative(game_type, action))

        count = len(group)
        avg_coop = total_coop / count if count else 0.0
        avg_invalid = total_invalid / count if count else 0.0
        first_rate = first_round_coop / first_round_total if first_round_total else 0.0
        reciprocity_rate = reciprocal_rounds / reciprocal_total if reciprocal_total else 0.0

        legal_actions = "C or D" if game_type == "iterated_prisoners_dilemma" else "CONTRIBUTE or KEEP"
        assets.append({
            "asset_type": "strategy",
            "task_family": "game_theory",
            "game_type": game_type,
            "name": "legal_action_protocol",
            "trigger_condition": f"When playing {game_type}, return exactly one legal action token.",
            "recommended_actions": [f"Use only these legal actions: {legal_actions}."],
            "evidence": evidence,
            "confidence": round(max(0.0, 1.0 - avg_invalid), 4),
            "metadata": {
                "source": "trajectory-derived game extractor",
                "avg_invalid_action_rate": round(avg_invalid, 4),
            },
        })

        if first_rate >= 0.5:
            assets.append({
                "asset_type": "strategy",
                "task_family": "game_theory",
                "game_type": game_type,
                "name": "cooperative_opening",
                "trigger_condition": f"When a repeated {game_type} starts and no history is available.",
                "recommended_actions": [cooperative_action(game_type)],
                "evidence": evidence,
                "confidence": round(first_rate, 4),
                "metadata": {
                    "source": "trajectory-derived game extractor",
                    "first_round_cooperation_rate": round(first_rate, 4),
                },
            })

        if reciprocity_rate >= 0.5:
            assets.append({
                "asset_type": "strategy",
                "task_family": "game_theory",
                "game_type": game_type,
                "name": "reciprocal_cooperation",
                "trigger_condition": "When most peers cooperated in the previous round.",
                "recommended_actions": [
                    "Continue cooperation after cooperative peer behavior.",
                    "Avoid switching to defection unless the recent group behavior collapses.",
                ],
                "evidence": evidence,
                "confidence": round(reciprocity_rate, 4),
                "metadata": {
                    "source": "trajectory-derived game extractor",
                    "conditional_cooperation_rate": round(reciprocity_rate, 4),
                },
            })

        if game_type == "public_goods" and avg_coop >= 0.5:
            assets.append({
                "asset_type": "strategy",
                "task_family": "game_theory",
                "game_type": game_type,
                "name": "public_goods_welfare_preservation",
                "trigger_condition": "When repeated public-goods interaction rewards group contribution.",
                "recommended_actions": [
                    "Contribute early to maintain group welfare.",
                    "Keep contributing while at least half of the group contributed recently.",
                ],
                "evidence": evidence,
                "confidence": round(avg_coop, 4),
                "metadata": {
                    "source": "trajectory-derived game extractor",
                    "avg_cooperation_rate": round(avg_coop, 4),
                },
            })

    return assets


def is_cooperative(game_type: str, action: str) -> bool:
    if game_type == "iterated_prisoners_dilemma":
        return action == "C"
    if game_type == "public_goods":
        return action == "CONTRIBUTE"
    return False


def cooperative_action(game_type: str) -> str:
    if game_type == "iterated_prisoners_dilemma":
        return "Start with C when repeated interaction is expected."
    if game_type == "public_goods":
        return "Start with CONTRIBUTE when repeated interaction is expected."
    return "Start with a legal cooperative action when available."
