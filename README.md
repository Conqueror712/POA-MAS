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

### 下一步：正式 Code Repair 数据

需要扩展到至少：

- train：30-50 个任务；
- test：30-50 个同分布任务；
- shifted test：20-30 个轻度分布偏移任务。

候选来源：

- HumanEval / MBPP 风格的小函数任务；
- 自制 bug-injection code repair 数据；
- 少量 SWE-bench Lite 任务作为 realism check。

HumanEval / MBPP 需要真实数据集。后续应增加一键下载/转换脚本，把原始 benchmark 转成当前系统使用的 JSON schema。

### 候选扩展域：博弈论 / Persona

博弈论任务适合研究 Persona 和策略涌现，例如：

- Iterated Prisoner's Dilemma；
- Public Goods Game；
- Ultimatum / Bargaining；
- Stag Hunt / Chicken Game。

建议它作为第二或第三实验域，不要抢占 code repair 的第一主线。

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

