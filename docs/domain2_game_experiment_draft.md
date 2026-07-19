# Domain 2 Experiment Draft: Repeated Social Dilemmas

This draft is intended as a paper-ready secondary experiment section. The empirical claim is deliberately modest: Domain 2 does not establish benchmark-level generality, but it provides controlled evidence that reusable strategy assets can shape multi-agent behavior in a non-code setting.

## Experiment 2: Strategy Assets in Repeated Social Dilemmas

### Research Question

Domain 1 shows that persistent organizational assets can improve the reliability of a multi-agent code-repair workflow, especially when procedural assets are reused selectively. We next ask whether the same idea appears in a more explicitly multi-agent setting, where agents repeatedly interact with each other and their collective behavior is directly measurable.

The research question is:

> Do persona prompts and reusable strategy assets change cooperation, payoff, and social welfare in repeated social dilemmas?

This experiment is designed as a low-cost phenomenon study rather than a leaderboard benchmark. The goal is to test whether persistent assets can influence stable group behavior when agents face strategic incentives, not to claim state-of-the-art performance on game-theory benchmarks.

### Task Construction

We use two programmatic classical games:

| game | action space | strategic tension |
|---|---|---|
| Iterated Prisoner's Dilemma (IPD) | `C` or `D` | unilateral defection is tempting, but mutual cooperation improves joint payoff |
| Public Goods Game | `CONTRIBUTE` or `KEEP` | each agent benefits from others' contributions while retaining an incentive to free-ride |

For each game, we instantiate a `test` task and a `shifted_test` task. The shifted tasks change game parameters such as horizon, number of players, and payoff multiplier. This gives a small but controlled transfer setting while keeping evaluation deterministic and inexpensive.

All game tasks are automatically evaluated. Each agent must return a legal action token at every round. The evaluator records actions, payoffs, invalid outputs, and aggregate metrics.

### Conditions

We compare three settings:

| setting | description |
|---|---|
| no_persona | Agents receive the game rules and payoff information, but no explicit persona or reusable strategy guidance. |
| persona | Agents receive heterogeneous behavioral descriptions, such as cooperative norm follower, reciprocal player, conditional cooperator, or self-interested maximizer. |
| reuse_assets | Agents receive reusable strategy assets, including compact procedural guidance for legal action formatting, reciprocity, and pro-social coordination. |

The `reuse_assets` condition is intended to test whether persistent organizational memory can act as reusable strategic guidance, rather than merely adding descriptive persona labels.

### Metrics

We report:

- `cooperation_rate`: fraction of cooperative or pro-social actions.
- `average_payoff`: mean payoff per agent-round.
- `social_welfare`: total payoff over all agents and rounds.
- `invalid_action_rate`: fraction of actions that fail to match the legal action space.
- `nash_deviation_rate`: a one-shot equilibrium-deviation proxy. In these binary social dilemmas, it equals the cooperation rate because cooperation/contribution deviates from the one-shot dominant free-riding action.

The primary behavioral metric is cooperation rate. Payoff and social welfare are included to check whether increased cooperation also improves collective outcomes under the instantiated games.

### Main Results

Table 1 reports the formal mini-run results. All runs use DeepSeek-V4-Flash with temperature 0.0. The game-action protocol is stable: every setting has `invalid_action_rate=0`.

![Domain 2 cooperation rates](../results/figures/game_domain_cooperation.svg)

![Domain 2 average payoff](../results/figures/game_domain_payoff.svg)

Generated table files: [Markdown](../results/tables/paper_game_main_results.md), [LaTeX](../results/tables/paper_game_main_results.tex).

