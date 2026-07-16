# POA-MAS

POA-MAS 是一个用于论文实验的多智能体研究原型，全称暂定为：

**Persistent Organizational Assets for Self-Organizing Multi-Agent LLM Systems**

项目核心问题：

> 多 Agent 系统在任务执行过程中涌现出的分工、角色和协作流程，能否被沉淀为可复用的组织资产，并在后续任务中提升效率、稳定性和成功率？

当前仓库是第一阶段最小实验闭环，不是最终论文代码。它的目标是先跑通：

1. 读取代码修复任务；
2. 运行多 Agent 协作；
3. 记录完整轨迹；
4. 自动评估代码修复是否通过测试；
5. 从成功轨迹中抽取 role assets 和 organization assets；
6. 在后续任务中复用这些资产；
7. 对比 free / manual / random / reuse 等基础设置。

---

## 目录结构

```text
POA-MAS_DEV/
  configs/
    experiments.json          # DeepSeek API 配置
    experiments_mock.json     # Mock 离线调试配置
  data/
    tasks_code/
      toy_code_repair.json    # 当前 toy 代码修复任务
  src/
    agents/                   # Agent 定义与 team 构造
    assets/                   # 资产 schema、抽取、验证、存储
    controller/               # 任务路由与自组织控制器
    eval/                     # 代码执行评估与指标
    runners/                  # 可直接运行的实验入口
    utils/                    # 配置、日志、LLM client
  Checkpoint.md               # 人类可读进度表
```

运行后会生成：

```text
trajectories/                 # 轨迹日志与 summary
assets/                       # 抽取出的 role / organization assets
results/                      # 后续表格和图表输出
```

---

## 运行方式一：Mock 离线闭环

Mock 模式不需要 API key，也不需要 GPU。它用于确认代码流程是否正常，不代表真实实验结果。

```powershell
python -m src.runners.run_emergence --config configs/experiments_mock.json --mode free --limit 3
python -m src.runners.run_extract_assets --config configs/experiments_mock.json --run-dir trajectories/latest
python -m src.runners.run_baselines --config configs/experiments_mock.json --limit 3
python -m src.runners.run_reuse --config configs/experiments_mock.json --asset-mode full --limit 3
```

所有 runner 都支持 `--offset`，用于从任务文件中跳过前面的样本；baseline 还支持
`--run-prefix`，emergence 与 reuse 支持 `--run-name`，以避免不同实验覆盖同名轨迹。
使用包含显式划分的数据集时，可通过 `--split train`、`--split test` 或
`--split shifted_test` 选择任务子集；任务划分会记录在每次运行的 summary 中。

### 资产消融

`run_reuse` 支持三种可比较策略：`prompt`（仅注入资产）、`routing`（仅按角色资产路由）和
`full`（两者同时启用）。summary 会记录 `reuse_strategy`、`asset_routing_rate`、LLM 调用和 token
统计，以及墙钟时间。

```powershell
python -m src.runners.run_reuse --config configs/experiments_semantic.json --split test --asset-mode full --reuse-strategy prompt
python -m src.runners.run_reuse --config configs/experiments_semantic.json --split test --asset-mode full --reuse-strategy routing
python -m src.runners.run_reuse --config configs/experiments_semantic.json --split test --asset-mode full --reuse-strategy full
```

`expanded_code_repair.json` 用于端到端稳定性检查，split 间共享修复家族；
`semantic_code_repair.json` 保证修复家族在 split 间不重叠，应优先用于复用比较。
所有 runner 支持 `--seed`，并将实际种子写入 summary；比较随机路由时应至少运行三个种子。

语义数据集的最小协议是：先在 `train` 运行 free 并抽取资产，再在 `test` 与
`shifted_test` 分别运行 free/manual/random 和三种 reuse 策略。只有在任务、模型配置和种子一致时，
这些 summary 才可横向比较。

### 公开基准

`scripts/build_humaneval_repair.py` 从公开的 OpenAI HumanEval 下载记录，保留原始
`check(candidate)` 测试主体，并只保留参考解通过、注入 bug 失败的样本。输出的 metadata 记录下载 URL
与 SHA-256。默认构建 15/15/15 个任务：

```powershell
python scripts/build_humaneval_repair.py
python -m src.runners.run_emergence --config configs/experiments_humaneval_mock.json --split train --limit 3
```

公开测试不等同于隐藏测试，且 HumanEval 可能已存在于模型训练数据中；论文实验应把它作为可复现的
受控基准，并另行报告 QuixBugs、BugsInPy 或 SWE-bench 子集的外部验证。
代码评估在独立子进程中执行，默认超时 5 秒；公开基准可通过 `evaluation_timeout_sec` 收紧该限制。

### APPS Repair

将官方 APPS 数据解压到 `data/public/APPS/` 后，可用其原始 stdin/stdout 用例构建本地 repair 集：

```powershell
python scripts/build_apps_repair.py
python -m src.runners.run_emergence --config configs/experiments_apps_mock.json --split train --limit 3
```

转换器保留仅能被原始用例验证的 Python mutation；默认从 introductory 题目生成 20 train、20 test，
从 interview 题目生成 15 shifted_test。评估在独立进程中运行程序并按规范化 stdout 比较输出。
程序级补丁需要更高的输出预算；`experiments_apps.json` 使用 4096 tokens，避免 reasoning 消耗完预算后返回空程序。

