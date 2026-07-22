# ORCA Paper — TODO List

_Last updated: 2026-07-22_

This file tracks all remaining work for the ORCA AAAI-27 submission. It covers
substantive experimental extensions, small polish items, and the fixed pre-submission
checklist. Items are grouped by the phase in which they should be handled.

---

## 1. Experimental extensions (blocking claims strength)

These are the items you plan to run before final submission. They directly address
reviewer risks flagged during the current pass (single-model, small benchmark).

- [ ] **1.1 Add at least one additional code-repair benchmark** (e.g. HumanEval,
      MBPP subset, or a small SWE-bench subset). This is the single most impactful
      addition: the current APPS-only evaluation is the first thing an AAAI reviewer
      will flag.
- [ ] **1.2 Add at least one additional LLM family** (e.g. one closed API + one
      open-weights model) on both APPS and the games. This unlocks a cross-model
      robustness claim and directly addresses the current Limitations paragraph.
- [ ] **1.3 Update tables and figures** in `ORCA/results/` after re-running with
      new benchmarks / models. Regenerate SVGs and re-run `python3 /tmp/svg2pdf.py`
      to refresh the PDFs under `AuthorKit27/Figures/`.
- [ ] **1.4 Refresh numeric claims** in `AuthorKit27/ORCA.tex` and the abstract
      once new data lands (currently: 68.9% → 82.2%, 13/45 → 4/45, etc.).

## 2. Writing polish that depends on §1

Do these together with §1 — they only make sense once new data is in.

- [ ] **2.1 Add an `algorithm` block** for asset extraction inside §2.3 or §2.4.
      Preamble already loads `algorithm` and `algorithmic`. After this, upgrade
      Reproducibility Checklist item **1.1** from `partial` to `yes`.
- [ ] **2.2 Add a Wilcoxon signed-rank test** (or paired bootstrap) on the
      matched shifted-split contrast in §3.3. After this, upgrade Checklist
      item **4.12** from `no` to `yes` (or `partial` if only one contrast is
      tested).
- [ ] **2.3 Consider a small "Implementation Details" subsection** in §2 once
      Wilcoxon and the algorithm block are in — it will naturally consume any
      leftover space on page 7.

## 3. Reproducibility Checklist follow-up

These are the two items I left as `partial` pending your review of the repo.

- [ ] **3.1 Confirm `configs/` covers all hyperparameters used in the reported
      runs.** If yes, upgrade Checklist item **4.2** (hyperparameter search) and
      item **4.13** (final hyperparameter list) from `partial` to `yes`. Edit
      `AuthorKit27/ReproducibilityChecklist.tex`.
- [ ] **3.2 Confirm `src/` code comments reference paper sections.** If yes,
      upgrade Checklist item **4.6** from `partial` to `yes`.

(Item **4.8** — computing infrastructure — was upgraded to `yes` on 2026-07-22,
along with a one-sentence addition to §3.1 of the paper.)

## 4. Mandatory pre-submission tasks

None of these require content decisions; they are format/hygiene only.

- [ ] **4.1 Strip PDF metadata** on the final export from Overleaf:
      `exiftool -all= ORCA.pdf` (or use another metadata cleaner). AAAI-27
      explicitly requires this for anonymous submissions.
- [ ] **4.2 Attach `ReproducibilityChecklist.pdf` separately** on the OpenReview
      submission form (do not `\input` it into `ORCA.tex`; AAAI-27 typically has
      a dedicated attachment slot).
- [ ] **4.3 Sanity check compile once on Overleaf** with pdfLaTeX + BibTeX after
      the final content pass, to catch any local file that failed to sync.

## 5. Camera-ready tasks (only after acceptance)

Do not touch these until a decision is in.

- [ ] **5.1 Remove `[submission]`** from `\usepackage[submission]{aaai2027}` in
      `ORCA.tex`.
- [ ] **5.2 Fill real authors and affiliations**, replacing
      `Anonymous Submission` / `Anonymous Institution`.
- [ ] **5.3 Restore the concrete model name** in §3.1 (currently `"a single
      production LLM family"`; the draft in `ORCA/docs/orca_main_paper_draft.md`
      still records `DeepSeek-V4-Flash`).
- [ ] **5.4 Confirm AAAI copyright block** on page 1 per the camera-ready
      instructions (remove no-copyright options, add signed copyright form).

## 6. Completed (kept for reference)

- [x] SVG → PDF conversion for 6 figures (`AuthorKit27/Figures/`).
- [x] Main tex compiles cleanly on pdfLaTeX (8 pages: 7 body + 1 refs page).
- [x] Bibliography expanded to 23 entries, including collaborator-flagged works
      (ExpeL, SWE-agent, AutoCodeRover) and reviewer-visible references
      (SWE-bench, Agentless, CoALA, MoA, DyLAN, GovSim).
- [x] Related Work restructured into 4 subsections and moved to appear right
      after §1 Introduction (AAAI-conventional placement).
- [x] Selective-reuse terminology anchored in abstract, intro, and discussion.
- [x] Modest-tone hedges tightened; Conclusion extended with a `future work`
      paragraph.
- [x] Table 5 (Domain 2 main results): welfare rendered as integers; the
      all-zero `Invalid` column removed with a footnote.
- [x] Table `p{}` layout + `table*` spanning fixes for the 4 wide tables to
      remove overfull hboxes.
- [x] `ReproducibilityChecklist.tex` filled with 25 answers.
- [x] `AuthorKit27/orca.bib` and the reference-copies under `ORCA/` kept in sync.
- [x] Overleaf-ready zip refreshed: `DEV_ORCA/ORCA_for_overleaf.zip`.

---

## File map

| Path | Purpose |
|---|---|
| `AuthorKit27/ORCA.tex` | Main paper (source of truth for submission) |
| `AuthorKit27/orca.bib` | Bibliography (23 entries) |
| `AuthorKit27/tables/` | Six table `.tex` files (mirror of `ORCA/results/tables/`) |
| `AuthorKit27/Figures/` | Six figure PDFs (converted from `ORCA/results/figures/*.svg`) |
| `AuthorKit27/ReproducibilityChecklist.tex` | Filled checklist, compiles standalone to 2 pages |
| `AuthorKit27/ORCA.pdf` | Latest compiled PDF (8 pages, zero warnings) |
| `ORCA_for_overleaf.zip` | One-click Overleaf upload bundle |
| `ORCA/docs/orca_main_paper_draft.md` | Working markdown draft, kept synced with `ORCA.tex` |
| `ORCA/docs/Related.md` | Collaborator's reference notes (already incorporated) |
| `ORCA/results/tables/*.tex` `.md` | Table sources (mirror of `AuthorKit27/tables/`) |
| `ORCA/results/figures/*.svg` | Figure sources (regenerate PDFs when changed) |
