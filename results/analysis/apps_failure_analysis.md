# APPS Failure Analysis

This report is generated from formal APPS protocol runs only. Runs whose names contain `smoke`, `mock`, or `preflight` are excluded.

## 1. Current Position

- Formal evaluated attempts: 630.
- Complete protocol coverage: 3 seeds x 2 held-out splits x 6 settings.
- The `test` split is close to saturation; `shifted_test` has clearer separation between settings.

## 2. Success Rates

| split | setting | attempts | success | failures | success rate |
|---|---:|---:|---:|---:|---:|
| shifted_test | free | 45 | 31 | 14 | 68.9% |
| shifted_test | manual | 45 | 28 | 17 | 62.2% |
| shifted_test | random | 45 | 34 | 11 | 75.6% |
| shifted_test | reuse_prompt | 45 | 37 | 8 | 82.2% |
| shifted_test | reuse_routing | 45 | 35 | 10 | 77.8% |
| shifted_test | reuse_full | 45 | 29 | 16 | 64.4% |
| test | free | 60 | 54 | 6 | 90.0% |
| test | manual | 60 | 56 | 4 | 93.3% |
| test | random | 60 | 51 | 9 | 85.0% |
| test | reuse_prompt | 60 | 55 | 5 | 91.7% |
| test | reuse_routing | 60 | 50 | 10 | 83.3% |
| test | reuse_full | 60 | 51 | 9 | 85.0% |

## 3. Reuse vs Free

Counts below compare each reuse setting against `free` on the same split, seed, and task.

| split | setting | rescued | hurt | both passed | both failed | net rescued-hurt |
|---|---:|---:|---:|---:|---:|---:|
| shifted_test | reuse_prompt | 8 | 2 | 29 | 6 | 6 |
| shifted_test | reuse_routing | 8 | 4 | 27 | 6 | 4 |
| shifted_test | reuse_full | 5 | 7 | 24 | 9 | -2 |
| test | reuse_prompt | 5 | 4 | 50 | 1 | 1 |
| test | reuse_routing | 2 | 6 | 48 | 4 | -4 |
| test | reuse_full | 2 | 5 | 49 | 4 | -3 |

## 4. Failure Modes

| split | setting | failure type | count | share of failures | share of attempts |
|---|---:|---:|---:|---:|---:|
| shifted_test | free | empty_or_missing_patch | 13 | 92.9% | 28.9% |
| shifted_test | free | syntax_error | 1 | 7.1% | 2.2% |
| shifted_test | manual | empty_or_missing_patch | 15 | 88.2% | 33.3% |
| shifted_test | manual | syntax_error | 1 | 5.9% | 2.2% |
| shifted_test | manual | wrong_output | 1 | 5.9% | 2.2% |
| shifted_test | random | empty_or_missing_patch | 10 | 90.9% | 22.2% |
| shifted_test | random | syntax_error | 1 | 9.1% | 2.2% |
| shifted_test | reuse_full | empty_or_missing_patch | 14 | 87.5% | 31.1% |
| shifted_test | reuse_full | syntax_error | 1 | 6.2% | 2.2% |
| shifted_test | reuse_full | wrong_output | 1 | 6.2% | 2.2% |
| shifted_test | reuse_prompt | empty_or_missing_patch | 4 | 50.0% | 8.9% |
| shifted_test | reuse_prompt | syntax_error | 2 | 25.0% | 4.4% |
| shifted_test | reuse_prompt | wrong_output | 2 | 25.0% | 4.4% |
| shifted_test | reuse_routing | empty_or_missing_patch | 8 | 80.0% | 17.8% |
| shifted_test | reuse_routing | wrong_output | 2 | 20.0% | 4.4% |
| test | free | empty_or_missing_patch | 2 | 33.3% | 3.3% |
| test | free | wrong_output | 4 | 66.7% | 6.7% |
| test | manual | empty_or_missing_patch | 2 | 50.0% | 3.3% |
| test | manual | wrong_output | 2 | 50.0% | 3.3% |
| test | random | empty_or_missing_patch | 8 | 88.9% | 13.3% |
| test | random | wrong_output | 1 | 11.1% | 1.7% |
| test | reuse_full | empty_or_missing_patch | 2 | 22.2% | 3.3% |
| test | reuse_full | runtime_error | 1 | 11.1% | 1.7% |
| test | reuse_full | syntax_error | 2 | 22.2% | 3.3% |
| test | reuse_full | wrong_output | 4 | 44.4% | 6.7% |
| test | reuse_prompt | empty_or_missing_patch | 4 | 80.0% | 6.7% |
| test | reuse_prompt | wrong_output | 1 | 20.0% | 1.7% |
| test | reuse_routing | empty_or_missing_patch | 5 | 50.0% | 8.3% |
| test | reuse_routing | syntax_error | 2 | 20.0% | 3.3% |
| test | reuse_routing | wrong_output | 3 | 30.0% | 5.0% |

## 5. Typical Contrasts

### shifted_test: prompt reuse helps

