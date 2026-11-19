# 统一输入与来源审计

正式空间是 `/home/liu/ring_first_3d_workspace`。依据 003 的正式工作空间记录、依赖闭包和 247 测试选择；没有使用废弃 Worktree。此前该目录无 Git，本轮建立独立本地源码快照、origin 和任务分支，没有更改任何旧对象库，也没有 push。

- 冻结来源：当前 contour-guided `inputs/SOURCES.json`，SHA 在 TASK_FREEZE.json。
- 实际 5 组、10 视频、105 视角：80 FIT、25 UPDATE_HOLDOUT。每视频 8 FIT；原方向分区、顺序和权重保留。UPDATE_HOLDOUT 在报告中归类 HOLDOUT，没有参与训练、支持图选择或 checkpoint 选择。
- INPUT_MANIFEST.csv 为不可变原始清单；OUTPUT_BINDINGS.csv 为后续相机/HERO结果链接，不重写原清单。
- 105 张 RGB/Mask 文件 SHA 均与来源记录一致；缓存 RGB/labels 像素 SHA 与冻结内容一致；K 完全一致，640×360、OpenCV c2w、毫米、轴向 Z。
- 各组沿用各自冻结的 EXACT013 V/F/F_solid/基底字段。相同初始化函数；组内 B0/B1/B2 起点完全相同，跨组不重新拟合或根据 GT 改尺寸。并非把所有物理组强行替换为同一尺寸的模型。
- 五组 R10 CAD 与正式 Ring-First 5.6mm 主半径、0.6mm 管半径相符；CAD 顶点对解析曲面的最大偏差 6.55e-7mm。原始 GT 只记录身份，所有训练冻结之前不读取其形状。

## Ring-First 来源政策

用户明确允许原正式 RGB yaw 消歧，禁止纯 PnP 替代。原 native.recover 同时计算 Ring-First 与 PnP 候选，混合比较的 105 结果完整保留。RF_ONLY_V1 在 GT 之前公开冻结“先过滤合法候选族，再按同一个 FIT_objective 比较”的政策；数值求解器、RF_CONFIG、RGB 内点和 yaw 搜索不变。每个选中 C 与原候选逐元素相同，并记录原结果 SHA 与候选下标。没有将 PnP 改名为 Ring-First。

归档参考库经原成员 SHA 提取。004 的 G01/G03/G05/G06 参考角色均为历史 FIT，参考 RGB 像素身份与当前 HOLDOUT 无重叠；并不强制参考库只能包含当前 8 帧，这些是固定的历史标定输入。本轮 Body 和 HERO 支持图仅使用本轮 FIT。各视频间没有共享相机或借用另一视频的参考库。

G02 无同视频 RGB 库；其余多数005也无库。G01/005 虽有库，但8个参考身份缺失，且代码来源显示继承旧跨视频变换，未认作认证的本视频 Ring 坐标。故均未准入。G03/004 的1个HOLDOUT Ring误差超过冻结3px，失败仍保留在原分母。

早期归档004图像的“原始视频精确帧号”部分未再次认证。本轮认证的是实际图像/Mask/缓存字节及像素身份，不夸大采集序号准确性。银行/机位仍属于历史RGB标定条件下的数值几何，不是独立相机GT。

## HERO 和主体

正式 API 为一目标+三支持，目标是冻结8个FIT，支持为同一顺序循环偏移2/4/6，推理前写入 HERO_TARGETS_FROZEN.json。没有读取HOLDOUT作为支持图，没有混用005。原生352×640内参与半像素映射复用正式 API；深度不插值，输出轴向Z。Raw XYZ和Mesh以有效Polyp像素身份保存，完整原始深度图同时保留。

归档参考资料中旧的 HERO 观测未进入相机或主体损失；新预测只使用本轮32次新HERO。B1的深度诊断/对照IO不改变训练目标；优化深度项只在B2启用。两臂的先验、36轮预算、几何保护及生长准入完全相同。

实际原视频、照片和ZIP身份见RAW_DATA_INVENTORY.json；外部Python、模型权重和官方源码目录见ENVIRONMENT.json。全部只读，没有重新打包ZIP、安装依赖或训练模型。
