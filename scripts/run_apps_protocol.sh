#!/usr/bin/env bash
# Bash counterpart of scripts/run_apps_protocol.ps1.
#
# Usage:
#     bash scripts/run_apps_protocol.sh <config> <prefix> [seed ...]
#
# Example:
#     bash scripts/run_apps_protocol.sh configs/experiments_apps_qwen9b.json apps_protocol_qwen9b_20260722 712 713 714
#
# For each seed:
#   1. run_training on `train` split (produces trajectory)      [skipped if trajectory already exists]
#   2. run_extract_assets on that trajectory                     [skipped if assets already exist]
#   3. run_apps_protocol on `test` + `shifted_test`, all 6 conditions
#
# Progress + errors are captured to logs/experiments/<prefix>_<seed>.log.
# The script does NOT abort on failures inside a single seed; it logs and moves on
# so a transient error in one seed does not lose progress in later seeds.
set -uo pipefail

CONFIG="${1:?config path required}"
PREFIX="${2:?run prefix required}"
shift 2
SEEDS=("$@")
if [[ "${#SEEDS[@]}" -eq 0 ]]; then
    SEEDS=(712 713 714)
fi

LOG_DIR="logs/experiments"
mkdir -p "${LOG_DIR}"

export PYTHONIOENCODING=utf-8

# Extract asset_root from the config so we can detect already-extracted assets.
ASSET_ROOT=$(python3 -c "import json,sys;print(json.load(open('${CONFIG}'))['asset_root'])")
ROLE_ASSET_FILE="${ASSET_ROOT}/role_assets/latest_role_assets.json"
ORG_ASSET_FILE="${ASSET_ROOT}/organization_assets/latest_organization_assets.json"

for SEED in "${SEEDS[@]}"; do
    RUN_LOG="${LOG_DIR}/${PREFIX}_s${SEED}.log"
    TRAIN_NAME="${PREFIX}_s${SEED}_train_free"

    {
        echo "==============================================="
        echo "==> $(date -Is) START prefix=${PREFIX} seed=${SEED}"
        echo "    config=${CONFIG}   asset_root=${ASSET_ROOT}"
        echo "==============================================="

        if [[ -f "trajectories/${TRAIN_NAME}/summary.json" ]]; then
            echo "==> $(date -Is) [1/3] SKIP train (trajectories/${TRAIN_NAME} already exists)"
        else
            echo "==> $(date -Is) [1/3] TRAINING assets  (run_name=${TRAIN_NAME})"
            python3 -m src.runners.run_training \
                --config "${CONFIG}" \
                --split train \
                --seed "${SEED}" \
                --run-name "${TRAIN_NAME}"
        fi

        if [[ -f "${ROLE_ASSET_FILE}" && -f "${ORG_ASSET_FILE}" ]]; then
            echo "==> $(date -Is) [2/3] SKIP extract (assets already at ${ASSET_ROOT})"
        else
            echo "==> $(date -Is) [2/3] EXTRACTING assets  (trajectories/${TRAIN_NAME})"
            python3 -m src.runners.run_extract_assets \
                --config "${CONFIG}" \
                --run-dir "trajectories/${TRAIN_NAME}"
        fi

        echo "==> $(date -Is) [3/3] APPS held-out protocol  (test + shifted_test)"
        python3 -m src.runners.run_apps_protocol \
            --config "${CONFIG}" \
            --seed "${SEED}" \
            --run-prefix "${PREFIX}_s${SEED}" \
            --splits test shifted_test \
            || echo "==> $(date -Is) SEED ${SEED} FAILED in protocol step (continuing to next seed)"

        echo "==> $(date -Is) SEED ${SEED} DONE"
    } 2>&1 | tee -a "${RUN_LOG}"
done

echo "==> $(date -Is) All seeds processed for ${PREFIX}"
echo "    Trajectories: trajectories/${PREFIX}_s<seed>_*"
echo "    Logs:         ${LOG_DIR}/${PREFIX}_s<seed>.log"
