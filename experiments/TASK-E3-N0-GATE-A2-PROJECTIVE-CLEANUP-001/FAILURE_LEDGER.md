# FAILURE_LEDGER

| ID | 类型/范围 | 实际发现 | 处理及证据 |
| --- | --- | --- | --- |
| F01 | 旧硬门槛 / r14 | crop(99,144)宽代理2px<3；解剖身份未认证 | 原ID/深度保留，旧FAIL不变；R14_THIN_STRUCTURE_DIAGNOSIS.json、Fig4第一行 |
| F02 | 清理副作用 / r04,r00 | 原生小分量增加；裁后新增5/65个sub3px ridge | 不二次删点或补洞；VALIDITY_TOPOLOGY_COMPARISON.csv、Fig4末行；A2未提升基线 |
| F03 | 输入竞争 / ref03,r04,r00 | 相邻原像素跨11.6–19.4mm深度层，正向配对13.42/11.64/19.56mm仍存在 | 逆NN身份/深度正确；保留层、不平滑；RESAMPLING_FAILURE_DIAGNOSIS.csv、Fig4。诊断开放问题，不新增硬门槛 |
| F04 | 未决 / P47–P55 | 其他视角落于Polyp内部且存在层竞争 | 9点全保留；P48仍决定Y界，P50仍为r00采样极值；PROJECTIVE_CLEANUP_DECISIONS.csv |
| F05 | 审查预算 | 4451个发现标记只审2810，1641未审 | 全保留；CANDIDATE_DISCOVERY_ALL_FLAGS.csv；不扩大阈值搜索 |
| F06 | 可见性资格 | CORE条件性；pilot仍INSUFFICIENT_EVIDENCE；真实BG表面未独立认证 | 轮廓票为代理，不认证物理真错；r14不否定其他源；不做相机优化 |
| F07 | 真实表面保护未能认证 | 高保留率/CORE连通域不等于独有侧面物理完整 | 区分工程保护与物理认证，无GT/Oracle；GATE_A2_FAIL，不建议直接GateB |
| E01 | 工作树初始化 | --no-checkout后sparse-checkout缺新worktree/info，命令退出128 | 只建新工作树info目录后完成；旧工作树未变 |
| E02 | 解释器 | shell python没有pathlib，元数据读取立即失败 | 后续固定复用既有.venv/bin/python；无数据计算/环境修改 |
| E03 | 守卫误拒绝 | 旧规则把GT_ISOLATION_AUDIT.md报告名当GT | 文件读取前拒绝；只对白名单该Markdown的只读访问放行，其余GT和写保护仍生效；common.py |
| E04 | 诊断坐标 | 旧叙述r14(99,143)差1行，最初A2诊断复用了该文字 | 从旧JSON/NPZ身份修正为(99,144)/native(282,215)，仅重做该诊断；config/INITIAL_THIN_DIAGNOSTIC_ISSUE.json |

没有参数搜索、第二轮清理、GPU、神经前向或正式推理失败被隐藏。原始Gate A结果没有覆盖。
