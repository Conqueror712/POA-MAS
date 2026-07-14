from __future__ import annotations

import traceback
from typing import Any


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


def evaluate_code(task: dict[str, Any], candidate_code: str) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    candidate_code = extract_python_code(candidate_code)
    try:
        exec(candidate_code, namespace)
        for test in task["tests"]:
            exec(test, namespace)
        return {"success": True, "error": None}
    except Exception as exc:  # noqa: BLE001 - experiment logger needs raw failures.
        return {
            "success": False,
            "error": repr(exc),
            "traceback": traceback.format_exc(limit=5),
        }
