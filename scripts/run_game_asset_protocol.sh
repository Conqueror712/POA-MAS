#!/usr/bin/env bash
# Run full Domain 2 game asset protocol for a single backbone.
#
# Usage:
#   bash scripts/run_game_asset_protocol.sh <config> <prefix> <seed1,seed2,...>
#
# Example:
#   bash scripts/run_game_asset_protocol.sh configs/experiments_game_qwen27b.json \
#     game_asset_qwen27b_20260723 712,713,714

set -euo pipefail

CONFIG="${1:?config path required}"
PREFIX="${2:?run-prefix required}"
SEEDS_CSV="${3:?comma-separated seeds required}"
ASSET_FILENAME="latest_strategy_assets.json"

# Extract asset_root from the config to build correct asset paths
ASSET_ROOT=$(python3 -c "import json,sys;print(json.load(open('${CONFIG}'))['asset_root'])")

IFS=',' read -r -a SEEDS <<< "${SEEDS_CSV}"

for SEED in "${SEEDS[@]}"; do
    TRAIN_PREFIX="${PREFIX}_s${SEED}_train"
    echo "==> [seed ${SEED}] train (persona)"
    python3 -m src.runners.run_game_domain \
        --config "${CONFIG}" \
        --splits train \
        --settings persona \
        --seed "${SEED}" \
        --run-prefix "${TRAIN_PREFIX}"

    echo "==> [seed ${SEED}] extract game assets from ${TRAIN_PREFIX}"
    python3 -m src.runners.run_extract_game_assets \
        --config "${CONFIG}" \
        --run-prefix "${TRAIN_PREFIX}" \
        --filename "${ASSET_FILENAME}"

    ASSET_FILE="${ASSET_ROOT}/game_assets/${ASSET_FILENAME}"
    echo "==> [seed ${SEED}] held-out (no_persona, persona, reuse_assets) on test + shifted_test"
    python3 -m src.runners.run_game_domain \
        --config "${CONFIG}" \
        --splits test shifted_test \
        --settings no_persona persona reuse_assets \
        --seed "${SEED}" \
        --run-prefix "${PREFIX}_s${SEED}" \
        --game-asset-file "${ASSET_FILE}"
done

echo "==> Done. Aggregate with:"
echo "    python3 scripts/aggregate_game_results.py --prefix ${PREFIX} --splits test shifted_test"
