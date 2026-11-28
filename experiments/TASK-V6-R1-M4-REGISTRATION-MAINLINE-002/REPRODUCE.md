# M4 主线入口与下游读取

从包含本任务的独立工作树运行。唯一科学方法是冻结的原 M4；M5 不参与常规路径。输入根及配置位于 `config/PROTOCOL.json`，全量终态与组清单位于 `config/INVENTORY.json`。原上游文件只读。

## 运行与续跑

```bash
# 全量：核验已冻结清单，按组匹配/求解→Clean→评价/图→交付核验
bash experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/run.sh --resume

# 单组；名称取 INVENTORY 的真实 group，包含全部可用视频
bash experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/run.sh --resume --group GP_IIa_14.0mm_closed_R5_single_refY

# 单独阶段；缓存逐项校验，不能只看文件是否存在
bash experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/run.sh --resume --stage clean
bash experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/run.sh --resume --stage review
bash experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/run.sh --resume --stage verify
```

首次新工作树运行不带`--resume`，审计会生成全部清单。局部失败保留阶段错误和原观测，继续其他组；中断未完成目录改名为`.incomplete_时间`保留，再执行原阶段。已完成缓存按输入、代码/配置、T、CAD和分类器身份校验。哈希不一致会停止该阶段，不能把旧缓存改名后接用。任务内限1GiB、磁盘余量5GiB；CPU单线程且低优先级，GPU不可见。不触发上游模型、相机、分割、HERO或原调度器。

`--stage register`只求M4及图像评价；`clean`输出可信面、相机、地标和GROUP接口；`review`固定原面曲面评价及三状态图集。无需运行旧方法矩阵。`diagnose.py`是本次已完成的开发诊断，不在全量入口重复搜索方法。

## 下游只消费 GROUP_INDEX → GROUP

```bash
bash experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/run_python.sh - <<'PY'
from context import T,read
from consume import load_source
index=read(T/'GROUP_INDEX.json')
entry=next(g for g in index['groups'] if g['group']=='GP_IIa_14.0mm_closed_R5_single_refY')
group=read(entry['path'])
source=next(s for s in group['sources'] if s['connected'] and s['clean_status']=='COMPLETE')
data=load_source(entry['path'],source['source_id'])
print(data['V'].shape,data['F'].shape,data['original_face_id'].shape,data['units'])
# data['V'], data['c2w'] 已经是共同坐标；禁止再次施加T。
PY
```

原始Mesh引用始终为LOCAL，应用一次`T_local_to_common`；Clean取原`F[trusted_original_face_id]`。相机NPZ保留全量c2w/K/帧ID、内部points及point_track_ids，c2w和points已经变到COMMON；轨迹ID命名空间为case，不能跨视频按同号合并。跨视频独立DLT地标也导出，但未假称已经融合。单视频组有合法本地锚点，不声称恢复了跨视频关系。无输出/未连接来源明确标状态。

## 依赖与归档

科学代码由`code/pinned.py`通过Git SHA解析：002 `efa0adfb`、虚拟001代码 `537c2070`、可信Clean `2d34cc86`；只恢复代码和必要小配置，不读取旧H004成品。R1 `clean_after.one`与共享源码保留在本分支基础 `f7a3ff85`。浅克隆若缺提交对象，先用`git fetch origin <完整提交SHA>`取回上述版本；解析器会核对内容，不能换成当前最新版本。不再依赖旧临时worktree路径；本机Python环境仍使用原只读venv及extra_packages，迁移可按`run_python.sh`改解释器/包路径。

输出归档以任务目录为根保留`runs/FULL_001/groups/`及统一入口，原始视频、HERO大文件、完整网格和环境不入归档。`evidence/ARCHIVE_MANIFEST.json`列归档SHA与成员。`evidence/RETAIN_DEPENDENCIES.json`列不可清理的原始输入和代码身份。

解压到另一个路径后，GROUP/回执中的任务内绝对路径需按旧任务根→新任务根统一映射；上游路径按原身份解析并校验SHA，不能更换内容。当前入口在本工作空间可直接运行；并非无外部原资产的独立安装包。

图集：`visuals/index.html`。结果表：`evidence/GROUP_STATUS.csv`、`VIDEO_STATUS.csv`、`EDGE_RESULTS.csv`、`SURFACE_RESULTS.csv`、`SOURCE_STATUS.csv`。失效和null均保留；条件统计不是完整均值，也不是GT精度。
