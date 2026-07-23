#!/usr/bin/env bash
# Asset-type ablation: within the prompt-channel reuse strategy, run
# role-only and organization-only variants so we can attribute the observed
# Prompt-vs-Free gap to a specific asset type.
#
# Usage:
#   bash scripts/run_asset_type_ablation.sh <config> <prefix> <seed1,seed2,...>
#
# The existing full-asset Prompt run (from run_apps_protocol) already exists;
# this script only adds the role-only and organization-only variants on the
# same seeds and splits, then hands off to the standard aggregator.

set -euo pipefail

CONFIG="${1:?config path required}"
PREFIX="${2:?run-prefix required (e.g. apps_ablation_qwen27b_20260723)}"
SEEDS_CSV="${3:?comma-separated seeds required}"

IFS=',' read -r -a SEEDS <<< "${SEEDS_CSV}"

for SEED in "${SEEDS[@]}"; do
    for SPLIT in test shifted_test; do
        for MODE in role organization; do
            RUN_NAME="${PREFIX}_s${SEED}_${SPLIT}_reuse_prompt_${MODE}"
            if [[ -f "trajectories/${RUN_NAME}/summary.json" ]]; then
                echo "==> SKIP (exists): ${RUN_NAME}"
                continue
            fi
            echo "==> [seed ${SEED}] ${SPLIT}  asset-mode=${MODE}  strategy=prompt"
            python3 -m src.runners.run_reuse \
                --config "${CONFIG}" \
                --asset-mode "${MODE}" \
                --reuse-strategy prompt \
                --split "${SPLIT}" \
                --seed "${SEED}" \
                --run-name "${RUN_NAME}"
        done
    done
done

echo "==> Aggregate with:"
echo "    python3 scripts/aggregate_apps_results.py --prefix ${PREFIX}_ --out-dir results/tables_${PREFIX##*_}"
