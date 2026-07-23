# Domain 2 Cross-Model Cooperation Rate

Cooperation rate on Domain 2 held-out splits, averaged over 3 seeds.
Backbone A = closed-API production LLM family (paper Table 5).
Backbone B = Qwen3.6-27B via local vLLM (this run,
`game_asset_qwen27b_20260723_*`).

| Split | Game | Setting | Backbone A | Backbone B | Δ (B−A) |
|---|---|---|---:|---:|---:|
| test | PG | no_persona | 0.611 | 1.000 | +0.389 |
| test | PG | persona | 0.750 | 0.833 | +0.083 |
| test | PG | reuse_assets | 0.986 | 0.833 | −0.153 |
| test | IPD | no_persona | 0.854 | 1.000 | +0.146 |
| test | IPD | persona | 1.000 | 1.000 | +0.000 |
| test | IPD | reuse_assets | 0.979 | 1.000 | +0.021 |
| shifted_test | PG | no_persona | 0.056 | 0.000 | −0.056 |
| shifted_test | PG | persona | 0.767 | 0.800 | +0.033 |
| shifted_test | PG | reuse_assets | 0.833 | 0.800 | −0.033 |
| shifted_test | IPD | no_persona | 1.000 | 1.000 | +0.000 |
| shifted_test | IPD | persona | 1.000 | 1.000 | +0.000 |
| shifted_test | IPD | reuse_assets | 1.000 | 1.000 | +0.000 |

Interpretation summary:
- **PG shifted_test**: on Backbone A, reuse (0.833) improves over persona (0.767)
  and sharply over no_persona (0.056). On Backbone B, reuse (0.800) matches persona (0.800)
  and both remain far above no_persona (0.000). The persona→no_persona gap replicates,
  but the reuse-over-persona increment does not.
- **PG test**: on Backbone A, reuse (0.986) is the best condition. On Backbone B,
  no_persona (1.000) is already saturated; reuse (0.833) does not improve on it.
- **IPD**: saturated near 1.000 on both backbones across all conditions, uninformative
  for reuse comparison.
