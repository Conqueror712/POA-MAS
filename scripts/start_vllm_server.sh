#!/usr/bin/env bash
# Start a local vLLM OpenAI-compatible server for ORCA experiments.
#
# Usage:
#     bash scripts/start_vllm_server.sh Qwen3.5-9B  8000  0
#     bash scripts/start_vllm_server.sh Qwen3.6-27B 8001  1,2
#
# Positional arguments:
#     $1  Model directory name under $ORCA_LOCAL_MODELS_ROOT
#         (default root: /mnt/tidal-sh01/dataset/GYF_DEV_0/Local_Models)
#     $2  Port to bind (default 8000)
#     $3  CUDA_VISIBLE_DEVICES to expose to this server (default 0)
#
# Environment overrides:
#     ORCA_LOCAL_MODELS_ROOT   Root dir containing model folders.
#     ORCA_VLLM_LOG_DIR        Where to redirect server logs (default logs/vllm).
#     ORCA_VLLM_EXTRA_ARGS     Extra flags forwarded verbatim to `vllm serve`.
#
# The served-model-name is set to the model folder name so it matches the
# `llm.model` field in configs/experiments_*_qwen*.json.

set -euo pipefail

MODEL_NAME="${1:-Qwen3.5-9B}"
PORT="${2:-8000}"
CUDA_VISIBLE_DEVICES_VALUE="${3:-0}"

MODELS_ROOT="${ORCA_LOCAL_MODELS_ROOT:-/mnt/tidal-sh01/dataset/GYF_DEV_0/Local_Models}"
MODEL_PATH="${MODELS_ROOT}/${MODEL_NAME}"

if [[ ! -d "${MODEL_PATH}" ]]; then
    echo "[start_vllm_server] Model path not found: ${MODEL_PATH}" >&2
    echo "[start_vllm_server] Set ORCA_LOCAL_MODELS_ROOT or check the model name." >&2
    exit 1
fi

LOG_DIR="${ORCA_VLLM_LOG_DIR:-logs/vllm}"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/${MODEL_NAME}_port${PORT}.log"

# Count GPUs to set an appropriate tensor-parallel size.
IFS=',' read -r -a GPU_ARRAY <<< "${CUDA_VISIBLE_DEVICES_VALUE}"
TP_SIZE="${#GPU_ARRAY[@]}"

echo "[start_vllm_server] model      = ${MODEL_NAME}"
echo "[start_vllm_server] model_path = ${MODEL_PATH}"
echo "[start_vllm_server] port       = ${PORT}"
echo "[start_vllm_server] GPUs       = ${CUDA_VISIBLE_DEVICES_VALUE} (TP=${TP_SIZE})"
echo "[start_vllm_server] log_file   = ${LOG_FILE}"

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES_VALUE}" \
    nohup vllm serve "${MODEL_PATH}" \
        --served-model-name "${MODEL_NAME}" \
        --host 0.0.0.0 \
        --port "${PORT}" \
        --tensor-parallel-size "${TP_SIZE}" \
        --dtype bfloat16 \
        --trust-remote-code \
        ${ORCA_VLLM_EXTRA_ARGS:-} \
        > "${LOG_FILE}" 2>&1 &

SERVER_PID=$!
echo "[start_vllm_server] launched PID=${SERVER_PID}"
echo "${SERVER_PID}" > "${LOG_DIR}/${MODEL_NAME}_port${PORT}.pid"

echo "[start_vllm_server] tailing logs (Ctrl-C to detach, server keeps running)..."
sleep 2
tail -n +1 -f "${LOG_FILE}"
