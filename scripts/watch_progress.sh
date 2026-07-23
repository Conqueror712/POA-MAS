#!/usr/bin/env bash
# Quick status snapshot for the running Qwen APPS protocols.
# Usage: bash scripts/watch_progress.sh
set -u

log_qwen9b="logs/experiments/apps_protocol_qwen9b_20260722_master.log"
log_qwen27b="logs/experiments/apps_protocol_qwen27b_20260722_master.log"

echo "===================================================="
echo "  ORCA vLLM Protocol Progress @ $(date -Is)"
echo "===================================================="

check_master() {
    local name="$1"
    local log="$2"
    local model_key="$3"
    local pid_file="logs/experiments/$(basename "$log" _master.log)_master.pid"

    echo
    echo "--- ${name} ---"
    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        echo "master PID: $(cat "$pid_file")   [RUNNING]"
    else
        echo "master PID: $(cat "$pid_file" 2>/dev/null || echo '?')   [DEAD or FINISHED]"
    fi

    # last progress line
    local progress
    progress=$(grep '"event": "progress"' "$log" 2>/dev/null | tail -1)
    if [[ -n "$progress" ]]; then
        echo "last progress: $progress"
    fi

    # count completed held-out runs across the whole log (sum across seeds)
    local completed
    completed=$(grep -c '"event": "condition_completed"' "$log" 2>/dev/null || echo 0)
    echo "held-out runs completed: ${completed}/36  (3 seeds × 2 splits × 6 conditions)"

    # per-seed summary count (from filesystem)
    if [[ -n "$model_key" ]]; then
        for seed in 712 713 714; do
            local n
            n=$(find "trajectories/apps_protocol_${model_key}_20260722_s${seed}_"*/ -maxdepth 1 -name summary.json 2>/dev/null | wc -l)
            printf "  seed %d: %d/13 summaries\n" "$seed" "$n"
        done
    fi

    # any errors?
    local errs
    errs=$(grep -ciE "traceback|BadRequestError|failed after retries" "$log" 2>/dev/null || echo 0)
    echo "error/traceback lines: ${errs}"

    # latest phase marker
    tail -30 "$log" 2>/dev/null | grep -E "^==> " | tail -3 | sed 's/^/  /'
}

check_master "Qwen3.5-9B  (port 8000, GPU 4)"    "$log_qwen9b"  "qwen9b"
check_master "Qwen3.6-27B (port 8001, GPU 5,6)"  "$log_qwen27b" "qwen27b"

echo
echo "--- vLLM servers ---"
for port in 8000 8001; do
    if curl -s -m 2 "http://127.0.0.1:${port}/v1/models" >/dev/null; then
        echo "  :${port} ALIVE"
    else
        echo "  :${port} DOWN"
    fi
done

echo
echo "--- GPU snapshot ---"
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv | sed 's/,/\t/g'

echo
echo "--- trajectories written so far ---"
find trajectories -maxdepth 1 -type d -name "apps_protocol_qwen*_20260722_*" 2>/dev/null | wc -l | xargs -I {} echo "  {} run directories"
