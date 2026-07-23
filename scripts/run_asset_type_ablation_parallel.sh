#!/usr/bin/env bash
# Parallel version: fire all (seed, split, asset-mode) combinations at once
# and let vLLM batch them. Requires the vLLM server to be running.
#
# Usage:
#   bash scripts/run_asset_type_ablation_parallel.sh <config> <prefix> <seed1,seed2,...>

set -uo pipefail

CONFIG="${1:?config path required}"
PREFIX="${2:?run-prefix required}"
SEEDS_CSV="${3:?comma-separated seeds required}"

IFS=',' read -r -a SEEDS <<< "${SEEDS_CSV}"

PIDS=()
LOG_DIR="logs/asset_ablation_qwen27b/jobs"
mkdir -p "${LOG_DIR}"

for SEED in "${SEEDS[@]}"; do
    for SPLIT in test shifted_test; do
        for MODE in role organization; do
            RUN_NAME="${PREFIX}_s${SEED}_${SPLIT}_reuse_prompt_${MODE}"
            if [[ -f "trajectories/${RUN_NAME}/summary.json" ]]; then
                echo "==> SKIP (exists): ${RUN_NAME}"
                continue
            fi
            LOG="${LOG_DIR}/${RUN_NAME}.log"
            echo "==> LAUNCH ${RUN_NAME}"
            (
                python3 -m src.runners.run_reuse \
                    --config "${CONFIG}" \
                    --asset-mode "${MODE}" \
                    --reuse-strategy prompt \
                    --split "${SPLIT}" \
                    --seed "${SEED}" \
                    --run-name "${RUN_NAME}" \
                    > "${LOG}" 2>&1
                echo "DONE ${RUN_NAME} exit=$?"
            ) &
            PIDS+=($!)
        done
    done
done

echo "==> Waiting for ${#PIDS[@]} jobs to finish..."
for pid in "${PIDS[@]}"; do
    wait "$pid" || echo "Job $pid failed."
done
echo "==> All jobs done."
