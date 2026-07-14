from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


EVALUATOR = (
    "import json, sys\n"
    "payload = json.load(sys.stdin)\n"
    "namespace = {}\n"
    "exec(payload['candidate_code'], namespace)\n"
    "for test in payload['tests']:\n"
    "    exec(test, namespace)\n"
)


def extract_python_code(candidate_code: str) -> str:
    text = candidate_code.strip()
    if "```" not in text:
        return text

    parts = text.split("```")
    for part in parts:
        stripped = part.strip()
        if stripped.startswith("python"):
            return stripped.removeprefix("python").strip()
    for part in parts:
        stripped = part.strip()
        if stripped.startswith("def ") or "\ndef " in stripped:
            return stripped
    return text


def evaluate_code(task: dict[str, Any], candidate_code: str, timeout_sec: float = 5.0) -> dict[str, Any]:
    candidate_code = extract_python_code(candidate_code)
    try:
        result = subprocess.run(
            [sys.executable, "-c", EVALUATOR],
            input=json.dumps({"candidate_code": candidate_code, "tests": task["tests"]}),
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Evaluation timed out after {timeout_sec} seconds.",
        }
    if result.returncode == 0:
        return {"success": True, "error": None}
    return {
        "success": False,
        "error": result.stderr.strip() or f"Evaluator exited with code {result.returncode}.",
    }
