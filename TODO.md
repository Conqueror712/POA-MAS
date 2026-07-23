# ORCA Paper — TODO List

_Last updated: 2026-07-23_

Forward-looking checklist for the AAAI-27 submission. Completed work is captured
in `Checkpoint.md`; this file only lists open items.

---

## 1. Pre-submission blockers (must be done before uploading to OpenReview)

These are AAAI-27 format hygiene items. None of them require content decisions.

- [ ] **B1. Inline-expand `\input{tables/...}`** into a single `ORCA.tex`.
      AAAI-27 explicitly forbids `\input` for anything other than the `.bib`
      file (see `AuthorKit27_Ori/AnonymousSubmission2027.tex` §"What Files to
      Submit"). Use `latexpand ORCA.tex > ORCA_flat.tex` or an equivalent
      one-shot script. Do this **last** to keep the working tree editable.
- [ ] **B2. Strip PDF metadata** on the final Overleaf export:
      `exiftool -all= ORCA.pdf` (or `qpdf --linearize --replace-input`).
      Overleaf otherwise embeds account info that violates double-blind.
- [ ] **B3. Trim the submission zip** so it contains only files used to
      compile the paper. Delete:
      - `AuthorKit27/AnonymousSubmission2027.*`, `CameraReady2027.*`,
        `aaai2027.bib` (all AAAI template samples)
      - `AuthorKit27/Word/`
      - `AuthorKit27/Figures/figure1.pdf`, `figure2.pdf` (template sample figs)
      - `AuthorKit27/missfont.log`, older `ORCA.pdf`
      `AuthorKit27_round3.zip` already reflects this cleaned layout.
- [ ] **B4. Update the significance-table caption**:
      `AuthorKit27/tables/paper_apps_significance.tex` currently ends with
      "Backbone A currently uses seeds 712 and 713; seed 714 to be added."
      Either add seed 714 first, or rewrite the sentence to remove the
      "to be added" wording so reviewers do not see an in-progress signal.
- [ ] **P1. Cut one page**: AAAI-27 is a hard 7-page body limit. Current V4 is
      8 pages. Options: shorten Related Work; drop `paper_apps_reuse_contrast`
      table (Table 2) since matched-pair counts are also reported inline;
      shrink Figure 1 mechanism diagram. Decide once B1-B4 are queued so we can
      see the true final layout.

## 2. Data completeness (not blocking, but nice to close)

- [ ] **Recover DeepSeek APPS seed-714 trajectories** from user's local machine.
      Paper text says "3 seeds: 712, 713, 714" but the local `trajectories/`
      only contains 712/713. The 3-seed aggregate numbers in the paper (0.689
      free, 0.822 prompt, 13/45 empty, etc.) are correct — they come from
      `results/analysis/apps_failure_analysis.md`, which was generated when
      seed 714 was still on disk. Recovering the raw trajectories will let
      `scripts/statistical_tests.py` update Table 3 from n=30 (2-seed) to
      n=45 (3-seed) — expected effect: Backbone-A shifted-split Prompt-vs-Free
      p-value drops from 0.10 towards <0.05.
- [ ] **Recover DeepSeek Domain 2 (games) trajectories** from user's local
      machine, plus `assets/game_assets/latest_strategy_assets.json`. The
      final Domain 2 numbers in the paper are frozen in
      `results/tables/paper_game_main_results.tex` so they are not at risk,
      but reviewers may request raw trajectories for reproducibility audit.

## 3. Content extensions (only if time allows)

Every item here is optional. The paper is submission-ready without them if
B1-B4 and P1 are cleared.

- [ ] **3.1 Second code benchmark**. MBPP has been built
      (`data/tasks_code/mbpp_repair.json`, 15/15/15) but a Qwen3.6-27B smoke
      test on `test/free` gave 5/5 pass — MBPP saturates like HumanEval.
      SWE-bench-lite would be discriminative but requires docker sandboxing
      and is out of scope for the current window.
- [ ] **3.2 Additional LLM backbone**. Currently 1 closed-API + 2 open-weights.
      Adding a fourth (e.g. Llama-3.3-70B) would strengthen scale-dependent
      claim, but marginal-return low given Backbone B is already at +0.022.
- [ ] **3.3 Games cross-model on Backbone C (9B)**. Not run. Symmetry with
      the APPS 9B negative would be tidy, but does not change the story.
- [ ] **3.4 Asset-type ablation on Backbone A**. Currently only Backbone B has
      role-only / organization-only conditions. Doing this on DeepSeek would
      let us claim the super-additive effect is not backbone-specific.

## 4. Reproducibility Checklist items still marked `partial`

- [ ] **4.1** Confirm `configs/` covers all hyperparameters used in the
      reported runs. If yes, upgrade item **4.2** and **4.13** from `partial`
      to `yes` in `AuthorKit27/ReproducibilityChecklist.tex`.
- [ ] **4.2** Confirm `src/` code comments reference paper sections. If yes,
      upgrade item **4.6** from `partial` to `yes`.

## 5. Camera-ready tasks (only after acceptance)

- [ ] **5.1** Remove `[submission]` from `\usepackage[submission]{aaai2027}`.
- [ ] **5.2** Fill real authors and affiliations (currently
      "Anonymous Submission" / "Anonymous Institution").
- [ ] **5.3** Restore concrete backbone identity ("closed-API production LLM
      family" → actual model name, e.g. `DeepSeek-V4-Flash`).
- [ ] **5.4** Include AAAI copyright form per camera-ready guidelines.
- [ ] **5.5** Optional: promote deleted/collapsed tables (Table 7 asset-type
      ablation, Table 9 game-cooperation deltas) into a Content Appendix
      after the References. Full versions still available in
      `ORCA/results/tables/`.
