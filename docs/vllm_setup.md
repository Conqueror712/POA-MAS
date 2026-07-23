# vLLM Backend for ORCA

This note explains how to run ORCA experiments against a **local open-weights
model** served by [vLLM](https://github.com/vllm-project/vllm), in addition to
the existing DeepSeek API path.

The integration is additive: `MockLLMClient` and `DeepSeekClient` are unchanged;
a new `VLLMClient` is added in `src/utils/llm_client.py` and selected by
`provider="vllm"` in the experiment config.

---

## 1. Requirements

* A GPU node with CUDA and enough memory to hold the target model
  (Qwen3.5-9B fits on 1 × H20; Qwen3.6-27B needs 1 × H20 or 2 × smaller GPUs).
* `vllm >= 0.8` installed in the current Python environment.
* Model weights available on the local filesystem. The default layout is:

  ```text
  /mnt/tidal-sh01/dataset/GYF_DEV_0/Local_Models/
      Qwen3.5-9B/
      Qwen3.6-27B/
  ```

  If the models live elsewhere, export `ORCA_LOCAL_MODELS_ROOT` before running
  the helper script.

---

## 2. Start a vLLM server

Use the helper script (from the ORCA repo root):

```bash
# One server per model. Each server binds to its own port and its own GPU(s).
bash scripts/start_vllm_server.sh Qwen3.5-9B  8000 0
bash scripts/start_vllm_server.sh Qwen3.6-27B 8001 1
```

Positional arguments: `<model-folder> <port> <CUDA_VISIBLE_DEVICES>`.
For multi-GPU tensor parallelism pass a comma list, e.g. `0,1`.

The script:
* redirects stdout/stderr to `logs/vllm/<model>_port<port>.log`;
* records the server PID to `logs/vllm/<model>_port<port>.pid`;
* forwards any extra flags in `$ORCA_VLLM_EXTRA_ARGS` verbatim
  (e.g. `--max-model-len 8192`).

Wait until the log prints `Uvicorn running on http://0.0.0.0:<port>` before
launching experiments.

Quick sanity check:

```bash
curl -s http://127.0.0.1:8000/v1/models | python3 -m json.tool
```

You should see the served-model-name (`Qwen3.5-9B`) that ORCA configs refer to.

---

## 3. Run an ORCA experiment against vLLM

Four new configs mirror the existing DeepSeek ones:

| Config                                       | Benchmark   | Model        | Port  |
|----------------------------------------------|-------------|--------------|-------|
| `configs/experiments_apps_qwen9b.json`       | APPS repair | Qwen3.5-9B   | 8000  |
| `configs/experiments_apps_qwen27b.json`      | APPS repair | Qwen3.6-27B  | 8001  |
| `configs/experiments_humaneval_qwen9b.json`  | HumanEval   | Qwen3.5-9B   | 8000  |
| `configs/experiments_humaneval_qwen27b.json` | HumanEval   | Qwen3.6-27B  | 8001  |

Small smoke test (2 tasks, single setting):

```bash
python3 -m src.runners.run_emergence \
    --config configs/experiments_humaneval_qwen9b.json \
    --split train --mode free --limit 2 \
    --run-name humaneval_qwen9b_smoke
```

Full APPS held-out protocol for one seed (mirrors the DeepSeek run):

```bash
python3 -m src.runners.run_apps_protocol \
    --config configs/experiments_apps_qwen9b.json --seed 712
```

Trajectories, assets, summaries and downstream aggregation
(`scripts/aggregate_apps_results.py`) all work unchanged — the vLLM path just
substitutes a different `llm.provider`.

---

## 4. Adding another local model later

1. Drop the model folder under `$ORCA_LOCAL_MODELS_ROOT`.
2. Copy one of the `experiments_*_qwen*.json` configs, change `llm.model` to
   match the folder name and pick a free `base_url` port.
3. Start a server with `scripts/start_vllm_server.sh <folder> <port> <gpus>`.

No changes to `src/` are needed as long as the new model is served via the
OpenAI-compatible route.

---

## 5. Stopping a server

```bash
kill "$(cat logs/vllm/Qwen3.5-9B_port8000.pid)"
```

or, more forcefully:

```bash
pkill -f "vllm serve .*Qwen3.5-9B"
```
