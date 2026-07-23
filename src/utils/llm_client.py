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


def build_game_messages(*, agent_id: str, task: dict[str, Any], context: dict[str, Any]) -> list[dict[str, str]]:
    assets = context.get("game_assets") or {}
    asset_hint = json.dumps(assets, ensure_ascii=False)[:1200] if assets else "No reusable strategy assets are loaded."
    persona = context.get("persona", "unspecified")
    history = context.get("history_text", "No previous rounds.")
    game_type = task["game_type"]
    if game_type == "iterated_prisoners_dilemma":
        legal = "Legal actions: C or D."
    elif game_type == "public_goods":
        legal = "Legal actions: CONTRIBUTE or KEEP."
    else:
        legal = "Return one legal action token."
    if context.get("force_action_retry"):
        system = "Output one legal action token only. No explanation."
        user = f"{legal}\nPrevious response was invalid or empty. Reply with exactly one legal action token."
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]
    system = (
        "You are choosing a single action in a game-theory experiment. "
        "Return only the action token. No explanation."
    )
    user = (
        f"Agent: {agent_id}\n"
        f"Persona: {persona}\n"
        f"Game: {game_type}\n"
        f"Payoff/task summary: {task['description'][:500]}\n"
        f"Recent actions: {history}\n"
        f"Reusable strategy assets:\n{asset_hint}\n\n"
        f"{legal}\n"
        "Answer:"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


class MockLLMClient:
    """Deterministic stand-in for API/local LLM calls.

    It lets us validate the experiment pipeline before spending API or GPU budget.
    """

    def complete(self, *, agent_id: str, subtask_type: str, task: dict[str, Any], context: dict[str, Any]) -> LLMResponse:
        if task.get("task_family") == "game_theory" and subtask_type == "decide":
            text = self._decide_game(agent_id, task, context)
        elif subtask_type == "localize":
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

    @staticmethod
    def _decide_game(agent_id: str, task: dict[str, Any], context: dict[str, Any]) -> str:
        game_type = task["game_type"]
        persona = str(context.get("persona", "")).lower()
        has_assets = bool(context.get("game_assets"))
        history = context.get("history") or []

        if game_type == "iterated_prisoners_dilemma":
            if has_assets:
                if not history:
                    return "C"
                other_actions = [
                    action
                    for player, action in history[-1]["actions"].items()
                    if player != agent_id
                ]
                return "C" if other_actions and other_actions[0] == "C" else "D"
            if "cooperative" in persona or "fairness" in persona:
                return "C"
            if "reciprocal" in persona or "conditional" in persona:
                if not history:
                    return "C"
                other_actions = [
                    action
                    for player, action in history[-1]["actions"].items()
                    if player != agent_id
                ]
                return "C" if other_actions and other_actions[0] == "C" else "D"
            return "D"

        if game_type == "public_goods":
            if has_assets:
                if len(history) < 2:
                    return "CONTRIBUTE"
                last_actions = list(history[-1]["actions"].values())
                contribution_rate = sum(1 for action in last_actions if action == "CONTRIBUTE") / len(last_actions)
                return "CONTRIBUTE" if contribution_rate >= 0.5 else "KEEP"
            if "cooperative" in persona or "fairness" in persona or "conditional" in persona:
                return "CONTRIBUTE"
            return "KEEP"

        return "D"


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
            "messages": (
                build_game_messages(agent_id=agent_id, task=task, context=context)
                if task.get("task_family") == "game_theory" and subtask_type == "decide"
                else build_code_repair_messages(
                    agent_id=agent_id,
                    subtask_type=subtask_type,
                    task=task,
                    context=context,
                )
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


class VLLMClient:
    """OpenAI-compatible HTTP client for a local vLLM server.

    This client talks to a vLLM instance started via
    ``vllm serve <model_path>`` (or the ``scripts/start_vllm_server.sh``
    helper). It reuses the same request-shape as :class:`DeepSeekClient`
    so downstream code (agents, controller, runners) can stay unchanged.

    Configuration expected under ``config["llm"]``::

        {
          "provider": "vllm",
          "model": "Qwen3.5-9B",              # served-model-name at vLLM start
          "base_url": "http://127.0.0.1:8000/v1",
          "api_key_env": "VLLM_API_KEY",       # optional; vLLM defaults to "EMPTY"
          "temperature": 0.2,
          "max_tokens": 1200,
          "timeout_sec": 120,
          "max_retries": 2,
          "extra_body": {}                    # e.g. {"top_p": 0.9}
        }

    Notes:
        * ``base_url`` should include the ``/v1`` suffix that vLLM exposes
          for the OpenAI-compatible route.
        * ``api_key_env`` is optional; if the env var is unset the client
          falls back to the literal ``"EMPTY"`` that vLLM accepts by default.
    """

    def __init__(self, config: dict[str, Any]):
        llm_config = config.get("llm", {})
        self.model = llm_config.get("model", "")
        if not self.model:
            raise ValueError("VLLMClient requires llm.model to match the served-model-name")
        self.base_url = llm_config.get("base_url", "http://127.0.0.1:8000/v1").rstrip("/")
        self.api_key_env = llm_config.get("api_key_env", "VLLM_API_KEY")
        self.api_key_file = llm_config.get("api_key_file")
        self.temperature = float(llm_config.get("temperature", 0.2))
        self.max_tokens = int(llm_config.get("max_tokens", 1200))
        self.timeout_sec = int(llm_config.get("timeout_sec", 120))
        self.max_retries = int(llm_config.get("max_retries", 2))
        self.extra_body = llm_config.get("extra_body", {})

    def complete(self, *, agent_id: str, subtask_type: str, task: dict[str, Any], context: dict[str, Any]) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": (
                build_game_messages(agent_id=agent_id, task=task, context=context)
                if task.get("task_family") == "game_theory" and subtask_type == "decide"
                else build_code_repair_messages(
                    agent_id=agent_id,
                    subtask_type=subtask_type,
                    task=task,
                    context=context,
                )
            ),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        payload.update(self.extra_body)

        api_key = self._resolve_api_key()
        last_error: str | None = None
        for attempt in range(self.max_retries + 1):
            try:
                raw = self._post_chat_completion(payload, api_key)
                choice = raw["choices"][0]["message"]
                return LLMResponse(
                    text=choice.get("content", ""),
                    metadata={
                        "provider": "vllm",
                        "model": self.model,
                        "base_url": self.base_url,
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

        raise RuntimeError(f"vLLM request failed after retries: {last_error}")

    def _resolve_api_key(self) -> str:
        api_key = os.environ.get(self.api_key_env)
        if api_key:
            return api_key
        if self.api_key_file:
            key_path = Path(self.api_key_file).expanduser()
            try:
                content = key_path.read_text(encoding="utf-8-sig").strip()
                if content:
                    return content
            except OSError:
                pass
        # vLLM accepts "EMPTY" when the server is started without --api-key.
        return "EMPTY"

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


# Any LLM client used by agents/team/controller.
# We keep this deliberately loose so new backends (vLLM, TGI, HF pipeline, ...)
# can be added later without touching the agent layer.
LLMClient = MockLLMClient | DeepSeekClient | VLLMClient


def build_llm_client(config: dict[str, Any]) -> LLMClient:
    provider = config.get("llm", {}).get("provider", "mock")
    if provider == "mock":
        return MockLLMClient()
    if provider == "deepseek":
        return DeepSeekClient(config)
    if provider == "vllm":
        return VLLMClient(config)
    raise ValueError(f"Unsupported provider: {provider}")
