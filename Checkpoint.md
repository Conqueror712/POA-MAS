# ORCA Checkpoint

更新时间：2026-07-20

---

## A. Idea 确认阶段

- ✅ 阅读并整理原始共享文档
- ✅ 确认主线：以“可持久化组织资产”为核心，代码修复作为第一实验域
- ✅ 确认 HumanEval 过于简单，不能作为唯一主实验
- ✅ 确认 APPS repair 作为当前代码主实验
- ✅ 起草英文标题与摘要候选：`docs/title_abstract_candidates.md`
- ✅ 人类共同确认最终英文标题：**ORCA: Organizational Reuse of Coordination Assets for Multi-Agent LLM Systems**
- ✅ 人类共同确认摘要主推版本：`docs/title_abstract_candidates.md`
- ✅ 完成主论文 draft v0：`docs/orca_main_paper_draft.md`
- ✅ 将临时测试缓存、`__pycache__`、smoke/mock/早期过程轨迹归档到 `archive/process_20260719/`
- ✅ 将 Domain 2 mock、误跑 `s713714`、早期固定策略结果归档到 `archive/process_20260720/domain2_superseded/`
- ✅ 摘要投稿前最终语言润色与字数检查：`docs/title_abstract_candidates.md`

---

## B. 最小实验闭环

- ✅ 创建项目骨架
- ✅ 实现 mock LLM client，支持离线自检
- ✅ 实现 DeepSeek API client
- ✅ 实现 multi-agent code-repair pipeline
- ✅ 实现 free / manual / random baselines
- ✅ 实现 prompt-channel / routing-only / full reuse ablations
- ✅ 实现 trajectory logging、asset extraction、asset reuse
- ✅ 实现 stdin/stdout 代码评测和超时隔离
- ✅ 实现 token、耗时、asset routing 等统计
- ✅ 增加 APPS 一键运行脚本 `scripts/run_apps_protocol.ps1`
- ✅ 增加 APPS 聚合脚本 `scripts/aggregate_apps_results.py`
- ✅ 增加 APPS 失败分析脚本 `scripts/analyze_apps_failures.py`

---

## C. APPS 主实验阶段

目标：用“跑得快但有难度”的 APPS repair 小子集验证组织资产复用是否提升跨任务稳健性。

- ✅ 构建 APPS repair 小子集：20 train / 20 test / 15 shifted_test
- ✅ 完成真实 API smoke test
- ✅ 完成正式 APPS protocol：3 seeds（712 / 713 / 714）
- ✅ 完成 2 个 held-out split：`test` 和 `shifted_test`
- ✅ 完成 6 个 setting：free / manual / random / reuse_prompt / reuse_routing / reuse_full
- ✅ 输出第一版结果表：`results/tables/apps_protocol_summary.md`
- ✅ 输出第一版失败分析：`results/analysis/apps_failure_analysis.md`
- ✅ 确认 `shifted_test` 是主要证据 split，`test` 更接近 sanity / saturation split
- ✅ 初步结论：`reuse_prompt` 在 `shifted_test` 上最稳定，`reuse_full` 不稳定
- ✅ Human-Review：初步确认 3 个 rescue case 和 2 个 hurt case 可用于支撑机制分析
- ✅ 将 APPS 主结果写入论文实验草稿：`docs/domain1_apps_experiment_draft.md`
- ✅ 生成第一版论文图表：`scripts/generate_apps_paper_assets.py`
- ✅ 将图表插入 Domain 1 实验草稿，便于 Human-Review
- ✅ 画第一版“组织资产提取与选择性复用”机制图：`results/figures/poa_mechanism_selective_reuse.svg`
- ⬜ 画第一版分工/组织结构机制图

---

## D. 当前关键结果

APPS formal runs：3 seeds × 2 splits × 6 settings。

`shifted_test` 平均成功率：

- ✅ free：0.689
- ✅ manual：0.622
- ✅ random：0.756
- ✅ reuse_prompt：0.822
- ✅ reuse_routing：0.778
- ✅ reuse_full：0.644

核心观察：

- ✅ `reuse_prompt` 相比 `free` 净 rescue +6 个 task-attempt
- ✅ `reuse_routing` 相比 `free` 净 rescue +4 个 task-attempt
- ✅ `reuse_full` 相比 `free` 净 rescue -2，说明 full reuse 可能过约束或干扰 patch handoff
- ✅ shifted split 的主要失败类型是 `empty_or_missing_patch`，prompt reuse 明显减少这类失败

当前 story 校准：

- ✅ 结果总体支持论文主线，但不支持“所有组织资产复用都有效”的强 claim
- ✅ 更稳妥的 claim：组织资产需要被分解和选择性复用；当前最清晰有效的是 prompt-channel asset reuse
- ✅ `reuse_full` 的负结果不是失败点，而是说明 full reuse 可能过约束，反而强化“资产类型消融”和“选择性复用”的必要性
- ✅ 论文叙事应从“POA 全面提升性能”调整为“POA 能提升 shifted task 下的协作稳健性，但收益依赖资产类型和复用方式”

---