- seed 712 / `apps_shifted_test_test_0000`: free failed as `empty_or_missing_patch`, prompt reuse passed.
- seed 712 / `apps_shifted_test_test_0003`: free failed as `empty_or_missing_patch`, prompt reuse passed.
- seed 712 / `apps_shifted_test_test_0007`: free failed as `empty_or_missing_patch`, prompt reuse passed.
- seed 712 / `apps_shifted_test_test_0008`: free failed as `empty_or_missing_patch`, prompt reuse passed.
- seed 713 / `apps_shifted_test_test_0001`: free failed as `empty_or_missing_patch`, prompt reuse passed.

### shifted_test: full reuse can hurt

- seed 712 / `apps_shifted_test_test_0012`: free passed, full reuse failed as `empty_or_missing_patch`.
- seed 713 / `apps_shifted_test_test_0008`: free passed, full reuse failed as `syntax_error`.
- seed 713 / `apps_shifted_test_test_0012`: free passed, full reuse failed as `empty_or_missing_patch`.
- seed 714 / `apps_shifted_test_test_0001`: free passed, full reuse failed as `empty_or_missing_patch`.
- seed 714 / `apps_shifted_test_test_0007`: free passed, full reuse failed as `empty_or_missing_patch`.

### test: saturation limits interpretability

- seed 712 / `apps_test_test_4001`: prompt reuse rescued a free failure, but the aggregate split remains high for most settings.
- seed 712 / `apps_test_test_4003`: prompt reuse rescued a free failure, but the aggregate split remains high for most settings.
- seed 712 / `apps_test_test_4012`: prompt reuse rescued a free failure, but the aggregate split remains high for most settings.
- seed 714 / `apps_test_test_4001`: prompt reuse rescued a free failure, but the aggregate split remains high for most settings.
- seed 714 / `apps_test_test_4018`: prompt reuse rescued a free failure, but the aggregate split remains high for most settings.

## 6. Interpretation for the Paper

### Story calibration

Overall, the current APPS result is positive for the paper story, but it supports a calibrated version of the story rather than a blanket "organizational assets always help" claim.

A suitable claim is: persistent organizational assets can improve multi-agent code-repair robustness when they are reused selectively. In the current evidence, prompt-level procedural assets are the clearest positive component; routing-only assets are mildly positive on the shifted split; full reuse is unstable and can hurt because it may over-constrain the team or interfere with patch handoff.

This makes the negative `reuse_full` result useful rather than fatal: it motivates the paper's emphasis on decomposing organizational assets and evaluating which asset type should be reused under distribution shift.

### Evidence-backed interpretation

- The strongest current evidence is not that all organizational assets help uniformly. The more defensible claim is narrower: reusable prompt-level organizational assets improve robustness under the shifted APPS split.
- `reuse_prompt` is consistently strongest on `shifted_test`, while `reuse_full` is unstable. This suggests that injecting distilled procedural knowledge helps, but forcing both prompt reuse and asset-based routing may over-constrain the team on unfamiliar tasks.
- `reuse_routing` also improves over `free` on `shifted_test`, but less than `reuse_prompt`. This is useful for an ablation story: content-level reuse appears more valuable than routing-only reuse in this code-repair setup.
- The `test` split should be treated as a sanity split rather than the main evidence source because baseline success is already high.
- The most visible shifted-split failure mode is `empty_or_missing_patch`: the team often localizes or reviews a bug but fails to hand the evaluator an executable patch. Prompt reuse reduces this failure mode sharply on `shifted_test`.
- Once a substantive patch is produced, remaining failures are mostly wrong-output or syntax errors. This supports a mechanism story in which organizational assets primarily stabilize the collaboration protocol and patch handoff, rather than simply making the model a stronger programmer.

## 7. Case Notes

- `apps_shifted_test_test_0000`: in seed 712, `free` produced no localization and no patch, while both `reuse_prompt` and `reuse_routing` localized the bracket/colon search bug and produced passing accordion parsers. This is a clean rescue case for reusable procedural guidance.
- `apps_shifted_test_test_0003`: `free` failed with empty patches in all three seeds. `reuse_prompt` passed in two of three seeds by turning the repair into an explicit coverage-prefix computation; the remaining failure was wrong output, not missing handoff.
- `apps_shifted_test_test_0012`: `free` passed in all three seeds, but `reuse_full` failed in all three seeds with empty patches. This is the clearest warning that full asset reuse can over-constrain the run or interfere with patch handoff.

## 8. Recommended Next Steps

1. Use `shifted_test` as the main result table in the paper draft; report `test` as sanity/near-saturation evidence.
2. Add one compact figure/table for `reuse_prompt` and `reuse_routing` net rescue counts against `free`.
3. Manually inspect 3-5 rescued tasks and 2-3 hurt tasks before writing claims about mechanism.
4. Defer Domain 2 until after the APPS story is drafted; add it only if the paper still needs a more explicitly multi-agent/persona-flavored experiment.

## 9. Generated Files

- `results/analysis/apps_failure_items.csv`: one row per task attempt.
- `results/analysis/apps_failure_modes.csv`: failure-type counts by split and setting.
- `results/analysis/apps_reuse_vs_free.csv`: per-task reuse/free contrasts.
- `results/analysis/apps_task_matrix.csv`: per-task success counts across settings.