| split | game | setting | cooperation | avg. payoff | welfare | invalid |
|---|---|---|---:|---:|---:|---:|
| test | IPD | no_persona | 0.000 | 1.000 | 16.000 | 0.000 |
| test | IPD | persona | 0.312 | 1.938 | 31.000 | 0.000 |
| test | IPD | reuse_assets | **1.000** | **3.000** | **48.000** | 0.000 |
| test | Public Goods | no_persona | 0.167 | 11.000 | 264.000 | 0.000 |
| test | Public Goods | persona | 0.625 | 13.750 | 330.000 | 0.000 |
| test | Public Goods | reuse_assets | **0.958** | **15.750** | **378.000** | 0.000 |
| shifted_test | IPD | no_persona | 1.000 | 3.000 | 60.000 | 0.000 |
| shifted_test | IPD | persona | 0.800 | 2.700 | 54.000 | 0.000 |
| shifted_test | IPD | reuse_assets | **1.000** | **3.000** | **60.000** | 0.000 |
| shifted_test | Public Goods | no_persona | 0.067 | 10.267 | 308.000 | 0.000 |
| shifted_test | Public Goods | persona | 0.767 | 13.067 | 392.000 | 0.000 |
| shifted_test | Public Goods | reuse_assets | **1.000** | **14.000** | **420.000** | 0.000 |

The cleanest result appears in Public Goods. On both `test` and `shifted_test`, cooperation, average payoff, and social welfare follow the same ordering:

> no_persona < persona < reuse_assets

This suggests that persona alone can induce more pro-social behavior, but reusable strategy assets produce the most stable cooperation in this controlled setting.

IPD is more mixed but still informative. On the `test` task, `reuse_assets` moves cooperation from 0.000 under `no_persona` and 0.312 under `persona` to 1.000. On the shifted IPD task, however, `no_persona` already reaches full cooperation, so the split is saturated and cannot provide evidence for an additional reuse benefit. We therefore avoid over-interpreting shifted IPD and treat Public Goods as the stronger Domain 2 signal.

### Cooperation Deltas

Generated delta table files: [Markdown](../results/tables/paper_game_cooperation_deltas.md), [LaTeX](../results/tables/paper_game_cooperation_deltas.tex).

| split | game | persona - no_persona | reuse_assets - no_persona | reuse_assets - persona |
|---|---|---:|---:|---:|
| test | IPD | +0.312 | +1.000 | +0.688 |
| test | Public Goods | +0.458 | +0.792 | +0.333 |
| shifted_test | IPD | -0.200 | +0.000 | +0.200 |
| shifted_test | Public Goods | +0.700 | +0.933 | +0.233 |

The delta analysis supports a cautious interpretation. Reused strategy assets improve cooperation relative to `persona` in all four game/split cells, but the magnitude varies. The most persuasive cells are Public Goods, where reuse improves over no-persona by +0.792 on `test` and +0.933 on `shifted_test`.

### Interpretation

Domain 2 complements the APPS result in two ways. First, it moves beyond code repair into a setting where the outcome is explicitly collective: cooperation and social welfare depend on how agents behave toward each other over repeated interaction. Second, it separates descriptive persona from reusable strategy assets. Persona prompts can change behavior, but reusable assets provide more direct procedural guidance about how to maintain cooperation, reciprocate, and return valid decisions.

The result supports a paper claim of the following form:

> Persistent organizational assets can be reused not only to stabilize task workflows, but also to bias multi-agent groups toward stable pro-social strategies in repeated interaction. However, the effect should be interpreted as controlled phenomenon evidence, not as a broad benchmark result.

This claim is consistent with Domain 1. In both domains, the strongest story is not that more context always helps. The stronger story is that typed, reusable assets can shape later multi-agent behavior when they are aligned with the structure of the new task.

### Limitations

The current Domain 2 experiment is intentionally small: it contains two games and one formal task per split/game pair. The games are programmatically generated rather than drawn from an external benchmark such as GAMA-Bench or GT-HarmBench. This makes the result easy to inspect and cheap to reproduce, but it limits claims about benchmark-level coverage.

The experiment also uses a single model family. Since LLM game behavior is sensitive to model and prompt details, the current result should be framed as secondary evidence for the mechanism. A stronger version would add more game variants, more seeds, and an external benchmark subset after the main paper story is stable.

### Reproduction Artifacts

The Domain 2 paper assets in this section are generated by:

```powershell
python scripts/generate_game_paper_assets.py
```

The script reads `results/tables/game_domain_aggregate.csv`, then writes SVG figures under `results/figures/` and Markdown/LaTeX tables under `results/tables/`.
