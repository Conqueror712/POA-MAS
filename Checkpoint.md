# ORCA Checkpoint

_最后更新：2026-07-23_

本项目最新提交版本对应论文：
**ORCA: Organizational Reuse of Coordination Assets for Multi-Agent LLM Systems**
（AAAI-27 投稿，`../AuthorKit27/ORCA.tex`）

---

## Phase 摘要

| Phase | 状态 | 关键产出 |
|---|---|---|
| **A. 主题确认** | ✅ 完成 | 标题、abstract 定稿；`docs/title_abstract_candidates.md`；主论文 draft `docs/orca_main_paper_draft.md` |
| **B. 最小实验闭环** | ✅ 完成 | multi-agent code-repair pipeline + DeepSeek/mock/vLLM 三种 LLM client + free/manual/random/reuse 四种控制器 + trajectory logging + stdin/stdout evaluator + APPS 一键脚本 |
| **C. Domain 1 主实验 (APPS repair)** | ✅ 完成（DeepSeek 3-seed 结果已入正文）| APPS 子集 20/20/15；3 seeds × 6 settings × 2 splits = 36 runs；主结果表 `results/tables/paper_apps_main_results.md` |
| **D. Domain 1 失败分析** | ✅ 完成 | matched-pair rescue/hurt 表；failure-mode 分类；`results/analysis/apps_failure_*.{md,csv}` |
| **E. Domain 2 (Repeated Games)** | ✅ 完成（DeepSeek 3-seed 已入正文）| IPD + Public Goods；no_persona/persona/reuse_assets；主结果表 `results/tables/paper_game_main_results.md` |
| **F. Cross-model 稳健性 (Qwen 9B & 27B)** | ✅ 完成，已入正文 §3.5 | vLLM 后端 + `VLLMClient`；APPS 各 39 runs；`results/tables/paper_apps_cross_model.{md,tex}` |
| **G. Review-driven strengthening (2026-07-23)** | ✅ 完成，已入正文 §3.2/3.3/3.6/4.3 | Wilcoxon 显著性、asset-type ablation、Domain 2 cross-model、Related Work 补 8 篇 |

---

## 当前关键结果快照（Backbone A / DeepSeek，3 seeds）

| Setting | shifted_test | test |
|---|---:|---:|
| Free | 0.689 | 0.900 |
| Manual | 0.622 | 0.933 |
| Random | 0.756 | 0.850 |
| **Prompt (reuse)** | **0.822** | 0.917 |
| Routing (reuse) | 0.778 | 0.833 |
| Full (reuse) | 0.644 | 0.850 |
| **Prompt − Free** | **+0.133** | +0.017 |

**Empty/missing patch failures** (shifted_test)：Free 13/45 → Prompt 4/45

**Games (Public Goods) cooperation rate**：no-persona 0.611/0.056 → reuse 0.986/0.833（test/shifted）

**Cross-model on shifted_test (Backbones A/B/C)**：Prompt-vs-Free = +0.133 / +0.022 / −0.156（scale-dependent）

**Significance (matched Wilcoxon on shifted_test, Prompt−Free)**：Backbone A p=0.10；样本量 n=45 相对小，正文已明说依赖 rescue/hurt counts 作为主要证据

---

## 论文当前状态

- 主 tex：`../AuthorKit27/ORCA.tex`（V4 版本，8 页正文 + 3 页 refs，`AuthorKit27_round3.zip` 是清理干净的提交候选）
- Reproducibility Checklist：`../AuthorKit27/ReproducibilityChecklist.tex`（25 项已填）
- 已进入 tex 的新内容：significance 表、asset-type ablation（inline 段落）、Domain 2 cross-model 表
- 论文规范核对：与 `AuthorKit27_Ori/` 官方 template bit-perfect 一致（sty/bst 未改）

## 尚待处理（详见 `TODO.md`）

- **B1** `\input{tables/...}` inline 展开成单文件（AAAI 官方要求 single tex）
- **B2** PDF metadata 匿名清洗（`exiftool -all=`）
- **B3** 打包时清理冗余源（`AnonymousSubmission2027.*` / `Word/` / 未用图片等）
- **B4** significance 表 caption 里 "seed 714 to be added" 措辞
- **P1** 页数决策：AAAI-27 = 7 页硬限制，V4 是 8 页 → 需再砍 1 页
- **数据待补**：DeepSeek APPS seed 714 trajectories + DeepSeek Domain 2 trajectories（用户回本地电脑取；不 blocking 论文数字，但影响本地可复现性）

## Domain / Backbone 覆盖矩阵

| | Domain 1 (APPS) | Domain 2 (Games) |
|---|---|---|
| Backbone A (DeepSeek-V4-Flash) | ✅ 3 seeds（trajectories 本地仅 712/713）| ✅ 3 seeds（trajectories 本地缺，数字在 tex 里固化）|
| Backbone B (Qwen3.6-27B) | ✅ 3 seeds + asset-type ablation | ✅ 3 seeds（本 session 新跑）|
| Backbone C (Qwen3.5-9B) | ✅ 3 seeds（scale-dependent 负例）| ⭕ 未跑（不 blocking，正文只谈 B 上的 cross-model）|

## 文件位置

- 源码：`src/`（agents, controller, eval, runners, assets, utils）
- 脚本：`scripts/`（build_*_repair, run_*_protocol, aggregate_*, analyze_*, statistical_tests）
- 配置：`configs/experiments_{apps,humaneval,mbpp,game,expanded,semantic}[_qwen{9b,27b}][_mock].json`
- 数据：`data/tasks_{code,game}/`
- 测试：`tests/`（17 项单测覆盖 LLM client / asset extractor / controller）
- 论文表格与图：`results/tables/`（10 个 tex + md）、`results/figures/`（6 个 svg + 生成 pdf 脚本）
- 论文源：`../AuthorKit27/`（同级目录，独立管理）
