# TASK-RESEARCH-POLICY-BOOTSTRAP-001

2026-11-16。本轮从 release/research-harness-001 的 e24fbd0069d31636424af188b863169633ca47ae 增量增加 Task Contract、Policy Runner、Failure Memory、产物检查和恢复机制。现有 DXY/选视角/Renderer、Preflight、Contracts、Smoke 原代码均未修改，也未执行新主体重建。35 项测试通过，18 次真实公开 CLI 检查通过；实际终止一次本任务 Smoke Runner 后，保留中断记录并复用已通过阶段恢复，最终工程验收 PASS。本地结果卡、manifest、报告、指标、失败台账和 HTML 可视化均已存在且通过 SHA/路径校验。导入 9 条失败记忆，均为 candidate，不自动批准永久规则或改变科学路线。

## 使用

交接仅需：**“按 TASK.yaml 检查、执行已授权阶段、使用同一 run-dir 恢复；失败停止，accept 后返回结果卡和可视化路径。”**

CLI 为 [tools/research/policy.py](../../tools/research/policy.py)，支持 init/check/run/status/accept/failures。模板 [templates/TASK.yaml](../../templates/TASK.yaml)；本次冻结契约 [TASK.yaml](TASK.yaml)；简短说明 [RESEARCH_POLICY_BOOTSTRAP.md](../../docs/RESEARCH_POLICY_BOOTSTRAP.md)。本机复现命令见 [REPRODUCE.md](REPRODUCE.md)。

## 实现与边界

| 能力 | 已实现的执行断言 |
| --- | --- |
| Task Contract | 严格 YAML 字段/类型、拒绝重复 key/对象/别名；目标、模块、冻结变量、来源 SHA、角色划分、授权、验收、预算、停止条件；不接受任意命令 |
| Policy Runner | 组合原 Preflight/11 Contracts/真实 Smoke；按模块加载原 SHA 锁定源码；单位 mm、原生像素、OpenCV c2w、axial Z；授权前缀和所有前置阶段必须 PASS，无绕过参数 |
| 数据隔离 | 相机角色必须匹配冻结 CASE.json，FIT/HOLDOUT 不交叉；GT 列表必须为空；可信 worker 的 Python I/O 门禁拒绝 GT 路径和 attempt 外写入 |
| Failure Memory | 代码、环境、身份错误与科学负结果/未完成评价分开；原因状态 confirmed 或 observed_only；本地证据 SHA 与固定历史链接；未经明确 review 不得永久晋升 |
| Artifact Checker | 必需文件/实际路径/SHA/大小、HTML 全部本地引用、失败证据、阶段原始输出完整性；缺可视化时验收拒绝，不自动补造通过 |
| Progress/Resume | 原子 JSON、独立 attempt、完成目录 rename、不可变 snapshot、原子 current 指针；flock 排他；成功阶段验证后跳过；保留失败/半写文件并记 INTERRUPTED |
| 预算/停止 | 总计算秒数、单阶段 timeout、重试次数、输出字节；超时终止本任务进程组；Linux parent-death 防止本任务孤儿 worker；中断保守扣预留超时 |

现有 Preflight/Smoke 是完整集成包，执行须声明十个模块，避免在单模块声明下隐式运行额外算法；模块子集可以 check 其源码契约。首版没有新科学阶段 handler，不能从 TASK.yaml 直接执行主体优化/训练/GT 评价。Python audit guard 约束的是固定可信 API，不是恶意原生代码的 OS 沙箱。真实数据和运行环境仍为已登记 LOCAL_ONLY 依赖。

## 实测结果

