# 历史004恢复记录

## 已核实血统

首批G01/004相机并非`CAMERA_INITIAL.json`，而是`ring_first_v5_real_validation/predictions/C_F980_0.npz`：V3多源双向LK轨迹→V5 reference8 E/PnP增量SfM→共同视觉BA→真实Ring单侧可见区域约束求全局公制Sim3→C臂100步联合BA。Ring给候选毫米尺度，轴内yaw由reference8规范固定，不是跨视频配准。

传递链：V5 C_F980_0→surface_pilot_v1 real_camera_points_0→surface_pilot_v2 real_camera_0→ring_vh_v1 real_camera_0→surface_fusion_v1 real_camera_0→HERO/013冻结输入→014扩展相机→018/019相机池→019 SIFT地标→020/021成品库→RF5DoF/RGB yaw/normal选择。014扩展也用旧相机三角化背景点再PnP；它不是无锚点RAW初始化。

019用SIFT6000/contrast.01，双向ratio.72，MAGSAC1.5px及既有相机Sampson<4px，合并不重复视图轨迹，最少3视图，最长基线三角化，soft_l1/f_scale1.5/max30点优化，全部正深度、max重投影<2px、最大视差>.5°、范数<300mm。继承相机/选优分母不能认证独立精度。

## 组合表（先于恢复代码）

| 阶段 | 既有实现 | 接口适配/边界 |
|---|---|---|
| RAW解码/INIT | continuous16/scripts/decode_segment.py、DXY INITSegmentation | 同JPEG95/native分割；新run路径；实际帧身份需顺序解码核验 |
| Ring观测 | V4/scripts/adapter.py::adapt、V5/scripts/prepare.py | native观测→640×360 half-pixel；仅物理R5/R10参数适配 |
| RGB轨迹 | V3/scripts/track_scene.py::main | 新RAW、新Mask、新目录；原双向LK及holdout排重 |
| 初始相机 | V5/scripts/visual_initialize.py、ring_candidates.py、run_real.py | 冻结F980/repeat0/C（旧正式首例），同算法阈值；其余重复/焦距为历史敏感性，非本轮选优池 |
| 地标 | 019/features019.py::landmarks | 新相机、同视频RAW；最小IO适配，记录每条轨迹及拒绝原因 |
| 后续相机 | native/rgb.py::pnp、camera.py::recover | 仅本轮地标；禁止历史fallback，Ring物理半径适配 |
| 评价 | V3 held-track、V5 geometry/ring_eval、原A→B | 独立性单独审查；无绝对poseGT |
| HERO | 原官方native HERO | 推理前冻结少量target/support预算；未合法则不推理 |

## 统一协议与待核查

先完成Ip12/004阶段检查。先进行H004_DIAGNOSTIC重放与已知相机下的019重建，全部标历史依赖；然后H004_RAW_BASELINE独立计算。普通路径修复与物理R5/R10参数适配单列，不把算法改动回写历史原版。

V5初始RAW/原生观测生成链仍在验证，尤其历史frame_index与真实解码图像的对应、V4 native观测与V5输入字节闭合。严格共同留出跨V6尚未认证。遇到缺口不加载历史成品补齐。

## 真实重放结果（2026-11-26）

- native camera_demo：相机矩阵max绝对差0、FIT目标差0、candidate_source完全一致；历史参考库条件重放成功，非RAW成果。
- 019：对8个原FIT相机/图像重新执行features019.landmarks，得到153点；与原CROSS_004的X最大差0、描述子逐元素相等。未按数量筛点，原算法自然产生153。完整来源/相机/轨迹/视差/正深度/误差/拒绝原因记录于本次DIAGNOSTIC/rebuild019/REBUILD_AUDIT.json。
- 原019 cache路径缺失，改用retained_sources中018同名cache；核验T/K以及提供的RGB/Mask数组哈希，日志保留缺失路径；未改旧断链。
- V4 adapter在原native ref08图像/Mask上重算，13个输出数组与V5 native_008逐元素完全一致。这闭合native观测生成核心，不能据此宣称其他输入未经验证也一致。
- 正式10视频RAW完整SHA均与M2F10的16份RUN_STATE对应一致；运行代码提交为a38d4c822daf9a9b3cd88e1cd0edebdc70b9bfad，报告提交为2cd9822e...，两者不混淆。

