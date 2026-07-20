# Domain 2 Plan: Game-Theoretic Persona Tasks

## Why This Domain

Domain 1 shows that organizational assets are useful when reused selectively, especially through prompt-channel asset reuse. Domain 2 tests the same principle in a setting that is more explicitly multi-agent: agents face repeated strategic interactions where persona, reciprocity, social welfare, and equilibrium behavior are directly measurable.

The goal is not to build a leaderboard benchmark. The goal is a low-cost, interpretable phenomenon study:

> Do persona and trajectory-derived strategy assets change cooperative behavior, payoff, and social welfare in repeated social dilemmas?

## Recommended Starting Point

Start with programmatic classical games rather than a heavy external dataset:

1. Iterated Prisoner's Dilemma
2. Public Goods Game

Reasons:

- The action spaces are tiny and cheap to evaluate.
- Cooperation rate, average payoff, social welfare, and Nash-deviation rate are well defined.
- The tasks directly expose the multi-agent/persona part of the paper.
- We can generate variants by changing horizon, number of players, multiplier, and persona mix.

## Current Minimal Implementation

Implemented files:

- `data/tasks_game/social_dilemmas.json`
- `configs/experiments_game_mock.json`
- `configs/experiments_game.json`
- `src/games/evaluator.py`
- `src/runners/run_game_domain.py`
- `scripts/aggregate_game_results.py`
- `scripts/generate_game_paper_assets.py`
- `docs/domain2_game_experiment_draft.md`

Mock command:

```powershell
python -m src.runners.run_game_domain --config configs/experiments_game_mock.json --run-prefix game_domain_mock_20260718
```

Outputs:

- `results/tables/game_domain_summary.md`
- `results/tables/game_domain_summary.csv`
- trajectories under `trajectories/game_domain_*`

## Current Conditions

- `no_persona`: agents receive no explicit persona and the mock policy defaults to individually rational defection/free-riding.
- `persona`: agents receive heterogeneous personas such as cooperative norm follower, self-interested maximizer, reciprocal player, and conditional cooperator.
- `reuse_assets`: agents receive trajectory-derived strategy assets, such as starting cooperatively, using reciprocity, and returning legal action tokens.

The current mock result is only a pipeline sanity check. It should not be reported as empirical evidence.

## Metrics

- `cooperation_rate`: fraction of cooperative actions.
- `average_payoff`: mean payoff per agent-round.
- `social_welfare`: total payoff over all rounds.
- `nash_deviation_rate`: fraction of cooperative/pro-social departures from the one-shot dominant equilibrium. For Prisoner's Dilemma and binary Public Goods, this equals the cooperation rate; it is useful as a compact measure of prosocial non-equilibrium behavior.

## External Benchmarks to Consider Later

These are useful for related work or for a later stronger Domain 2, but they are not necessary for the first minimal experiment.

- GAMA-Bench: dynamic classical game-theory benchmark for multi-agent LLM decision-making.
- GT-HarmBench: 2x2 game-theoretic scenarios in AI-risk contexts, useful if we want realistic narrative games.
- CooperBench / CoLLAB: broader coordination benchmarks for agent teams, useful as related work but heavier than the current game-theory scope.

Useful links:

- GAMA-Bench paper page: https://huggingface.co/papers/2403.11807
- GAMA-Bench code: https://github.com/CUHK-ARISE/GAMABench
- GT-HarmBench dataset: https://huggingface.co/datasets/Jinesis/gt-harmbench
- CoopEval overview: https://www.alphaxiv.org/abs/2604.15267

## Next Step

The first real-API smoke tests with prefixes `game_domain_api_smoke_20260718` and `game_domain_api_smoke_fix_20260718` completed, but they exposed a configuration issue rather than a reliable behavioral signal: many DeepSeek calls returned empty content with `finish_reason=length` because the output budget was consumed by reasoning tokens. Empty outputs were parsed as the default non-cooperative action, artificially depressing cooperation rates.

The configuration has therefore been updated to `temperature=0.0` and `max_tokens=512`, game history is compressed into action-only summaries, invalid actions are retried once with a minimal prompt, and the evaluator records `invalid_action_rate` instead of silently treating invalid outputs as meaningful behavior.

The retry smoke test with prefix `game_domain_api_smoke_retry_20260718` passed the protocol check: all actions were legal and `invalid_action_rate=0` in all six runs. That early protocol used fixed strategy prompts and has been superseded by the trajectory-derived asset protocol below.

Use both `test` and `shifted_test` splits:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_game_asset_protocol.ps1 -Config configs/experiments_game.json -Seeds 712,713,714 -Prefix game_asset_protocol_api_20260720
```

The output budget is modest because each decision returns one action token, but DeepSeek may consume reasoning tokens internally, so `max_tokens=512` is retained.

## Formal Mini-Run Status

The formal trajectory-derived asset run with prefix `game_asset_protocol_api_20260720` completed successfully:

- 36 held-out runs: 3 seeds x 2 splits x 2 games x 3 settings.
- 6 source runs: 3 seeds x 2 train games, used for trajectory-derived strategy asset extraction.
- `invalid_action_rate=0` for every run.
- All game-action API calls ended with `finish_reason=stop`.
- Aggregated output: `results/tables/game_domain_aggregate.md`.
- Paper figures:
  - `results/figures/game_domain_cooperation.svg`
  - `results/figures/game_domain_payoff.svg`
- Paper tables:
  - `results/tables/paper_game_main_results.md`
  - `results/tables/paper_game_main_results.tex`
  - `results/tables/paper_game_cooperation_deltas.md`
  - `results/tables/paper_game_cooperation_deltas.tex`
- Draft experiment section: `docs/domain2_game_experiment_draft.md`.

Current interpretation:

- Public Goods is the cleanest Domain 2 signal: both `test` and `shifted_test` show `no_persona < persona < reuse_assets` for cooperation, average payoff, and social welfare.
- IPD is saturated or near-saturated: persona reaches 1.000 cooperation on test IPD, and all settings reach 1.000 on shifted IPD.
- The safest paper claim is therefore: trajectory-derived strategy assets transfer beyond code repair and improve Public Goods cooperation in a controlled repeated-games domain, while matching persona prompting in saturated IPD settings.

To regenerate the paper assets:

```powershell
python scripts/generate_game_paper_assets.py
```