| 检查 | 实际结果 |
| --- | --- |
| 新策略/恢复/错误拒绝回归 | 24/24 单元/边界测试通过；昂贵 handler 的状态机单元测试使用明确标注的 test double |
| 原数学/身份契约 | 11/11 通过，原文件未改 |
| 公开 CLI 集成 | 18 次真实调用符合预期，无 handler mock；既有实际 CUDA/DXY API |
| 正常阶段执行及验收 | Preflight、Contracts、Smoke、Artifacts 全 PASS，accept=True |
| 错误单位 / SHA / GT / FIT-HOLDOUT 重叠 | 分别拒绝 COORDINATES / SOURCE_SHA / GT_LEAK / DATA_ISOLATION |
| 越权 / 缺前置 / 失败任务验收 | UNAUTHORIZED_STAGE / PREDECESSOR_FAILED / ACCEPTANCE_GATE |
| 缺可视化 / 冻结参数漂移 | ARTIFACT_MISSING / FREEZE_DRIFT；拒绝验收没有重建/覆盖旧快照 |
| 实际预算超时 | BUDGET_TIMEOUT，本任务 worker 已终止 |
| 实际杀进程恢复 | 自建 Smoke Runner 被 SIGKILL；worker 无继续运行；前两次 PASS attempt 哈希未变；中断作为 INTERRUPTED 保留；恢复后 accept PASS |
| 永久规则 / 并发 / 半写结果 / outside write | 未审查永久规则、并发 writer、半写 PASS、GT/outside 写入均由回归验证拒绝 |

原完整 Smoke 包含一个冻结 G01 的正式 DXY、015/016/MAX 列表与 T13 四视角子集、一个公制 Renderer 视角、Contour/Guard 兼容性。不是全组测量验收。233 个真实输入被绑定核验，环境包括 Python 3.12.13、Torch 2.7.1+cu128、PyTorch3D 0.7.9、RTX 3060 Laptop GPU。完整实际输出、耗时、容差和中断证据见 [CLI_INTEGRATION_RESULTS.json](CLI_INTEGRATION_RESULTS.json)，35 项测试日志见 [REGRESSION_TEST_LOG.txt](REGRESSION_TEST_LOG.txt)，冻结字节哈希与版本见 [TEST_RESULTS.json](TEST_RESULTS.json)。

初期门禁将 /dev/null、NumPy 的 lscpu 查询和 dir_fd 临时清理误拦截，已按真实原因修复并增加回归；4 次原始开发失败的结果/traceback 保存在 [development_failures](development_failures)，全部原 run 仍留本地。该事实作为 FM-POLICY-001 候选记忆，没有删除失败或改科学算法来通过门禁。

## 本地交付

项目：`/home/liu/ring_first_3d_policy_bootstrap`

正常结果目录：`experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/runs/verified-001`。

可视化绝对路径：

`/home/liu/ring_first_3d_policy_bootstrap/experiments/TASK-RESEARCH-POLICY-BOOTSTRAP-001/runs/verified-001/visualization/index.html`

RESULT_CARD.md、RUN_MANIFEST.json、TECHNICAL_REPORT.md、metrics.json、failures.json 位于该正常结果目录，当前指针指向完整不可变快照。实际恢复试验位于同级 `resume-001`，其失败台账保留 INTERRUPTED。入口结果卡和 HTML 展示本次真实阶段状态/耗时；嵌入图明确标记为先前登记的真实回归图，不冒充新三维成果。

运行目录保留 LOCAL_ONLY，Git 只提交代码、模板、失败证据摘要与测试报告。SOURCE_FREEZE 为 a15f443af506f3f4d50353cc1cfbcb44dfd8388c7af70a94a7faae82e68a0677；执行字节与最终提交一致性以 TEST_RESULTS 中逐文件 SHA 为准，Git 提交不会改已冻结源码。

## 科研固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 新科学测量 0；既有 G01 工程回归样本 1 |
| 本算法独立成功 | 新科学预测 0；正常及恢复后的工程四阶段均通过 |
| 本算法失败 | 新科学测量 NaN 不适用；开发与注入失败逐次保留 |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | 无新增测量失败组；工程原因、负向拒绝和中断见 Failure Registry/CLI 结果/原始失败记录 |
| 最终统计样本 | 工程回归，非科学独立覆盖；MAE、中位绝对相对误差、p95、最大误差、共同成功组配对比较均 N/A |
| 是否使用 GT 选择算法 | 否；GT 未读，参数/来源/执行字节/授权冻结；无历史融合对照参与生成预测 |

工程验收不改变既有科学 CONDITIONAL/MIXED 状态。后续科研任务仍需明确批准相应科学 handler 和阶段；本轮到此交付，不进入主体重建实验。
