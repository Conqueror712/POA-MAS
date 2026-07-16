from __future__ import annotations

import argparse
import ast
import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.code_eval import evaluate_code


SPLITS = {
    "train": ("train", {"introductory"}),
    "test": ("test", {"introductory"}),
    "shifted_test": ("test", {"interview"}),
}


class MutateFirst(ast.NodeTransformer):
    def __init__(self, kind: str):
        self.kind = kind
        self.done = False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        node = self.generic_visit(node)
        options = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.LtE: ast.Gt, ast.Gt: ast.LtE, ast.GtE: ast.Lt}
        if self.kind == "compare" and not self.done:
            for index, operator in enumerate(node.ops):
                if replacement := options.get(type(operator)):
                    node.ops[index] = replacement()
                    self.done = True
                    break
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        node = self.generic_visit(node)
        options = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv}
        if self.kind == "binary" and not self.done and (replacement := options.get(type(node.op))):
            node.op = replacement()
            self.done = True
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if self.kind == "integer" and not self.done and isinstance(node.value, int) and not isinstance(node.value, bool):
            node.value += 1 if node.value >= 0 else -1
            self.done = True
        return node


def task_from_problem(problem: Path, split: str, source_split: str, timeout_sec: float) -> dict[str, object] | None:
    try:
        metadata = json.loads((problem / "metadata.json").read_text(encoding="utf-8"))
        io = json.loads((problem / "input_output.json").read_text(encoding="utf-8"))
        solutions = json.loads((problem / "solutions.json").read_text(encoding="utf-8"))
        question = (problem / "question.txt").read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        return None
    inputs, outputs = io.get("inputs", []), io.get("outputs", [])
    if not inputs or len(inputs) != len(outputs) or not all(isinstance(value, str) for value in [*inputs, *outputs]):
        return None
    base = {"evaluation_mode": "stdin_stdout", "inputs": inputs, "outputs": outputs, "tests": []}
    for solution in solutions:
        if not isinstance(solution, str) or not evaluate_code(base, solution, timeout_sec)["success"]:
            continue
        try:
            tree = ast.parse(solution)
        except SyntaxError:
            continue
        for mutation in ("compare", "binary", "integer"):
            transformer = MutateFirst(mutation)
            mutant = transformer.visit(copy.deepcopy(tree))
            if not transformer.done:
                continue
            buggy_code = ast.unparse(ast.fix_missing_locations(mutant)) + "\n"
            if not evaluate_code(base, buggy_code, timeout_sec)["success"]:
                return {
                    **base,
                    "task_id": f"apps_{split}_{source_split}_{problem.name}",
                    "split": split,
                    "task_family": "apps_repair",
                    "repair_family": f"{source_split}/{problem.name}",
                    "source_problem_id": f"{source_split}/{problem.name}",
                    "public_source": "hendrycks/apps",
                    "difficulty": metadata.get("difficulty"),
                    "description": question,
                    "entry_point": "stdin_stdout",
                    "buggy_code": buggy_code,
                    "reference_solution": solution,
                    "mutation": mutation,
                }
    return None


def collect(root: Path, split: str, count: int, timeout_sec: float) -> list[dict[str, object]]:
    source_split, allowed = SPLITS[split]
    tasks = []
    for problem in sorted((root / source_split).iterdir()):
        metadata_path = problem / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            if json.loads(metadata_path.read_text(encoding="utf-8")).get("difficulty") not in allowed:
                continue
        except json.JSONDecodeError:
            continue
        if task := task_from_problem(problem, split, source_split, timeout_sec):
            tasks.append(task)
        if len(tasks) == count:
            return tasks
    raise ValueError(f"Only found {len(tasks)} validated APPS tasks for {split}; need {count}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local APPS code-repair benchmark.")
    parser.add_argument("--apps-root", default="data/public/APPS")
    parser.add_argument("--output", default="data/tasks_code/apps_repair.json")
    parser.add_argument("--train-count", type=int, default=20)
    parser.add_argument("--test-count", type=int, default=20)
    parser.add_argument("--shifted-count", type=int, default=15)
    parser.add_argument("--case-timeout", type=float, default=2.0)
    args = parser.parse_args()

    root = Path(args.apps_root)
    tasks = []
    for split, count in (("train", args.train_count), ("test", args.test_count), ("shifted_test", args.shifted_count)):
        tasks.extend(collect(root, split, count, args.case_timeout))
    source_ids = [task["source_problem_id"] for task in tasks]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("APPS source problems overlap across splits.")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "split_counts": {split: sum(task["split"] == split for task in tasks) for split in SPLITS}}, indent=2))


if __name__ == "__main__":
    main()
