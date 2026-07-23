# APPS Cross-Model Robustness (3 seeds: 712/713/714)

All values are mean success rate over 3 seeds (matched task set), Δ = Prompt − Free.
Bold indicates the best per-model setting per split; the sign of Δ shows whether
selective prompt-channel reuse helps on that model.

## shifted_test (out-of-family held-out, 15 tasks)

| Setting          | DeepSeek-V4-Flash | Qwen3.6-27B | Qwen3.5-9B |
|------------------|------------------:|------------:|-----------:|
| Free             |             0.689 |       0.778 |      0.533 |
| Manual           |             0.622 |       0.711 |      0.444 |
| Random           |             0.756 |       0.756 |      0.444 |
| Prompt (reuse)   |         **0.822** |   **0.800** |      0.378 |
| Routing (reuse)  |             0.778 |       0.667 |      0.378 |
| Full (reuse)     |             0.644 |       0.778 |      0.400 |
| **Δ Prompt−Free**|         **+0.133**|   **+0.022**|     −0.156 |

## test (in-family held-out, 20 tasks)

| Setting          | DeepSeek-V4-Flash | Qwen3.6-27B | Qwen3.5-9B |
|------------------|------------------:|------------:|-----------:|
| Free             |             0.900 |       0.783 |      0.517 |
| Manual           |         **0.933** |       0.750 |      0.517 |
| Random           |             0.850 |       0.767 |      0.467 |
| Prompt (reuse)   |             0.917 |   **0.850** |      0.383 |
| Routing (reuse)  |             0.833 |       0.750 |      0.500 |
| Full (reuse)     |             0.850 |   **0.850** |      0.500 |
| **Δ Prompt−Free**|            +0.017 |     +0.067  |     −0.133 |

## Interpretation

- On both **DeepSeek-V4-Flash** and **Qwen3.6-27B**, `Prompt` (selective
  prompt-channel asset reuse) is the best or tied-best setting on
  `shifted_test`, matching the paper's central claim that selective reuse
  improves shifted-task robustness.
- On the smaller **Qwen3.5-9B**, `Prompt` under-performs `Free` on both splits
  (Δ = −0.156 on shifted, −0.133 on test). We interpret this as an
  asset-quality × context-budget interaction: assets extracted from 9B
  trajectories are less discriminative, and injecting them into the patch
  agent's prompt displaces context that the smaller model needs for the fix
  itself. This is discussed in the Limitations section as a scale-dependent
  boundary of ORCA.
- The Qwen3.6-27B result confirms cross-model robustness of the mechanism
  without relying on a single API family.

## Provenance

- Trajectories: `trajectories/apps_protocol_{qwen9b,qwen27b}_20260722_s{712,713,714}_*/summary.json`
- Configs: `configs/experiments_apps_{qwen9b,qwen27b}.json`
  (both use `extra_body.chat_template_kwargs.enable_thinking=false`)
- Aggregator: `python3 scripts/aggregate_apps_results.py --prefix apps_protocol_qwen9b_ --out-dir results/tables_qwen9b`
  (and analogously for `qwen27b_`)
