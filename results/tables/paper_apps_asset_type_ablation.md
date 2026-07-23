# APPS Asset-Type Ablation (Prompt Channel, Qwen3.6-27B)

Within the prompt-channel reuse strategy, we restrict the loaded asset
set to a single asset type and compare the resulting success rate to
the full-asset Prompt condition (which loads both role and organization
assets) and to the Free baseline.

All runs use Qwen3.6-27B (Backbone B) with 3 seeds (712, 713, 714).

| Split | Asset set | Mean | Min | Max | Δ vs Free | Δ vs Full Prompt |
|---|---|---:|---:|---:|---:|---:|
| shifted_test | Role only | 0.733 | 0.733 | 0.733 | −0.044 | −0.067 |
| shifted_test | Organization only | 0.733 | 0.600 | 0.800 | −0.044 | −0.067 |
| shifted_test | **Full (role + org)** | 0.800 | – | – | +0.022 | (ref) |
| shifted_test | *Free (no assets)* | 0.778 | – | – | (ref) | – |
| test | Role only | 0.750 | 0.650 | 0.800 | −0.033 | −0.100 |
| test | Organization only | 0.783 | 0.700 | 0.850 | −0.000 | −0.067 |
| test | **Full (role + org)** | 0.850 | – | – | +0.067 | (ref) |
| test | *Free (no assets)* | 0.783 | – | – | (ref) | – |

Reading:
- On both splits, restricting Prompt to a single asset type
  (role-only or organization-only) *does not* improve over Free and
  is worse than the full-asset Prompt condition. The role and
  organization assets appear to act complementarily rather than as
  independent contributors.
- This dissociates the effect: the observed Prompt-vs-Free gap on this
  backbone is not driven by any single asset type, and the
  full-asset Prompt condition is what carries the improvement.