## RAW冻结协议

统一16帧等间隔内区，沿历史82..1192/1265比例适配视频长度；不是V6选帧或组名分支。F980、原repeat0/C是历史正式预设首例；视觉初始化原3次均记录，但只用预先冻结的0，不择优；本轮不复刻3K×3初值完整资格认证，因此不宣称通过其完整可靠性门槛。R5只替换真实torus主半径3.1/外半径3.7mm，管半径.6不变；所有阈值统一。RAW解算有读写隔离：禁止历史预测、Tracks、地标库进入；源码/模型和RAW允许清单逐次记录。

## Ip12/004 RAW阶段检查

16张native JPEG/INIT均从锁定RAW重算。seek标称帧与真实顺序解码有偏差，逐JPEG完整SHA匹配后绑定真实帧（例674→676），不是复用V6帧图。V3轨迹、V5公制相机、019库与native恢复全部写入独立run。固定F980/repeat0产生16个公制数值种子、2150个拟合点；整轨迹留出MAE 2.689588 px，高于原2px门槛，不能声称初始化精度PASS。019自然产生322点（不强凑153），原生RF/PnP产生16数值相机，其中15通过原MAX自身资格门槛、15合法Target，每个3支持。

本轮组装使用16帧新相机池建库，未重演历史014选帧扩展及后期跨视频Ceres共同BA。其历史内核被忠实复用，采样和独立视频组合是明确的复现协议适配，不能称整个旧MAX产品流程逐比特重放。005也独立重走该入口。

原native FEATURE_HELD为landmark ID mod5，只排除PnP拟合，未排除上游建库/初始化；保留其自身准入但标为诊断。V3整轨迹留出在seed初始化/BA前固定，使用两个端点三角化、其余观测测试；该独立性仅适用于seed阶段，无法认证后续SIFT与LK身份不交叉。跨V6共同独立RGB测试为NOT_EVALUABLE，不拿不同选帧均值证明因果。

审查修复：补全120份实际源码闭包，批次每阶段开始验证；分开seed已注册建库池与全16帧query池；补记非有限三角化剔除。首轮support接口缺hashlib绑定的失败日志保留，未作算法优化。首轮typed观测临时适配已换回原MAX observe实现后复跑。R5只改变真实Ring内径/主半径。Python audit隔离覆盖Python文件打开；OpenCV原生读操作另由固定RAW配置和新run路径绑定，不能把audit日志声称为OS级完整沙箱。

## 身份核验工程修复R2

IIa14/004的RAW 758与760帧无损像素不同，但JPEG95编码完全相同，导致旧JPEG-only校验拒绝。按原seek调用重新解码、核对生成JPEG与分割输入逐字节一致，再用无损BGR完整SHA扫描顺序RAW，唯一确认该图像来自760。其余已完成4视频的16帧无损绑定与先前结果一致，未改变图像、分割、相机参数或求解。R2只提升身份检查，不是算法优化；失败日志保留。

补充源码锁R2涵盖176文件，包括早期torus_contours、ring_pose_contact求解器及DXY源码。R1的120文件锁保留；早期pilot只有阶段源码快照，补充锁不能倒称为运行前已锁齐。全部既有科学内核仍只读未改。

R3进一步处理RAW真实重复帧：Ip20/005中同像素出现在578/580/582/584/586/588，原seek呈现时间戳4946.766667ms唯一对应582；Ip8.8/004的655/657同像素，时间戳5657.622222ms唯一对应655。统一使用无损BGR SHA＋解码PTS＋JPEG校验，保留相同像素的全部帧索引。所有先前成功视频用R3重新核验，实际帧号不变。该步骤只修复输入身份，不生成新相机算法或按组放宽阈值。

001参考库核验：`TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/audit/reference_banks`的G01_004点坐标与描述子均与原019 CROSS_004逐元素一致；其余库只记录身份与OBSERVATIONS血统，未用于本轮RAW。001 pipeline.audit本身将canonical/FIT血统未认证标FAIL；RF_ONLY_V1是从已有候选选择originalRF5DoF来源，不是最早公制相机生成器。详见DIAGNOSTIC_001_BANK_BINDING.json。
