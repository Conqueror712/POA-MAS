from __future__ import annotations

import argparse
import ast
import copy
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from urllib import request


DEFAULT_URL = "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz"
SPLITS = ("train", "test", "shifted_test")
EVALUATOR = (
    "import json, sys\n"
    "payload = json.load(sys.stdin)\n"
    "namespace = {}\n"
    "exec(payload['candidate_code'], namespace)\n"
    "for test in payload['tests']:\n"
    "    exec(test, namespace)\n"
)


class FirstMutation(ast.NodeTransformer):
    def __init__(self, mutation: str):
        self.mutation = mutation
        self.mutated = False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        node = self.generic_visit(node)
        replacements = {
            ast.Eq: ast.NotEq,
            ast.NotEq: ast.Eq,
            ast.Lt: ast.GtE,
            ast.LtE: ast.Gt,
            ast.Gt: ast.LtE,
            ast.GtE: ast.Lt,
        }
        if self.mutation == "compare" and not self.mutated:
            for index, operator in enumerate(node.ops):
                replacement = replacements.get(type(operator))
                if replacement:
                    node.ops[index] = replacement()
                    self.mutated = True
                    break
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        node = self.generic_visit(node)
        if self.mutation == "boolean" and not self.mutated:
            if isinstance(node.op, ast.And):
                node.op = ast.Or()
                self.mutated = True
            elif isinstance(node.op, ast.Or):
                node.op = ast.And()
                self.mutated = True
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        node = self.generic_visit(node)
        replacements = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv}
        if self.mutation == "binary" and not self.mutated:
            replacement = replacements.get(type(node.op))
            if replacement:
                node.op = replacement()
                self.mutated = True
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if self.mutation == "integer" and not self.mutated and isinstance(node.value, int) and not isinstance(node.value, bool):
            node.value = node.value + 1 if node.value >= 0 else node.value - 1
            self.mutated = True
        return node


def cache_source(url: str, cache_path: Path, refresh: bool) -> bytes:
    if refresh or not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(request.urlopen(url, timeout=60).read())
    return cache_path.read_bytes()


def build_tests(record: dict[str, str]) -> list[str]:
    return [f"{record['test']}\ncheck({record['entry_point']})"]


def passes_public_tests(task: dict[str, object], candidate_code: str, timeout_sec: float) -> bool:
    payload = json.dumps({"candidate_code": candidate_code, "tests": task["tests"]})
    try:
        completed = subprocess.run(
            [sys.executable, "-c", EVALUATOR],
            input=payload,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False
    return completed.returncode == 0


def make_task(record: dict[str, str], timeout_sec: float) -> dict[str, object] | None:
    reference = record["prompt"] + record["canonical_solution"]
    base = {
        "task_id": record["task_id"],
        "description": record["prompt"],
        "entry_point": record["entry_point"],
        "tests": build_tests(record),
        "reference_solution": reference,
    }
    if not passes_public_tests(base, reference, timeout_sec):
        return None
    tree = ast.parse(reference)
    for mutation in ("compare", "boolean", "binary", "integer"):
        transformer = FirstMutation(mutation)
        mutated = transformer.visit(copy.deepcopy(tree))
        if not transformer.mutated:
            continue
        buggy_code = ast.unparse(ast.fix_missing_locations(mutated)) + "\n"
        if not passes_public_tests(base, buggy_code, timeout_sec):
            return {
                **base,
                "buggy_code": buggy_code,
                "mutation": mutation,
                "complexity": sum(1 for _ in ast.walk(tree)),
            }
    return None


def assign_splits(tasks: list[dict[str, object]], per_split: int) -> list[dict[str, object]]:
    needed = per_split * len(SPLITS)
    if len(tasks) < needed:
        raise ValueError(f"Only {len(tasks)} valid mutations found; need {needed}.")
    ordered = sorted(tasks, key=lambda task: (int(task["complexity"]), str(task["task_id"])))
    selected = ordered[:per_split] + ordered[per_split:2 * per_split] + ordered[-per_split:]
    output: list[dict[str, object]] = []
    for split, chunk in zip(SPLITS, (selected[:per_split], selected[per_split:2 * per_split], selected[2 * per_split:])):
        for task in chunk:
            output.append(
                {
                    **task,
                    "task_id": f"humaneval_{split}_{str(task['task_id']).replace('/', '_')}",
                    "split": split,
                    "task_family": "humaneval_repair",
                    "repair_family": task["task_id"],
                    "public_source": "openai/human-eval",
                    "source_task_id": task["task_id"],
                    "difficulty": "shifted" if split == "shifted_test" else "standard",
                }
            )
    return output


def validate(tasks: list[dict[str, object]], timeout_sec: float) -> None:
    families = {
        split: {task["repair_family"] for task in tasks if task["split"] == split}
        for split in SPLITS
    }
    if any(families[first] & families[second] for first, second in (("train", "test"), ("train", "shifted_test"), ("test", "shifted_test"))):
        raise ValueError("Public source tasks overlap across splits.")
    failures = [task["task_id"] for task in tasks if not passes_public_tests(task, str(task["reference_solution"]), timeout_sec)]
    undetected = [task["task_id"] for task in tasks if passes_public_tests(task, str(task["buggy_code"]), timeout_sec)]
    if failures or undetected:
        raise ValueError({"reference_failures": failures, "undetected_bugs": undetected})


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a public HumanEval code-repair benchmark.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--cache", default="data/public/HumanEval.jsonl.gz")
    parser.add_argument("--output", default="data/tasks_code/humaneval_repair.json")
    parser.add_argument("--per-split", type=int, default=15)
    parser.add_argument("--case-timeout", type=float, default=2.0)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    raw = cache_source(args.url, Path(args.cache), args.refresh)
    records = [json.loads(line) for line in gzip.decompress(raw).splitlines()]
    candidates = [task for record in records if (task := make_task(record, args.case_timeout)) is not None]
    tasks = assign_splits(candidates, args.per_split)
    validate(tasks, args.case_timeout)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    metadata_path = output.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps({
        "source": "openai/human-eval",
        "url": args.url,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "records": len(records),
        "valid_mutations": len(candidates),
        "split_counts": {split: sum(task["split"] == split for task in tasks) for split in SPLITS},
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "metadata": str(metadata_path), "num_tasks": len(tasks)}, indent=2))


if __name__ == "__main__":
    main()
