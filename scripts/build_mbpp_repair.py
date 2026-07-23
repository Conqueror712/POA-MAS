"""Build a public MBPP code-repair benchmark, mirroring build_humaneval_repair.py.

MBPP (Mostly Basic Python Programming) provides a text description, a canonical
Python solution, and a small list of asserts per task. We keep the same repair
protocol as HumanEval: apply one AST-level mutation to the canonical solution,
keep only samples where the reference passes but the mutation fails, and
assign per-split subsets.

Usage:
    python3 scripts/build_mbpp_repair.py
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from urllib import request


# MBPP sanitised split as hosted on Hugging Face; we consume the four
# split-shards (prompt/test/validation/train) and merge them, because we
# construct our own train/test/shifted_test split from complexity ordering.
DEFAULT_URL_BASE = "https://hf-mirror.com/datasets/google-research-datasets/mbpp/resolve/main/sanitized"
DEFAULT_SPLIT_SHARDS = ("prompt", "test", "validation", "train")
SPLITS = ("train", "test", "shifted_test")

# MBPP does not ship with an entry_point; we execute the solution followed by
# the asserts under a shared namespace.
EVALUATOR = (
    "import json, sys\n"
    "payload = json.load(sys.stdin)\n"
    "namespace = {}\n"
    "exec(payload['candidate_code'], namespace)\n"
    "for test in payload['tests']:\n"
    "    exec(test, namespace)\n"
)


class FirstMutation(ast.NodeTransformer):
    """Apply exactly one AST-level mutation to introduce a semantic bug."""

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
        if (
            self.mutation == "integer"
            and not self.mutated
            and isinstance(node.value, int)
            and not isinstance(node.value, bool)
        ):
            node.value = node.value + 1 if node.value >= 0 else node.value - 1
            self.mutated = True
        return node


def cache_source(url_base: str, split_shards: tuple[str, ...], cache_dir: Path, refresh: bool) -> tuple[list[dict[str, object]], bytes]:
    """Download and merge the four sanitized-mbpp parquet shards.

    Returns the merged list of records and the concatenated raw bytes (used
    to compute a stable SHA-256 for the metadata file).
    """
    import pandas as pd  # local import so the script is optional-dependency friendly

    cache_dir.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, object]] = []
    raw_concat = b""
    for shard in split_shards:
        cache_path = cache_dir / f"mbpp_sanitized_{shard}.parquet"
        if refresh or not cache_path.exists():
            url = f"{url_base}/{shard}-00000-of-00001.parquet"
            cache_path.write_bytes(request.urlopen(url, timeout=60).read())
        raw = cache_path.read_bytes()
        raw_concat += raw
        df = pd.read_parquet(cache_path)
        for row in df.to_dict(orient="records"):
            # Normalize numpy arrays to lists for JSON friendliness.
            if hasattr(row.get("test_list"), "tolist"):
                row["test_list"] = row["test_list"].tolist()
            if hasattr(row.get("test_imports"), "tolist"):
                row["test_imports"] = row["test_imports"].tolist()
            all_records.append(row)
    return all_records, raw_concat


def build_tests(record: dict[str, object]) -> list[str]:
    # MBPP records ship with "test_list" (list[str]) of executable asserts.
    tests = record.get("test_list") or record.get("test") or []
    if isinstance(tests, str):
        tests = [tests]
    # Keep at most three asserts per task for parity with HumanEval's single
    # aggregated check call; leaves comparable test-signal density.
    return [t for t in tests[:3] if isinstance(t, str) and t.strip()]


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


def make_task(record: dict[str, object], timeout_sec: float) -> dict[str, object] | None:
    # sanitized-mbpp uses "prompt" and "code" fields; the source release uses
    # "text" and "code". Handle both.
    description = record.get("prompt") or record.get("text") or ""
    reference = record.get("code") or ""
    if not description or not reference:
        return None
    task_id_raw = record.get("task_id") or record.get("source_file") or ""
    tests = build_tests(record)
    if not tests:
        return None
    base = {
        "task_id": f"MBPP/{task_id_raw}",
        "description": description,
        "entry_point": "",  # MBPP does not ship a canonical entry_point name
        "tests": tests,
        "reference_solution": reference,
    }
    if not passes_public_tests(base, reference, timeout_sec):
        return None
    try:
        tree = ast.parse(reference)
    except SyntaxError:
        return None
    for mutation in ("compare", "boolean", "binary", "integer"):
        transformer = FirstMutation(mutation)
        mutated = transformer.visit(copy.deepcopy(tree))
        if not transformer.mutated:
            continue
        try:
            buggy_code = ast.unparse(ast.fix_missing_locations(mutated)) + "\n"
        except Exception:
            continue
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
    # train = simplest per_split, test = next per_split, shifted_test = the most complex per_split.
    selected = (
        ordered[:per_split]
        + ordered[per_split : 2 * per_split]
        + ordered[-per_split:]
    )
    output: list[dict[str, object]] = []
    for split, chunk in zip(
        SPLITS,
        (selected[:per_split], selected[per_split : 2 * per_split], selected[2 * per_split :]),
    ):
        for task in chunk:
            output.append(
                {
                    **task,
                    "task_id": f"mbpp_{split}_{str(task['task_id']).replace('/', '_')}",
                    "split": split,
                    "task_family": "mbpp_repair",
                    "repair_family": task["task_id"],
                    "public_source": "google-research/mbpp (sanitized)",
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
    for a, b in (("train", "test"), ("train", "shifted_test"), ("test", "shifted_test")):
        if families[a] & families[b]:
            raise ValueError(f"Public source tasks overlap across splits ({a} vs {b}).")
    failures = [
        task["task_id"]
        for task in tasks
        if not passes_public_tests(task, str(task["reference_solution"]), timeout_sec)
    ]
    undetected = [
        task["task_id"]
        for task in tasks
        if passes_public_tests(task, str(task["buggy_code"]), timeout_sec)
    ]
    if failures or undetected:
        raise ValueError({"reference_failures": failures, "undetected_bugs": undetected})


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a public MBPP code-repair benchmark.")
    parser.add_argument("--url-base", default=DEFAULT_URL_BASE)
    parser.add_argument("--split-shards", nargs="+", default=list(DEFAULT_SPLIT_SHARDS))
    parser.add_argument("--cache-dir", default="data/public")
    parser.add_argument("--output", default="data/tasks_code/mbpp_repair.json")
    parser.add_argument("--per-split", type=int, default=15)
    parser.add_argument("--case-timeout", type=float, default=2.0)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    records, raw = cache_source(args.url_base, tuple(args.split_shards), Path(args.cache_dir), args.refresh)
    candidates: list[dict[str, object]] = []
    for record in records:
        task = make_task(record, args.case_timeout)
        if task is not None:
            candidates.append(task)
    tasks = assign_splits(candidates, args.per_split)
    validate(tasks, args.case_timeout)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    metadata_path = output.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(
            {
                "source": "google-research-datasets/mbpp (sanitized, via hf-mirror)",
                "url_base": args.url_base,
                "split_shards": args.split_shards,
                "sha256_concat": hashlib.sha256(raw).hexdigest(),
                "records": len(records),
                "valid_mutations": len(candidates),
                "split_counts": {split: sum(task["split"] == split for task in tasks) for split in SPLITS},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(output), "metadata": str(metadata_path), "num_tasks": len(tasks)}, indent=2))


if __name__ == "__main__":
    main()
