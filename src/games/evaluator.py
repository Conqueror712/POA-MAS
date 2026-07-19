from __future__ import annotations

from collections import Counter
from typing import Any


PD_ACTIONS = {"C", "D"}
PG_ACTIONS = {"CONTRIBUTE", "KEEP"}


def parse_action(game_type: str, text: str) -> tuple[str, bool]:
    value = text.strip().upper()
    if game_type == "iterated_prisoners_dilemma":
        if "COOPERATE" in value or value == "C":
            return "C", True
        if "DEFECT" in value or value == "D":
            return "D", True
        return "D", False
    if game_type == "public_goods":
        if "CONTRIBUTE" in value or value in {"C", "COOPERATE"}:
            return "CONTRIBUTE", True
        if "KEEP" in value or "DEFECT" in value or value == "D":
            return "KEEP", True
        return "KEEP", False
    raise ValueError(f"Unsupported game_type: {game_type}")


def normalize_action(game_type: str, text: str) -> str:
    action, _ = parse_action(game_type, text)
    return action


def score_round(task: dict[str, Any], actions: dict[str, str]) -> dict[str, Any]:
    game_type = task["game_type"]
    if game_type == "iterated_prisoners_dilemma":
        return score_prisoners_dilemma(actions)
    if game_type == "public_goods":
        return score_public_goods(task, actions)
    raise ValueError(f"Unsupported game_type: {game_type}")


def score_prisoners_dilemma(actions: dict[str, str]) -> dict[str, Any]:
    if len(actions) != 2:
        raise ValueError("Prisoner's Dilemma requires exactly two players.")
    players = sorted(actions)
    a1, a2 = actions[players[0]], actions[players[1]]
    if a1 not in PD_ACTIONS or a2 not in PD_ACTIONS:
        raise ValueError(f"Invalid Prisoner's Dilemma actions: {actions}")
    payoff_matrix = {
        ("C", "C"): (3.0, 3.0),
        ("C", "D"): (0.0, 5.0),
        ("D", "C"): (5.0, 0.0),
        ("D", "D"): (1.0, 1.0),
    }
    p1, p2 = payoff_matrix[(a1, a2)]
    return {
        "payoffs": {players[0]: p1, players[1]: p2},
        "cooperative_actions": sum(1 for action in actions.values() if action == "C"),
        "total_actions": 2,
        "social_welfare": p1 + p2,
        "nash_deviation_actions": sum(1 for action in actions.values() if action == "C"),
    }


def score_public_goods(task: dict[str, Any], actions: dict[str, str]) -> dict[str, Any]:
    endowment = float(task.get("endowment", 10))
    multiplier = float(task.get("multiplier", 1.6))
    if any(action not in PG_ACTIONS for action in actions.values()):
        raise ValueError(f"Invalid public-goods actions: {actions}")
    contributions = {
        player: endowment if action == "CONTRIBUTE" else 0.0
        for player, action in actions.items()
    }
    pool_return = multiplier * sum(contributions.values()) / len(actions)
    payoffs = {
        player: endowment - contribution + pool_return
        for player, contribution in contributions.items()
    }
    return {
        "payoffs": payoffs,
        "cooperative_actions": sum(1 for action in actions.values() if action == "CONTRIBUTE"),
        "total_actions": len(actions),
        "social_welfare": sum(payoffs.values()),
        "nash_deviation_actions": sum(1 for action in actions.values() if action == "CONTRIBUTE"),
    }


def summarize_game_results(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    total_actions = 0
    cooperative_actions = 0
    nash_deviation_actions = 0
    social_welfare = 0.0
    payoff_total = 0.0
    payoff_count = 0
    action_counts: Counter[str] = Counter()
    invalid_actions = 0

    for result in task_results:
        for round_result in result["rounds"]:
            scores = round_result["scores"]
            total_actions += int(scores["total_actions"])
            cooperative_actions += int(scores["cooperative_actions"])
            nash_deviation_actions += int(scores["nash_deviation_actions"])
            social_welfare += float(scores["social_welfare"])
            action_counts.update(round_result["actions"].values())
            invalid_actions += sum(1 for valid in round_result.get("action_valid", {}).values() if not valid)
            for payoff in scores["payoffs"].values():
                payoff_total += float(payoff)
                payoff_count += 1

    return {
        "cooperation_rate": cooperative_actions / total_actions if total_actions else 0.0,
        "nash_deviation_rate": nash_deviation_actions / total_actions if total_actions else 0.0,
        "invalid_action_rate": invalid_actions / total_actions if total_actions else 0.0,
        "average_payoff": payoff_total / payoff_count if payoff_count else 0.0,
        "social_welfare": social_welfare,
        "action_counts": dict(sorted(action_counts.items())),
    }
