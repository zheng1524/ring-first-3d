# 阶段A 清理回执

按本轮PM授权执行；没有按上一轮审计“无条件0字节”停止工作。

## 实际执行

2026-11-26T01:57:40.955486+08:00至2026-11-26T01:57:44.221828+08:00，同挂载点 `/dev/nvme0n1p3` → `/`。先核验精简归档全部5,759成员，再逐文件复核SHA/size/inode/单链接及保护列表后清理5,831个专属衍生文件，无执行错误。

| 退役运行路径 | 移除文件分配字节 |
|---|---:|
| `/home/liu/ring_first_3d_workspace/runs/m2e_historical_method_integration` | 928092160 |
| `/home/liu/ring_first_3d_workspace/runs/m2f1_w0_admission_restoration` | 1424338944 |
| `/home/liu/ring_first_3d_workspace/runs/m2f1_strict_restoration` | 467648512 |
| `/home/liu/ring_first_3d_workspace/runs/m2f2_root_cause_corrective` | 111001600 |
| `/home/liu/ring_first_3d_workspace/runs/m2f3_admission_convergence` | 404037632 |
| `/home/liu/ring_first_3d_workspace/runs/m2f5_unified` | 291352576 |
| `/home/liu/ring_first_3d_workspace/runs/m2f8_v6_general` | 42283008 |
| `/home/liu/ring_first_3d_workspace/runs/m2f9_v6_general` | 54927360 |

仅移除清单中FACE_EVIDENCE、HERO_native、RAW_NATIVE_MESH、NATIVE_RGB_LABELS和PLY输出。各物理组代表目录共93个保留；所有相机、轨迹、地标、Ring观测、RAW、CAD、源码、状态/日志/指标及已有PNG留在原位。原路径的完整输出现不再齐备，这是退役精简，不承诺一键恢复全部历史大产物。

## 空间实测

- 删除前普通用户可用：6,359,973,888 B（5.9232 GiB）。
- 删除后普通用户可用：10,083,643,392 B（9.3911 GiB）。
- 同盘df净增加：**3,723,669,504 B（3.4679 GiB）**。
- 清单文件块合计：3,723,681,792 B；与df差额含目录/元数据及系统同期写入。归档在测量前完成，另占9,229,298 B；不能把小型同盘归档称外部备份。

## 精简归档及验证

`archive/RETIRED_MINIMAL_EVIDENCE.tar.gz`，SHA256 `1b6f4782b30dcafa1b23cf3a639512a9c77fd3e8be072f8fa85ef5dcd9e44af6`。包含实际源码快照、现存运行配置/状态/输入身份、结论/指标/日志及少量图。逐成员源路径、SHA与大小见 `evidence/ARCHIVE_MANIFEST.json`；提取只需对具体member流式读取核验，不需恢复整套环境。归档不包含被移除的大产物；它保留方法和正负结果解释，不是全量数据备份。

`evidence/CLEANUP_PLAN.json`及`CLEANUP_EXECUTED.json`保存每个删除路径、原SHA、inode、大小、所属运行与理由；`code/cleanup_guard.py`保存执行器。5项夹具测试通过：有效文件/越界/受保护/哈希漂移/软链接。

## 共享依赖与暂不处置

V6仍读取 `runs/m2f5_unified/cad/R5.npz`和`R10.npz`；CAD、M2F5准备代码及V5/V6旧源码保留。Open3D及DINO/HERO等公共权重和环境未动；没有Git GC或历史删除。M2F10正式五组基准、M2F11部分运行、M2F6对照、004参考库/019/021和主体/柄部闭包保留。

TSDF、NeuralFusion、MonoSDF、PMGR、Hull、MapAnything与旧SU源码及结论已纳入精简归档（模块对应见上轮CSV）。其旧混合目录/环境没有整树删除：旧P只读边界、共享库和主体资产使目录级归属不清；此次只清理W内已核实专属衍生输出。MonoSDF标“停止推进/训练未完成”，不改写为充分训练后证伪。UNIFIED-002及旧soft-zbuf的现存源码与证据保留，不盲删独有版本。

轻量保留入口检查：9655个保留依赖文件均存在；114个非分支模块源码SHA与审计一致；93个代表目录存在。未以此宣称重新运行完整科研流水线。原tracked修改不变；授权退休run的未跟踪输出消失单列记录。