## E. Domain 2：博弈论 / Persona 任务

定位：补充一个更有 Multi-Agent 味道的非代码域，验证 persona、策略稳定性和组织资产复用。

- ✅ 设计 game task JSON schema：`data/tasks_game/social_dilemmas.json`
- ✅ 实现 Iterated Prisoner's Dilemma evaluator
- ✅ 实现 Public Goods Game evaluator
- ✅ 支持 persona prompt 配置
- ✅ 记录 cooperation rate / average payoff / social welfare / Nash-deviation rate
- ✅ 跑通 mock no-persona vs persona vs reused strategy assets 对照
- ✅ 输出 Domain 2 mock summary：`results/tables/game_domain_summary.md`
- ✅ 写入 Domain 2 启动说明：`docs/domain2_game_theory_plan.md`
- ✅ 跑第一轮真实 API smoke test：pipeline 正常，但发现 `max_tokens=32` 导致大量空 action
- ✅ 修复 Domain 2 API 配置：`temperature=0.0`、`max_tokens=128`，并新增 `invalid_action_rate`
- ✅ 重跑修复后的真实 API smoke test：`game_domain_api_smoke_fix_20260718`，但 invalid action 仍然偏高
- ✅ 继续修复 Domain 2 动作协议：`max_tokens=512`、压缩 history、非法动作极简 retry
- ✅ 重跑 retry 版真实 API smoke test：`game_domain_api_smoke_retry_20260718`，`invalid_action_rate=0`
- ✅ 增加 Domain 2 聚合脚本：`scripts/aggregate_game_results.py`
- ✅ 跑小规模正式 Domain 2：`test + shifted_test`，3 settings，`invalid_action_rate=0`
- ✅ 聚合正式 Domain 2 结果：`results/tables/game_domain_aggregate.md`
- ✅ 生成 Domain 2 论文图表：`results/figures/game_domain_cooperation.svg`、`results/figures/game_domain_payoff.svg`
- ✅ 生成 Domain 2 论文表格：`results/tables/paper_game_main_results.md`、`results/tables/paper_game_cooperation_deltas.md`
- ✅ 写 Domain 2 实验小节草稿：`docs/domain2_game_experiment_draft.md`
- ✅ Human-Review：初步决定 Domain 2 可放正文，最终篇幅后续按全文空间调整
- ✅ Human-Review 发现风险：早期 `reuse_assets` 使用代码中固定的 strategy prompts，不足以支撑“从轨迹抽取资产后复用”的核心主张
- ✅ 新增 trajectory-derived game asset extractor：`src/assets/game_extractor.py`
- ✅ 新增 game asset 抽取入口：`src/runners/run_extract_game_assets.py`
- ✅ 修改 `run_game_domain.py`：`reuse_assets` 必须读取资产文件，不再使用硬编码 `GAME_ASSETS`
- ✅ 新增 Domain 2 一键闭环脚本：`scripts/run_game_asset_protocol.ps1`
- ✅ 跑通 Domain 2 mock asset protocol：train trajectories -> extract strategy assets -> held-out reuse -> aggregate -> regenerate tables/figures
- ✅ 运行真实 API 版 Domain 2 asset protocol：`game_asset_protocol_api_20260720`，3 seeds（712 / 713 / 714）
- ✅ 排除误跑 `s713714` 并重新聚合正式 3-seed 结果
- ✅ 根据真实 API 版结果，决定摘要中保留 Domain 2，但写成 controlled secondary evidence
- ✅ 优化论文图表风格第一轮：APPS 主结果改为 point-line + error bars，Domain 2 改为小面板 point-line 图
- ✅ 优化论文图表风格第二轮：APPS 主结果改为双 split 雷达图，Domain 2 改为暖色小面板柱状图 / grouped bars
- ✅ 全文整合阶段：将 Domain 1 / Domain 2 小节合并进主论文 draft v0
- ⬜ 篇幅控制：全文写完后决定 Domain 2 主文保留细节还是压缩部分到 appendix

当前建议：

- Domain 2 可以按正文实验二保留，但必须使用新的一键脚本得到的 trajectory-derived asset 结果作为核心证据
- 摘要中 Domain 2 的安全说法：trajectory-derived strategy assets transfer beyond code repair, improving Public Goods cooperation while matching persona prompting in saturated IPD settings
- 当前不建议继续花 API 费用；优先改论文、Related Work、LaTeX 和提交材料
- 当前 mock 结果只用于流程自检，不作为论文证据

正式 Domain 2 结果：

- ✅ held-out runs：3 seeds × 2 splits × 2 games × 3 settings = 36
- ✅ source runs：3 seeds × 2 train games = 6，用于抽取 strategy assets
- ✅ 所有正式 runs 的 `invalid_action_rate=0`
- ✅ Public Goods：`test` 上 reuse_assets 0.986 > persona 0.750；`shifted_test` 上 reuse_assets 0.833 > persona 0.767
- ✅ IPD：大多饱和；`test` 上 reuse_assets 0.979，略低于 persona 1.000；`shifted_test` 三种设置均为 1.000
