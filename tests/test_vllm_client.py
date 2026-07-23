from __future__ import annotations

import json
import unittest
from typing import Any
from unittest import mock

from src.agents.team import build_team
from src.utils.llm_client import (
    LLMResponse,
    VLLMClient,
    build_llm_client,
)


def _make_config(**overrides: Any) -> dict[str, Any]:
    llm: dict[str, Any] = {
        "provider": "vllm",
        "model": "Qwen3.5-9B",
        "base_url": "http://127.0.0.1:8000/v1",
        "api_key_env": "VLLM_TEST_API_KEY_NEVER_SET",
        "temperature": 0.0,
        "max_tokens": 64,
        "timeout_sec": 5,
        "max_retries": 0,
    }
    llm.update(overrides.pop("llm", {}))
    return {"llm": llm, **overrides}


class BuildLLMClientTests(unittest.TestCase):
    def test_build_vllm_client_returns_vllm_client(self) -> None:
        client = build_llm_client(_make_config())
        self.assertIsInstance(client, VLLMClient)
        self.assertEqual(client.model, "Qwen3.5-9B")
        self.assertEqual(client.base_url, "http://127.0.0.1:8000/v1")

    def test_build_unknown_provider_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_llm_client({"llm": {"provider": "totally-not-a-real-backend"}})

    def test_vllm_requires_model_name(self) -> None:
        with self.assertRaises(ValueError):
            VLLMClient({"llm": {"provider": "vllm", "model": ""}})


class VLLMClientChatCompletionTests(unittest.TestCase):
    """Verify request payload / response parsing without a live vLLM server."""

    def _fake_completion(self) -> dict[str, Any]:
        return {
            "id": "cmpl-test-1",
            "object": "chat.completion",
            "model": "Qwen3.5-9B",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "def solve(): return 42"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
        }

    def test_complete_builds_payload_and_parses_response(self) -> None:
        client = VLLMClient(_make_config())
        task = {
            "task_id": "unit-1",
            "description": "return 42",
            "buggy_code": "def solve(): return 0",
            "tests": ["assert solve() == 42"],
            "entry_point": "solve",
        }
        with mock.patch.object(
            VLLMClient, "_post_chat_completion", return_value=self._fake_completion()
        ) as posted:
            response = client.complete(
                agent_id="A1", subtask_type="patch", task=task, context={}
            )
            self.assertEqual(posted.call_count, 1)
            payload, api_key = posted.call_args.args
            # Default fallback API key for a vLLM server started without --api-key.
            self.assertEqual(api_key, "EMPTY")
            self.assertEqual(payload["model"], "Qwen3.5-9B")
            self.assertEqual(payload["temperature"], 0.0)
            self.assertEqual(payload["max_tokens"], 64)
            self.assertFalse(payload["stream"])
            self.assertIsInstance(payload["messages"], list)
            self.assertGreaterEqual(len(payload["messages"]), 1)

        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.text, "def solve(): return 42")
        self.assertEqual(response.metadata["provider"], "vllm")
        self.assertEqual(response.metadata["model"], "Qwen3.5-9B")
        self.assertEqual(response.metadata["usage"]["total_tokens"], 20)
        self.assertEqual(response.metadata["finish_reason"], "stop")

    def test_complete_retries_then_surfaces_error(self) -> None:
        cfg = _make_config()
        cfg["llm"]["max_retries"] = 1
        client = VLLMClient(cfg)
        task = {
            "task_id": "unit-2",
            "description": "noop",
            "buggy_code": "pass",
            "tests": [],
            "entry_point": "noop",
        }
        with mock.patch.object(
            VLLMClient,
            "_post_chat_completion",
            side_effect=RuntimeError("HTTP 500: boom"),
        ) as posted, mock.patch("src.utils.llm_client.time.sleep"):
            with self.assertRaises(RuntimeError) as ctx:
                client.complete(
                    agent_id="A1", subtask_type="patch", task=task, context={}
                )
        self.assertIn("vLLM request failed", str(ctx.exception))
        self.assertEqual(posted.call_count, 2)  # initial + 1 retry

    def test_extra_body_is_merged_into_payload(self) -> None:
        cfg = _make_config()
        cfg["llm"]["extra_body"] = {"top_p": 0.9, "seed": 42}
        client = VLLMClient(cfg)
        task = {
            "task_id": "unit-3",
            "description": "return one",
            "buggy_code": "def f(): return 0",
            "tests": ["assert f() == 1"],
            "entry_point": "f",
        }
        with mock.patch.object(
            VLLMClient, "_post_chat_completion", return_value=self._fake_completion()
        ) as posted:
            client.complete(agent_id="A1", subtask_type="patch", task=task, context={})
            payload, _ = posted.call_args.args
            self.assertEqual(payload["top_p"], 0.9)
            self.assertEqual(payload["seed"], 42)

    def test_game_task_uses_game_message_builder(self) -> None:
        client = VLLMClient(_make_config())
        task = {
            "task_id": "ipd-1",
            "task_family": "game_theory",
            "game_type": "iterated_prisoners_dilemma",
            "description": "IPD 5 rounds",
        }
        context = {"persona": "cooperative", "history_text": "No previous rounds."}
        fake = self._fake_completion()
        fake["choices"][0]["message"]["content"] = "C"
        with mock.patch.object(
            VLLMClient, "_post_chat_completion", return_value=fake
        ) as posted:
            response = client.complete(
                agent_id="A1", subtask_type="decide", task=task, context=context
            )
            payload, _ = posted.call_args.args
            joined = json.dumps(payload["messages"])
            # game builder mentions the legal actions token
            self.assertIn("Legal actions", joined)
        self.assertEqual(response.text, "C")


class VLLMClientAgentIntegrationTests(unittest.TestCase):
    """Ensure Agent/team layer accepts a VLLMClient without changes."""

    def test_agent_can_be_built_with_vllm_client(self) -> None:
        client = build_llm_client(_make_config())
        agents = build_team(num_agents=4, llm_client=client)
        self.assertEqual(len(agents), 4)
        self.assertTrue(all(a.llm_client is client for a in agents))


if __name__ == "__main__":
    unittest.main()
