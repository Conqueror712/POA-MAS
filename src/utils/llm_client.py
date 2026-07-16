from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


@dataclass
class LLMResponse:
    text: str
    metadata: dict[str, Any]


def build_code_repair_messages(*, agent_id: str, subtask_type: str, task: dict[str, Any], context: dict[str, Any]) -> list[dict[str, str]]:
    assets = context.get("assets") or {}
    asset_hint = json.dumps(assets, ensure_ascii=False)[:4000] if assets else "No reusable assets are loaded."
    system = (
        "You are an agent in a multi-agent code repair experiment. "
        "Follow the assigned subtask exactly. Keep outputs concise and machine-readable."
    )
    tests = task.get("tests", [])
    if task.get("evaluation_mode") == "stdin_stdout":
        tests = [f"stdin: {stdin!r}\nexpected stdout: {stdout!r}" for stdin, stdout in zip(task["inputs"], task["outputs"])]

    if subtask_type == "localize":
        user = (
            f"Agent: {agent_id}\n"
            "Subtask: localize the likely bug.\n"
            f"Task: {task['description']}\n"
            f"Buggy code:\n```python\n{task['buggy_code']}\n```\n"
            f"Reusable assets:\n{asset_hint}\n\n"
            "Return 1-3 bullet points describing the likely bug and relevant lines. Do not patch yet."
        )
    elif subtask_type == "patch":
        output_instruction = (
            "Return only the complete corrected Python program. It must read from standard input and write the expected output. "
            "No Markdown fence. No explanation."
            if task.get("evaluation_mode") == "stdin_stdout"
            else "Return only the complete corrected Python function. No Markdown fence. No explanation."
        )
        user = (
            f"Agent: {agent_id}\n"
            "Subtask: patch the buggy code.\n"
            f"Task: {task['description']}\n"
            f"Buggy code:\n```python\n{task['buggy_code']}\n```\n"
            f"Localization notes:\n{context.get('localize', 'No localization notes.')}\n"
            f"Reusable assets:\n{asset_hint}\n\n"
            + output_instruction
        )
    elif subtask_type == "review":
        user = (
            f"Agent: {agent_id}\n"
            "Subtask: review the candidate patch.\n"
            f"Task: {task['description']}\n"
            f"Candidate code:\n```python\n{context.get('candidate_code', '')}\n```\n"
            f"Tests:\n" + "\n".join(tests) + "\n\n"
            "Return PASS if the patch appears correct, otherwise return FAIL followed by one short reason."
        )
    else:
        user = f"Unknown subtask: {subtask_type}"

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


class MockLLMClient:
    """Deterministic stand-in for API/local LLM calls.

    It lets us validate the experiment pipeline before spending API or GPU budget.
    """

    def complete(self, *, agent_id: str, subtask_type: str, task: dict[str, Any], context: dict[str, Any]) -> LLMResponse:
        if subtask_type == "localize":
            text = self._localize(task)
        elif subtask_type == "patch":
            text = task["reference_solution"]
        elif subtask_type == "review":
            candidate = context.get("candidate_code", "")
            text = "PASS" if candidate.strip() else "FAIL: empty patch"
        else:
            text = f"{agent_id} has no handler for {subtask_type}."

        return LLMResponse(
            text=text,
            metadata={
                "provider": "mock",
                "agent_id": agent_id,
                "subtask_type": subtask_type,
            },
        )

    @staticmethod
    def _localize(task: dict[str, Any]) -> str:
        return (
            "Likely bug: implementation does not match task description. "
            f"Entry point: {task.get('entry_point', 'unknown')}."
        )


class DeepSeekClient:
    def __init__(self, config: dict[str, Any]):
        llm_config = config.get("llm", {})
        self.model = llm_config.get("model", "deepseek-v4-flash")
        self.base_url = llm_config.get("base_url", "https://api.deepseek.com").rstrip("/")
        self.api_key_env = llm_config.get("api_key_env", "DEEPSEEK_API_KEY")
        self.api_key_file = llm_config.get("api_key_file")
        self.temperature = float(llm_config.get("temperature", 0.2))
        self.max_tokens = int(llm_config.get("max_tokens", 1200))
        self.timeout_sec = int(llm_config.get("timeout_sec", 60))
        self.max_retries = int(llm_config.get("max_retries", 2))
        self.extra_body = llm_config.get("extra_body", {})

    def complete(self, *, agent_id: str, subtask_type: str, task: dict[str, Any], context: dict[str, Any]) -> LLMResponse:
        api_key = self._resolve_api_key()
        if not api_key:
            raise RuntimeError(
                f"Missing API key. Set environment variable {self.api_key_env} "
                "or configure a non-empty api_key_file before using DeepSeek."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": build_code_repair_messages(
                agent_id=agent_id,
                subtask_type=subtask_type,
                task=task,
                context=context,
            ),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        payload.update(self.extra_body)

        last_error: str | None = None
        for attempt in range(self.max_retries + 1):
            try:
                raw = self._post_chat_completion(payload, api_key)
                choice = raw["choices"][0]["message"]
                return LLMResponse(
                    text=choice.get("content", ""),
                    metadata={
                        "provider": "deepseek",
                        "model": self.model,
                        "agent_id": agent_id,
                        "subtask_type": subtask_type,
                        "usage": raw.get("usage", {}),
                        "finish_reason": raw["choices"][0].get("finish_reason"),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - retry then surface API details.
                last_error = repr(exc)
                if attempt < self.max_retries:
                    time.sleep(1.5 * (attempt + 1))

        raise RuntimeError(f"DeepSeek request failed after retries: {last_error}")

    def _resolve_api_key(self) -> str | None:
        api_key = os.environ.get(self.api_key_env)
        if api_key:
            return api_key
        if not self.api_key_file:
            return None

        key_path = Path(self.api_key_file).expanduser()
        try:
            return key_path.read_text(encoding="utf-8-sig").strip() or None
        except OSError as exc:
            raise RuntimeError(f"Unable to read API key file {key_path}: {exc}") from exc

    def _post_chat_completion(self, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_sec) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def build_llm_client(config: dict[str, Any]) -> MockLLMClient | DeepSeekClient:
    provider = config.get("llm", {}).get("provider", "mock")
    if provider == "mock":
        return MockLLMClient()
    if provider == "deepseek":
        return DeepSeekClient(config)
    raise ValueError(f"Unsupported provider: {provider}")
