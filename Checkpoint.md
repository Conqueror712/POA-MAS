# POA-MAS Checkpoint

更新时间：2026-07-15

---

## A. Idea 确认阶段

- ✅ 阅读原始共享文档 `AAAI-2027.md`
- ✅ 判断 Idea 1 与 Idea 2 是否适合融合
- ✅ 确认主线：以 Idea 1 为核心，Idea 2 作为 framing
- ✅ 新建整理稿 `AAAI-2027-Fix.md`
- ✅ 收窄论文问题：涌现分工能否被沉淀为可复用组织资产
- ✅ 初步列出 novelty 风险与 related work 风险
- ⬜ 人类共同确认最终英文标题
- ⬜ 人类共同确认摘要投稿版本

---

## B. 第一阶段：最小实验闭环

目标：先跑通 `emergence -> trajectory logging -> asset extraction -> reuse`，不追求最终性能。

- ✅ 创建 `POA-MAS/` 项目目录
- ✅ 创建第一阶段代码骨架
- ✅ 创建 toy code-repair 任务集
- ✅ 实现 mock LLM client，支持无 API/GPU 的离线调试
- ✅ 实现多 Agent team 初始化
- ✅ 实现 self-organization controller
- ✅ 实现三类基础模式：free / manual / random
- ✅ 实现代码任务自动评估
- ✅ 实现 trajectory logger
- ✅ 实现基础指标：success rate / specialization index / task overlap rate
- ✅ 实现 role asset / organization asset schema
- ✅ 实现 deterministic asset extractor
- ✅ 实现 asset store
- ✅ 实现 reuse runner
- ✅ 用 mock client 跑通 emergence / extraction / baselines / reuse
- ✅ 接入 DeepSeek-V4-Flash API 配置
- ✅ 保留 mock config 作为离线自检
- ✅ 用真实 DeepSeek API 跑通 smoke-test 任务
- ⬜ 接入本地 7B/8B 模型
- ✅ 扩充合成 code-repair 任务并写入 train/test/shifted split
- ✅ 支持按 split、seed 和唯一运行名执行实验
- ✅ 增加 prompt-only / routing-only / full reuse 消融
- ✅ 记录 token、调用数、墙钟时间和资产路由率
- ✅ 将代码评估改为带超时的隔离子进程

---

## C. 公开基准与当前结果

- ✅ 接入公开 HumanEval 测试主体，保留原始 `check(candidate)` 测试
- ✅ 构建 45 个可验证 HumanEval repair 任务（train/test/shifted_test 各 15）
- ✅ 记录公开来源 URL、SHA-256、原始 task ID 和 mutation 类型
- ✅ 完成 HumanEval 单 seed 的 train -> asset extraction -> held-out 对照
- ✅ 确认资产证据仅来自 train，不与 held-out 来源任务重叠
- ✅ 在 shifted_test 上观察到 prompt-only reuse 13/15，高于 free 8/15
- ⬜ 用至少 3 个 seed 重复 HumanEval 完整协议并报告置信区间
- ⬜ 引入 QuixBugs、BugsInPy 或 SWE-bench 子集作为外部真实性验证
- ⬜ 增加隐藏/扩展测试，降低公开测试与训练数据污染风险

---

## D. 第二阶段：主实验扩展

目标：把 toy pipeline 扩成能写进摘要的初步实验。

- ⬜ 跑 Free MAS baseline
- ⬜ 跑 Manual Roles baseline
- ⬜ 跑 Random Roles baseline
- ⬜ 跑 Role Assets Only 消融
- ⬜ 跑 Organization Assets Only 消融
- ⬜ 跑 Full POA-MAS
- ⬜ 跑 No Validation 消融
- ⬜ 至少 3 个随机种子
- ⬜ 记录 token cost / latency
- ⬜ 输出第一版结果表格
- ⬜ 输出第一版分工指标图
- ⬜ Human-Review：判断实验结果是否支撑摘要 claim