### 终端训练进度

使用训练入口可在终端中逐题看到进度；它不设置总训练超时：

```powershell
python -m src.runners.run_training --config configs/experiments_apps.json --split train --seed 712 --run-name apps_train_live
```

每个完成的任务会输出一行 JSON，包含累计成功数、当前任务和耗时；最终 summary 仍写入 run 目录。

APPS 的完整 held-out 对照可由一个命令串行运行：

```bash
python -m src.runners.run_apps_protocol --config configs/experiments_apps.json --seed 712
```

它按 `free/manual/random/prompt/routing/full` 的顺序依次运行 test 与 shifted_test，并在每题完成时输出进度。

## 测试

```powershell
python -m unittest discover -s tests -v
```

也可以只跑最小 smoke test：

```powershell
python -m src.runners.run_emergence --config configs/experiments_mock.json --mode free --limit 2
```

---

## 运行方式二：DeepSeek API 闭环

DeepSeek API 使用 OpenAI-compatible chat completions 接口。主配置文件是：

```text
configs/experiments.json
```

其中默认模型为：

```text
deepseek-v4-flash
```

运行前先设置环境变量：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

也可以在 `experiments.json` 中设置 `llm.api_key_file`，让它指向本地密钥文件。默认使用
`configs/.deepseek_api_key`；该文件已被 Git 忽略，内容应仅为 API Key。环境变量优先于该文件。
不要将真实密钥直接写入 `api_key_env` 或提交到仓库。

然后运行：

```powershell
python -m src.runners.run_emergence --config configs/experiments.json --mode free --limit 3
python -m src.runners.run_extract_assets --config configs/experiments.json --run-dir trajectories/latest
python -m src.runners.run_baselines --config configs/experiments.json --limit 3
python -m src.runners.run_reuse --config configs/experiments.json --asset-mode full --limit 3
```

建议第一次真实 API 测试只跑 2-3 个任务，确认输出格式、费用和失败样例：

```powershell
python -m src.runners.run_emergence --config configs/experiments.json --mode free --limit 2
```

---

## 当前实验域

### 已实现：Toy Code Repair

当前任务文件：

```text
data/tasks_code/toy_code_repair.json
```

它只用于验证流程。任务太简单，baseline 之间不会有足够差异，不能作为论文结果。

### 当前公开基准：HumanEval Repair

仓库已经包含 HumanEval repair 版本：

```text
data/tasks_code/humaneval_repair.json
```

它保留 HumanEval 原始 `check(candidate)` 测试主体，并记录来源 URL、SHA-256、原始 task ID 和 mutation 类型。当前结论是：HumanEval 对 DeepSeek-V4-Flash 偏简单，容易出现 100% 或接近 100% 的饱和结果。因此它适合作为可复现受控基准，不适合作为唯一主实验数据集。

### 下一步：正式 Code Repair 主实验数据

需要切到跑得快但更有难度的数据集。当前优先级：

候选来源：

1. **DebugBench Python subset**  
   首选主 benchmark。它本身是 debugging/code repair benchmark，任务形态最贴近当前 `localize -> patch -> review` 流程。目标是先取 Python 子集，生成 train/test/shifted_test。

2. **APPS introductory/interview subset**  
   第二选择。APPS 比 HumanEval 更难，测试明确，适合快速制造区分度。它原本是 code generation benchmark，因此需要转换成 code-repair 形式，或者作为代码 realism check。

3. **HumanEval repair**  
   保留为 sanity / controlled benchmark，不承担主要说服力。

4. **SWE-bench Lite / BugsInPy / QuixBugs**  
   作为后续外部真实性验证。它们更接近真实工程，但环境成本更高，不建议先压进第一批主实验。

下一步应增加：

```text
scripts/build_debugbench_repair.py
scripts/build_apps_subset.py
```

把公开数据一键下载/转换成当前系统使用的 JSON schema。

### Domain 2：博弈论 / Persona

博弈论任务适合研究 Persona、策略稳定性和多 Agent 涌现行为。它不替代代码主实验，建议作为第二实验域或 appendix。

候选任务：

- Iterated Prisoner's Dilemma；
- Public Goods Game；
- Ultimatum / Bargaining；
- Stag Hunt / Chicken Game。

核心指标：

- cooperation rate；
- average payoff；
- social welfare；
- equilibrium deviation；
- persona consistency；
- strategy stability；
- reused strategy assets 是否加速收敛或提升合作。

---

## 常用命令

编译检查：

```powershell
python -m compileall src
```

查看最新 summary：

```powershell
Get-Content trajectories/latest/summary.json
```

查看最新事件日志：

```powershell
Get-Content trajectories/latest/events.jsonl
```

---

## 当前状态

请优先查看：

```text
Checkpoint.md
```

它记录了当前论文与实验推进进度。合作者第一次接手时，建议阅读顺序是：

1. `README.md`
2. `Checkpoint.md`
3. `configs/experiments_mock.json`
4. `data/tasks_code/toy_code_repair.json`
5. `src/runners/`

---

## 重要提醒

- Mock 结果只用于验证代码流程，不可写入论文结果。
- 当前 toy 任务太简单，下一步必须扩充正式任务集。
- API 实验应先小规模 smoke test，确认输出和费用后再批量跑。
- 代码修复主实验应尽量使用自动测试评估，减少人工 judge 噪声。

