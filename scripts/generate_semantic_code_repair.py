from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.code_eval import evaluate_code


SPLIT_FAMILIES = {
    "train": ["sum_even", "safe_max", "palindrome", "flatten_once", "word_counts"],
    "test": ["clamp", "factorial", "fizz_buzz", "dedupe_ordered", "merge_counts"],
    "shifted_test": ["first_index", "average", "rotate_right", "count_vowels", "normalize_spaces"],
}
SOURCE_SPLITS = ("train", "test", "shifted_test")


def load_source(path: Path) -> dict[str, dict[str, object]]:
    tasks = json.loads(path.read_text(encoding="utf-8"))
    return {str(task["task_id"]): task for task in tasks}


def build_tasks(source: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for split, families in SPLIT_FAMILIES.items():
        for family in families:
            for variant, source_split in enumerate(SOURCE_SPLITS, start=1):
                original = source[f"expanded_{source_split}_{family}"]
                original_name = str(original["entry_point"])
                entry_point = f"{family}_{split}_{variant}"
                replace_name = lambda text: text.replace(original_name, entry_point)
                tasks.append(
                    {
                        "task_id": f"semantic_{split}_{family}_{variant}",
                        "split": split,
                        "repair_family": family,
                        "task_family": "code_repair",
                        "difficulty": "medium" if split == "shifted_test" else "easy",
                        "description": str(original["description"]),
                        "buggy_code": replace_name(str(original["buggy_code"])),
                        "entry_point": entry_point,
                        "tests": [replace_name(str(test)) for test in original["tests"]],
                        "reference_solution": replace_name(str(original["reference_solution"])),
                    }
                )
    return tasks


def validate(tasks: list[dict[str, object]]) -> None:
    families_by_split = {
        split: {str(task["repair_family"]) for task in tasks if task["split"] == split}
        for split in SPLIT_FAMILIES
    }
    for first, second in (("train", "test"), ("train", "shifted_test"), ("test", "shifted_test")):
        overlap = families_by_split[first] & families_by_split[second]
        if overlap:
            raise ValueError(f"Repair-family leakage between {first} and {second}: {sorted(overlap)}")
    failures = [str(task["task_id"]) for task in tasks if not evaluate_code(task, str(task["reference_solution"]))["success"]]
    undetected = [str(task["task_id"]) for task in tasks if evaluate_code(task, str(task["buggy_code"]))["success"]]
    if failures or undetected:
        raise ValueError({"reference_failures": failures, "undetected_bugs": undetected})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate semantic-family-disjoint code-repair splits.")
    parser.add_argument("--source", default="data/tasks_code/expanded_code_repair.json")
    parser.add_argument("--output", default="data/tasks_code/semantic_code_repair.json")
    args = parser.parse_args()

    tasks = build_tasks(load_source(Path(args.source)))
    validate(tasks)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "num_tasks": len(tasks), "families": SPLIT_FAMILIES}, indent=2))


if __name__ == "__main__":
    main()
