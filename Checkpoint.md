# POA-MAS Checkpoint

更新时间：2026-07-14

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
- ⬜ 用真实 DeepSeek API 跑通 3-5 个 smoke-test 任务
- ⬜ 接入本地 7B/8B 模型
- ⬜ 扩充 code-repair 任务到 30-50 个（写入正式 train/test/shifted split）
- ⬜ 设计同分布测试集与偏移测试集
- ⬜ Human-Review：检查当前 toy task 是否足以验证流程