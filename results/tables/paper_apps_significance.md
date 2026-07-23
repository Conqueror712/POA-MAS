# APPS Matched-Pair Significance Tests

> **PENDING seed 714 for Backbone A**: the current Backbone A rows in this
> table are computed over 2 seeds (712, 713) because seed 714 trajectories
> are not yet in `trajectories/`. The paper reports 3 seeds; regenerate this
> table after seed 714 is added by re-running
> `python3 scripts/statistical_tests.py`.

For each contrast, we pair per-task success indicators across matching
(seed, task_id) and compute the paired difference. `Mean diff` reports the
mean over pairs with a bootstrap 95% CI (10k resamples). `p` is the
two-sided Wilcoxon signed-rank test (zeros dropped).

`Rescues`/`Hurts` count pairs where setting-a succeeds but setting-b fails, and
vice versa; `Ties` are pairs with identical outcomes.

| Backbone | Split | Contrast | n | Rescues | Hurts | Ties | Mean diff [95% CI] | p |
|---|---|---|---:|---:|---:|---:|:--|---:|
| Backbone A (closed-API) | shifted_test | reuse_prompt − free | 30 | 7 | 2 | 21 | +0.167 [-0.001, +0.367] | 0.10 |
| Backbone A (closed-API) | shifted_test | reuse_prompt − random | 30 | 5 | 2 | 23 | +0.100 [-0.067, +0.267] | 0.26 |
| Backbone A (closed-API) | shifted_test | reuse_full − free | 30 | 4 | 3 | 23 | +0.033 [-0.133, +0.200] | 0.71 |
| Backbone A (closed-API) | shifted_test | reuse_routing − free | 30 | 6 | 1 | 23 | +0.167 [+0.000, +0.333] | 0.06 |
| Backbone A (closed-API) | test | reuse_prompt − free | 40 | 3 | 3 | 34 | +0.000 [-0.125, +0.125] | 1.00 |
| Backbone A (closed-API) | test | reuse_prompt − random | 40 | 4 | 0 | 36 | +0.100 [+0.025, +0.200] | 0.05 |
| Backbone A (closed-API) | test | reuse_full − free | 40 | 1 | 4 | 35 | −0.075 [-0.200, +0.025] | 0.18 |
| Backbone A (closed-API) | test | reuse_routing − free | 40 | 1 | 4 | 35 | −0.075 [-0.175, +0.025] | 0.18 |
| Backbone B (Qwen-27B) | shifted_test | reuse_prompt − free | 45 | 3 | 2 | 40 | +0.022 [-0.067, +0.111] | 0.65 |
| Backbone B (Qwen-27B) | shifted_test | reuse_prompt − random | 45 | 4 | 2 | 39 | +0.044 [-0.067, +0.156] | 0.41 |
| Backbone B (Qwen-27B) | shifted_test | reuse_full − free | 45 | 1 | 1 | 43 | +0.000 [-0.067, +0.067] | 1.00 |
| Backbone B (Qwen-27B) | shifted_test | reuse_routing − free | 45 | 1 | 6 | 38 | −0.111 [-0.222, +0.000] | 0.06 |
| Backbone B (Qwen-27B) | test | reuse_prompt − free | 60 | 8 | 4 | 48 | +0.067 [-0.050, +0.183] | 0.25 |
| Backbone B (Qwen-27B) | test | reuse_prompt − random | 60 | 8 | 3 | 49 | +0.083 [-0.017, +0.183] | 0.13 |
| Backbone B (Qwen-27B) | test | reuse_full − free | 60 | 5 | 1 | 54 | +0.067 [+0.000, +0.150] | 0.10 |
| Backbone B (Qwen-27B) | test | reuse_routing − free | 60 | 3 | 5 | 52 | −0.033 [-0.117, +0.050] | 0.48 |
| Backbone C (Qwen-9B) | shifted_test | reuse_prompt − free | 45 | 5 | 12 | 28 | −0.156 [-0.333, +0.022] | 0.09 |
| Backbone C (Qwen-9B) | shifted_test | reuse_prompt − random | 45 | 2 | 5 | 38 | −0.067 [-0.178, +0.044] | 0.26 |
| Backbone C (Qwen-9B) | shifted_test | reuse_full − free | 45 | 4 | 10 | 31 | −0.133 [-0.289, +0.022] | 0.11 |
| Backbone C (Qwen-9B) | shifted_test | reuse_routing − free | 45 | 2 | 9 | 34 | −0.156 [-0.289, -0.022] | 0.03 |
| Backbone C (Qwen-9B) | test | reuse_prompt − free | 60 | 3 | 11 | 46 | −0.133 [-0.250, -0.017] | 0.03 |
| Backbone C (Qwen-9B) | test | reuse_prompt − random | 60 | 5 | 10 | 45 | −0.083 [-0.200, +0.050] | 0.20 |
| Backbone C (Qwen-9B) | test | reuse_full − free | 60 | 7 | 8 | 45 | −0.017 [-0.150, +0.117] | 0.80 |
| Backbone C (Qwen-9B) | test | reuse_routing − free | 60 | 7 | 8 | 45 | −0.017 [-0.150, +0.117] | 0.80 |

Note: matched pairs are indexed by (seed, task_id) so `n` = number of tasks
in the split times the number of seeds. On `shifted_test` this is 15×3=45,
on `test` it is 20×3=60. **Backbone A rows currently show n=30 (shifted) /
n=40 (test) because only seeds 712 and 713 are available; expected n=45 /
n=60 after seed 714 is added.**
