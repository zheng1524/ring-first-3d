"""Publish measured maintenance outcomes and the single mainline entry."""
import json,csv,os,hashlib,subprocess,shutil,gzip,collections,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1];M=R/'mainline'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def text(p,s):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n')
mods={'ring-first':'RING_FIRST','hero':'HERO','body-initialization':'BODY_INITIALIZATION','body-update':'BODY_UPDATE','stalk-growth-g01':'STALK_GROWTH_G01','stalk-growth-g03':'STALK_GROWTH_G03','a-to-b':'A_TO_B','depth-supervised-pytorch':'DEPTH_SUPERVISED_PYTORCH'}
res={k:read(M/'validation/replays/003'/k/'RESULT.json')for k in mods};assert all(v['status']=='PASS'for v in res.values())
freeze=M/'manifests/REPLAY_INPUT_FREEZE.json';assert all(v['replay_freeze_sha256']==sha(freeze)for v in res.values())
for x in read(freeze)['source_files']:assert sha(R/x['path'])==x['sha256']
for k,n in mods.items():save(T/'REPRODUCIBILITY_TESTS'/(n+'.json'),res[k])
reg=read(M/'validation/regression/RESULT.json');assert reg['status']=='PASS'and reg['tests']==247 and reg['skipped']==0
harness={k:read(M/'validation/harness'/(k+'.json'))for k in ['preflight','validate_contracts','audit_reuse','smoke']};assert all(v['status']=='PASS'for v in harness.values())
cleanup=read(T/'CLEANUP_RECEIPTS.json');plan=read(T/'PHASE1_DELETE_MANIFEST.json');initial=read(T/'READ_ONLY_SCAN_SUMMARY.json');copies=read(T/'COPY_VERIFICATION.json');assert copies['all_copy_hashes_verified']
oldroutes=read(M/'references/HISTORICAL_RETENTION.json');sourceprov=read(M/'manifests/SOURCE_PROVENANCE.json')

mapping=[]
for mod,name in mods.items():
    mapping.append(dict(id=name,classification='REUSABLE_REFERENCE'if mod in ['hero','a-to-b','depth-supervised-pytorch']else'ACTIVE_MAINLINE',entry='mainline/scripts/python.sh -m ring_first_3d.mainline.cli '+mod,canonical_implementation='src/ring_first_3d/mainline/replays.py::'+{'stalk-growth-g01':'growth','stalk-growth-g03':'growth'}.get(mod,mod.replace('-','_')),test=str((T/'REPRODUCIBILITY_TESTS'/(name+'.json')).relative_to(R)),status='PASS',source_execution_guard='Forbids exec from every former experiment workspace',scientific_certification=False))
mapping +=[dict(id='E1_E2_NINE_PARAMETER',classification='REUSABLE_REFERENCE',implementation='src/ring_first_3d/models / src/ring_first_3d/initialization plus frozen_registry T04–T09',status='MATH_AND_SOURCE_RETAINED; not substituted for EXACT013'),dict(id='DXY_PIXEL_API',classification='REUSABLE_REFERENCE',implementation='src/ring_first_3d/adapters/dxy.py',source='/home/liu/new-polyp-dxy',copied=False,readonly=True),dict(id='P0_RENDERER',classification='REUSABLE_REFERENCE',implementation='src/ring_first_3d/mainline/frozen_registry/visualization/real_p0_renderer.py',status='Exact source and its visualization interfaces retained; A-to-B has its own tested canonical entry'),dict(id='T28_OLD_DEPTH_BLOCK',classification='REUSABLE_REFERENCE',implementation='src/ring_first_3d/mainline/lineage/experiments/TASK-E4-PYTORCH3D-014/code/components.py',observation_model='OLD_DEPTH; separate from native018'),dict(id='T30_NATIVE_DEPTH_BLOCK',classification='REUSABLE_REFERENCE',implementation='src/ring_first_3d/mainline/lineage/experiments/TASK-E4-HERO-BODY-ADAPT-018/code/hero_objective018.py',observation_model='Native pixel first-hit barycentric axial Z; explicit misses'),dict(id='CROSS_VIDEO_BA',classification='REUSABLE_REFERENCE',implementation='src/ring_first_3d/mainline/lineage/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code',status='Source/report evidence retained; not newly optimized')]
assetmap=dict(task='TASK-MAINLINE-ASSET-CONSOLIDATION-001',state='ACTIVE_RESEARCH_MAINLINE',certified_scientific_baseline=False,project_root=str(R),modules=mapping,primary_initialization='EXACT_013_INPUT_MESH_V_F_SOLID_CAP',source_provenance='mainline/manifests/SOURCE_PROVENANCE.json',external_inputs='mainline/manifests/EXTERNAL_INPUTS.json',history='mainline/references/HISTORICAL_RETENTION.json',results='mainline/results',mainline_pipeline='mainline/PIPELINE.md')
save(M/'manifests/MAINLINE_ASSET_MAP.json',assetmap);save(T/'MAINLINE_ASSET_MAP.json',assetmap)
env=harness['preflight']['environment'];native=read(M/'references/ring_hero/VERSION_LOCK.json')
dependency=dict(python=env['executable'],environment=env,compiled_runtime_manifest='mainline/manifests/RUNTIME_FILES.json',runtime_LOCAL_ONLY=True,official_HERO=native['official_mvsanywhere'],checkpoint=native['checkpoint'],DINO=native.get('dinov2'),external_inputs='mainline/manifests/EXTERNAL_INPUTS.json',fixed_source_lock='src/ring_first_3d/source_lock.json',replay_input_freeze_sha256=sha(freeze),old_experiment_code_execution=False,raw_data_kept_in_original_locations=True,cross_machine_status='NOT_CERTIFIED: controlled data paths, CUDA/Python ABI, compiled runtime and official weights must be provisioned and hash-bound')
save(M/'manifests/DEPENDENCY_LOCK.json',dependency);save(T/'MAINLINE_DEPENDENCIES.json',dependency)
status=dict(engineering='PASS',modules_passed=8,modules_total=8,regression=reg,preflight='PASS',contracts='PASS',reuse_audit='PASS',smoke='PASS',scientific_state='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False,cross_machine='NOT_CERTIFIED',end_to_end='CHECKPOINT_CONTINUATION_REPLAY: fixed camera/HERO real sample, exact013 initializer, saved graph state, saved spline parameters, fresh Boolean/projection gates. No new joint training or HERO-to-Body feedback was executed.',source_freeze_sha256=sha(freeze))
save(M/'manifests/REPRODUCIBILITY_STATUS.json',status)
save(T/'CLEANUP_CANDIDATES.json',dict(authorized_operations=plan['operations'],protected_archives=read(T/'ARCHIVE_CONTENT_VERIFICATION.json'),unknown_or_unique_assets='KEEP; no filename-only classification or forced deletion'))
commands=read(T/'INITIAL_COMMANDS.json');initial_by_root=initial['workspace_stats']
text(T/'INITIAL_STORAGE_REPORT.md',f'''# 初始存储盘点

来源分支与远端均核验为bac3fc89ef95db522b63cf6bb98e6914b9382864。初始df显示197G文件系统已用187G、普通用户可用0。只读扫描在首次删除之前完成，输出先写/dev/shm。

逐文件盘点 {initial['files']} 个资产，逻辑字节 {initial['logical_bytes']:,}；该数字包含重复副本，不能当物理占用。范围为所有ring_first_3d*目录、独立ring-first-hero-core及受保护宿主的科研资产；.git对象另计，虚拟环境/node_modules另作外部依赖，未删除。

大文件阈值计数：{json.dumps(initial['threshold_counts'],ensure_ascii=False)}。完整SHA、Git跟踪状态、初始保留决策和静态引用在ASSET_INVENTORY.csv/json及DEPENDENCY_REFERENCE_GRAPH.json。初始KEEP是未审查前的默认保护，最终决策以PHASE1_DELETE_MANIFEST/CLEANUP_CANDIDATES为准。

df、du、最大200项、Git对象/分支/worktree原始输出见INITIAL_COMMANDS.json。文件系统保留块使初始f_bfree仍有{cleanup['before']['free_bytes']:,}字节而f_bavail为0，报告分别记录。

|工作区|文件数|逻辑字节|
|---|---:|---:|
'''+ '\n'.join(f'|{x["root"]}|{x["files"]}|{x["logical_bytes"]}|'for x in initial_by_root))
by_action=collections.Counter(x['status']for x in cleanup['operations']);route_bytes=collections.Counter()
for x in cleanup['operations']:
    task=next((p for p in Path(x['path']).parts if p.startswith('TASK-')),'CACHE_OR_UNASSIGNED');route_bytes[task]+=x['released_payload_allocated_bytes']
text(T/'PHASE1_CLEANUP_REPORT.md',f'''# 第一阶段实际清理

实际文件系统空闲增加 **{cleanup['measured_free_byte_change']:,}字节（{cleanup['measured_free_byte_change']/2**30:.6f}GiB）**；操作级释放的原payload已分配块合计{cleanup['payload_allocated_bytes_released']:,}字节。两者差异包含元数据及后台文件系统变化，不用逻辑文件大小冒充实际空间。

操作状态：{dict(by_action)}。可再生成的缓存逐文件删除；SHA完全相同的静态派生产物通过原子硬链接去重，规范payload只保留一个inode，每个旧路径及其内容仍有效。不是把所有重复路径删除后留下断链。

原始观测、官方权重、唯一预测、Growth Recovery完整目录及STEP024候选不删除。两份约0.9GB归档因各有124个成员无独立副本（另有内容差异）保留，逐成员哈希证据见ARCHIVE_CONTENT_VERIFICATION.json。

TSDF、NeuralFusion、MonoSDF等历史目录仅消除已证实重复payload；未删除未知唯一checkpoint或负证据。MonoSDF保持未充分训练身份。本次没有改写Git历史、删除远端分支或声称缩小GitHub历史存储。

|来源任务|释放payload分配字节（非逻辑估计）|
|---|---:|
'''+ '\n'.join(f'|{k}|{v}|'for k,v in route_bytes.most_common(40)))

table=['|模块|状态|与冻结结果比较|','|---|---|---|']
details={
'ring-first':f'相机矩阵max abs={res["ring-first"]["c2w_max_abs"]:.3g}；分支身份相同',
'hero':'新官方原生推理；深度逐bit一致，Raw FaceID/PixelID/顶点一致',
'body-initialization':'G01/G03原始013容器SHA相同，V/F/F_solid/cap/boundary逐元素一致',
'body-update':'保存的32节点变换经原Graph真实生成Mesh；最大误差'+str(max(x['max_vertex_error_mm']for x in res['body-update']['cases']))+'mm',
'stalk-growth-g01':'新Boolean并集顶点误差0、面索引相同、投影变化误差0；自动门禁仍通过',
'stalk-growth-g03':'新Boolean并集及投影同历史；PER_VIEW_PROTECTION仍拒绝，正式柄长NaN',
'a-to-b':'RGBA、轴向深度、FaceID、重心、CAD深度和有效域逐bit一致',
'depth-supervised-pytorch':f'实际T30加权loss差{res["depth-supervised-pytorch"]["loss_abs_error"]:.3g}；梯度相对误差{res["depth-supervised-pytorch"]["gradient_relative_error"]:.12g}' }
for k in mods:table.append(f'|{k}|PASS|{details[k]}|')
equiv='\n'.join(table)
text(T/'RESULT_EQUIVALENCE_REPORT.md','# 结果一致性\n\n'+equiv+'''\n
全部容差在重放前冻结，见mainline/configs/REPLAY_TOLERANCES.json。前两次工程接线失败和源码/配置快照保存在REPLAY_PROTOCOL_REVISIONS；没有放宽容差。共享ARM.json的G03视图不能替代G01历史逐病例记录；重序列化INITIAL缓存与原始013 ZIP分别保存。

本轮是工程重放，Graph使用实际保存的节点参数、Sweep使用保存参数；没有重跑36轮/80轮训练，也没有根据HERO或GT新增Body更新。旧实验源码执行被audit guard拒绝，官方外部代码及原始数据通过清单管理。
''')

failures=[dict(id='MC-DISK',category='environment_error',symptom='Initial ordinary-user disk space0',confirmed_cause='Measured statvfs/df',repair='Hash-verified payload dedup and regenerable-cache deletion',evidence='PHASE1_DELETE_MANIFEST.json',permanent_rule=False),dict(id='MC-CLOSURE',category='engineering_error',symptom='First247-test migration: missing Failure Memory evidence and actual SIM revision directory',repair='Copy required exact files; keep all original assertions',evidence='REGRESSION_INITIAL_FAILURE.txt',permanent_rule=False),dict(id='MC-SHARED-ARM',category='data_identity_error',symptom='Historical shared ARM.json contains G03 views for a G01 replay',confirmed_cause='Per-case G01_HERO_WEIGHTS/gradient artifacts contradict overwritten shared config',repair='Use actual per-case frozen identities, not new selection',evidence='REPLAY_PROTOCOL_REVISIONS/001/DEPTH_FAILURE.json',permanent_rule=False),dict(id='MC-INITIAL-CONTAINER',category='engineering_error',symptom='Array-identical reserialized INITIAL ZIP differs from original013 file SHA',repair='Copy original013 container byte-for-byte; retain cache separately',evidence='REPLAY_PROTOCOL_REVISIONS/002/INITIALIZATION_FAILURE.json',permanent_rule=False),dict(id='MC-SCIENCE',category='scientific_negative',symptom='G01 root exposure/fixed-frame GT worsening and G03 per-view protection remain',repair='Retain original findings; no scientific repair in maintenance',evidence='../../mainline/results/FAILURE_REGISTRY.json',permanent_rule=False)]
save(T/'FAILURE_REGISTRY.json',dict(task='TASK-MAINLINE-ASSET-CONSOLIDATION-001',records=failures,permanent_promotion=False,scientific_certification=False))

readme='''# Ring-First 3D — 当前主线入口

当前状态：**ACTIVE_RESEARCH_MAINLINE**。工程重放通过，尚非CERTIFIED_SCIENTIFIC_BASELINE。

先读 [PROJECT_HOME](docs/PROJECT_HOME.md)、[mainline README](mainline/README.md)、[PIPELINE](mainline/PIPELINE.md) 和 [MAINLINE_ASSET_MAP](mainline/manifests/MAINLINE_ASSET_MAP.json)。规范代码在src/ring_first_3d；mainline提供配置、运行入口、依赖锁和精选结果。

活动路线：EXACT013 Init-A → Deformation Graph + Smooth ARAP → 嵌入式B-spline/RMF → Boolean Union → 多视角轮廓与Ring验收。

- G01：外露1.726844mm；FIT/HOLDOUT0.932784/0.933253；自动门禁通过，但近端局部外露0.047185mm、固定INITIAL→GT框架MAE恶化。
- G03：PER_VIEW_PROTECTION；005两个视角IoU下降0.023444/0.012446，正式柄长NaN。
- 下一阶段：HERO原生深度约束、G03跨视频诊断、根部完整内藏及主体/柄部联合更新；需新TASK/源码锁和科研授权。

运行固定重放：

```bash
bash mainline/scripts/run_ring_first.sh --out /tmp/rf-replay
bash mainline/scripts/run_hero.sh --out /tmp/hero-replay
bash mainline/scripts/run_stalk_growth.sh G01 --out /tmp/stalk-replay
```

入口：[本地主线可视化](mainline/visualization/index.html) · [工程整理报告](maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/TECHNICAL_REPORT.md) · [结果一致性](maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/RESULT_EQUIVALENCE_REPORT.md)。原始数据、权重、官方第三方代码和环境采用LOCAL_ONLY清单，不重复分发。DXY独立只读。
'''
old=(R/'README.md').read_bytes();archive=M/'references/README_BEFORE_CONSOLIDATION.md'
if not archive.exists():archive.write_bytes(old)
text(R/'README.md',readme)
text(M/'README.md','''# 主线科研资产

这是统一入口和可运行资产闭包。状态ACTIVE_RESEARCH_MAINLINE，工程通过不认证三维科学精度。

活动实现位于src/ring_first_3d/mainline/lineage，按原任务版本隔离，避免混合014旧深度、018原生HERO、E1/E2和当前Init-A。既有src的契约、相机变换、Renderer、对应及评价API继续复用。frozen_registry保存原SHA源码供既有AST适配器直接读取，无需执行旧工作区脚本。

配置与身份：[资产表](manifests/MAINLINE_ASSET_MAP.json)、[来源](manifests/SOURCE_PROVENANCE.json)、[依赖锁](manifests/DEPENDENCY_LOCK.json)、[外部数据](manifests/EXTERNAL_INPUTS.json)、[工程状态](manifests/REPRODUCIBILITY_STATUS.json)。[流水线](PIPELINE.md)列出实际调用。

默认脚本是**固定输入工程重放**，不是新的科学优化任务。Body Update重放已保存Graph节点变换，Growth重建保存的样条并重新做Boolean/投影；真实HERO命令执行一次新的官方原生推理。原优化器源代码完整保留，未来科研执行须新TASK、数据/源码冻结和Policy门禁，不直接重跑历史协议。

保留G01的数值改善及根部缺陷、G03正式NaN和全部关键失败证据。原始RGB/Mask/GT/深度/权重留原位；旧目录仍有唯一资产及LOCAL_ONLY绑定，所以本轮没有整体删除工作区。临时环境依赖已复制到本项目.runtime并逐文件锁定，不创建新虚拟环境。

同机首次检出需要按manifests/RUNTIME_FILES.json恢复LOCAL_ONLY运行库，并从SITE.example.json配置SITE.local.json；受控数据和官方checkpoint必须事先存在。跨机器尚未认证，尤其Python/CUDA ABI、绝对数据路径和原生二进制需重新核验。

固定重放入口：run_ring_first.sh、run_hero.sh、run_body_initialization.sh、run_body_update.sh、run_stalk_growth.sh、run_a_to_b.sh、run_depth_supervised.sh。全部要求新--out目录，拒绝覆盖。

[可视化](visualization/index.html)保留实际Mesh与图像。完整盘点平面CSV/JSON为LOCAL_ONLY，Git中inventory/*.gz是其逐字节压缩副本，可用unpack_inventory.py还原并核验哈希。
''')
text(M/'PIPELINE.md','''# 固定输入主线运行与数据流

1. run_ring_first.sh：真实Ring Mask + RGB地图 → 原RF5DoF/SIFT-PnP/yaw → OpenCV c2w/mm。数值解不当作pose GT。
2. run_hero.sh：真实四帧、冻结公制相机 → 官方MVSAnywhere/HERO → 352×640原生轴向Z → 真实Raw Mesh/FaceID/PixelID。checkpoint仅加载，不训练。
3. run_body_initialization.sh：原始EXACT013容器 → 同一initialize函数 → 固定拓扑/公制Body；E1/E2只保留独立参考，不能替换。
4. run_body_update.sh：同一初始Body + 保存的32节点旋转/平移 → 原Graph.mesh；同时检查Smooth ARAP能量。重放不是重新优化36轮。
5. run_stalk_growth.sh G01/G03：冻结STEP024、保存的5控制点/双轴 → 16站×16角RMF Sweep → Blender EXACT Union → 新投影/对应/Ring及完整几何验收。
6. G01保持自动接受；G03必须重现PER_VIEW_PROTECTION。内部弧不计柄长，正式G03仍NaN。根截面缺陷保持披露。
7. run_a_to_b.sh：原A三角面+原A RGB → 冻结B相机，B颜色/Mask仅在预测保存后评价。输出RGBA、FaceID、重心、深度和完整未匹配域。
8. run_depth_supervised.sh：原018真实native观测与初始Mesh → 原PyTorch3D首次命中/barycentric损失及梯度；与历史实际梯度数组比较，T28旧块另存。

以上是两个已验证区块：相机/HERO真实固定样本，以及EXACT013→保存Graph状态→保存Sweep→新几何/投影验收的checkpoint continuation。尚未将HERO反馈接入当前Body优化，也未执行新的从原图到训练收敛的科研全链。各区块身份与实际输入在清单中，不能将旧checkpoint重放说成重新训练。

运行脚本统一调用mainline/scripts/python.sh与ring_first_3d.mainline.cli。每次先校验源码、输入及运行库哈希，并禁止执行旧实验目录Python代码；输出不可覆盖。原Policy Preflight、Contracts、Reuse Audit、Smoke和247项回归已在此入口环境实际执行。
''')
text(R/'docs/PROJECT_HOME.md','''# 项目入口

当前唯一规范入口：[mainline README](../mainline/README.md) → [PIPELINE](../mainline/PIPELINE.md) → [资产映射](../mainline/manifests/MAINLINE_ASSET_MAP.json)。根README给出最新状态和命令。

ACTIVE_RESEARCH_MAINLINE：EXACT013 Init-A → Graph/Smooth ARAP → 嵌入式样条/RMF生长 → Boolean → 多视角投影与Ring门禁。G01自动门禁通过但根部/固定GT框架仍有问题；G03正式NaN。工程测试通过不等同于科学验收。

下一阶段为HERO原生深度、G03的005配准、根截面完整嵌入及主体柄部联合更新。DXY只读；相机、原始数据和历史结果保留冻结边界。

历史科学报告由原commit和SOURCE_PROVENANCE追溯；只复制必要代码、协议与代表证据。LOCAL_ONLY的实际输入和官方权重见EXTERNAL_INPUTS；跨机器配置及ABI仍需核验。
''')
text(R/'docs/architecture/SYSTEM_OVERVIEW.md','''# 系统结构

统一代码包src/ring_first_3d继续承载契约、视角、初始化、Renderer、对应、配准和评价。mainline/lineage是版本隔离的既有算法源码闭包；native是经来源核验的Ring-First/HERO适配器；frozen_registry供原AST API读取原SHA定义。

mainline提供运行入口、配置、来源/依赖锁、精选结果和离线可视化。外部原始数据、官方代码、checkpoint与既有venv不混入算法包。.runtime是复制且核验过的本机编译库，LOCAL_ONLY。

工程状态PASS；科学状态ACTIVE_RESEARCH_MAINLINE。Graph节点及样条状态是历史checkpoint重放，不是新的训练结果。
''')
text(R/'docs/architecture/DATA_FLOW.md','''# 数据流与冻结边界

```mermaid
flowchart LR
 RGB[原始RGB/Mask] --> RF[Ring-First公制相机]
 RF --> HERO[官方HERO原生Depth/Mesh]
 I[EXACT013输入] --> G[Graph + Smooth ARAP]
 G --> S[嵌入式B-spline/RMF]
 S --> U[Boolean外部统一Mesh]
 RGB --> P[新轮廓对应/逐视角保护]
 U --> P
 CAD[固定Ring CAD] --> R[双向Ring非恶化]
 U --> R
 P --> F[预测冻结]
 R --> F
 F --> E[独立GT/可视化]
 HERO -.未来任务引入深度约束.-> G
```

本维护任务不执行虚线的新科学耦合；HERO独立固定样本推理、主体checkpoint链分别重放。FIT/HOLDOUT、相机及原始深度不改；GT不参与新参数选择。
''')
text(R/'docs/registry/DEPENDENCY_GRAPH.mmd','''flowchart TD
 HOME[README / PROJECT_HOME] --> MAP[MAINLINE_ASSET_MAP]
 MAP --> SRC[src/ring_first_3d/mainline]
 SRC --> REG[frozen_registry 原SHA源码]
 SRC --> VERS[lineage 版本隔离算法]
 SRC --> NATIVE[Ring-First / HERO native]
 SRC --> RT[LOCAL_ONLY runtime manifest]
 NATIVE --> OFF[官方MVS / DINO / checkpoint SHA]
 VERS --> DATA[EXTERNAL_INPUTS 冻结原始资产]
 SRC --> GATE[SHA / 旧源码执行拒绝 / 247回归]
 GATE --> REPLAY[8个固定重放]
 REPLAY --> NEG[原科学结论与负证据保持]
''')
prefix='''# 主线资产整理更新

规范入口为mainline/README.md及MAINLINE_ASSET_MAP。ACTIVE_MAINLINE、REUSABLE_REFERENCE、HISTORICAL_EVIDENCE与DEPRECATED_EXPLORATION必须分别使用；工程PASS不能升格科学认证。旧表为原版本快照，最新调用与数据依赖以mainline清单为准。

'''
for name in ['TECHNICAL_ROUTE_MATRIX.md','REUSABLE_MODULES.md','ASSET_MANAGEMENT_POLICY.md']:
    p=R/'docs/registry'/name;old=p.read_text()if p.exists()else''
    text(p,prefix+old)
with(R/'docs/registry/EXPERIMENT_INDEX.csv').open('a')as f:f.write('\n# TASK-MAINLINE-ASSET-CONSOLIDATION-001,maintenance,ACTIVE_RESEARCH_MAINLINE,8/8 engineering replays; scientific certification false,mainline/README.md\n')
with(R/'docs/registry/ASSET_MANAGEMENT_POLICY.md').open('a')as f:f.write('\n静态历史资产的硬链接去重保留内容和全部路径。禁止原地修改这些历史副本；新任务必须复制到独立输出并用原子替换保存。原始观测、权重和唯一失败证据默认KEEP。Git历史与远端分支不通过本轮清理删除。\n')
for sub in ['ring_first','mvs_hero','body_initialization','body_update','stalk_growth']:
    text(M/'configs'/sub/'README.md','来源、原始参数和代码版本见SOURCE_PROVENANCE及REPLAY_INPUT_FREEZE。重放容差见REPLAY_TOLERANCES；不得看到结果后放宽。当前参数不按病例调节。原协议只读保存于lineage相应任务目录。')
shutil.copyfile(M/'configs/SITE.local.json',M/'configs/SITE.example.json')
for script,module in [('run_ring_first.sh','ring-first'),('run_hero.sh','hero'),('run_body_initialization.sh','body-initialization'),('run_body_update.sh','body-update'),('run_a_to_b.sh','a-to-b'),('run_depth_supervised.sh','depth-supervised-pytorch')]:
    text(M/'scripts'/script,'#!/usr/bin/env bash\nset -euo pipefail\nmainline_script_dir="$(cd "$(dirname "$0")" && pwd)"\nexec bash "$mainline_script_dir/python.sh" -m ring_first_3d.mainline.cli '+module+' "$@"')
text(M/'scripts/run_stalk_growth.sh','''#!/usr/bin/env bash
set -euo pipefail
mainline_script_dir="$(cd "$(dirname "$0")" && pwd)"
mainline_case="${1:-G01}"; if [ "$#" -gt 0 ]; then shift; fi
case "$mainline_case" in G01) mainline_module=stalk-growth-g01;; G03) mainline_module=stalk-growth-g03;; *) exit 2;; esac
exec bash "$mainline_script_dir/python.sh" -m ring_first_3d.mainline.cli "$mainline_module" "$@"
''')

# New measured figures, no synthetic illustration.
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
h=M/'validation/replays/003/hero/hero';a=dict(np.load(h/'HERO_native.npz'));b=dict(np.load(Path(read(M/'configs/SITE.local.json')['controlled_example'])/'historical/HERO_native.npz'));rgb=dict(np.load(h/'NATIVE_RGB_LABELS.npz'))
fig,axes=plt.subplots(1,3,figsize=(12,4));axes[0].imshow(rgb['RGB']);axes[0].set_title('Actual native RGB / G01');im=axes[1].imshow(a['depth_mm'],cmap='viridis');axes[1].set_title('Fresh official axial depth / mm');fig.colorbar(im,ax=axes[1],fraction=.04);im=axes[2].imshow(abs(a['depth_mm']-b['depth_mm']),vmin=0,vmax=.02,cmap='magma');axes[2].set_title('Absolute difference to frozen output / mm');fig.colorbar(im,ax=axes[2],fraction=.04)
for ax in axes:ax.axis('off')
fig.tight_layout();p=M/'visualization/hero/NATIVE_REPLAY.png';p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=120);plt.close(fig)
p=M/'visualization/a_to_b/A_TO_B.png';p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(M/'validation/replays/003/a-to-b/A_TO_B.png',p)
text(M/'visualization/index.html','''<!doctype html><meta charset="utf-8"><title>Ring-First 3D Mainline</title><style>body{font:16px sans-serif;max-width:1500px;margin:auto}img{max-width:100%}</style>
<h1>ACTIVE_RESEARCH_MAINLINE</h1><p>8/8工程重放通过；科学状态未认证。G01近端局部外露及固定GT框架误差恶化、G03投影拒绝均保留。</p>
<p><a href="../../maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/TECHNICAL_REPORT.md">维护报告</a> · <a href="../results/TECHNICAL_REPORT.md">原科学报告</a> · <a href="stalk_growth/index.html">完整G01/G03 Mesh与根部证据</a> · <a href="../manifests/MAINLINE_ASSET_MAP.json">资产入口</a></p>
<h2>原生HERO新推理重放</h2><img src="hero/NATIVE_REPLAY.png"><h2>实际A→B</h2><img src="a_to_b/A_TO_B.png"><h2>G01实际连接与保留缺陷</h2><img src="stalk_growth/figures/G01_ROOT.png"><h2>G03正式失败</h2><img src="stalk_growth/figures/G03_PROXIMAL_CAP_AUDIT.png">
''')

# Pack complete metadata for Git without huge flat blobs; exact flat files stay local.
packs=[]
for name in ['ASSET_INVENTORY.csv','ASSET_INVENTORY.json','DUPLICATE_ASSET_REPORT.json','DEPENDENCY_REFERENCE_GRAPH.json']:
    p=T/name;dest=T/'inventory'/ (name+'.gz');dest.parent.mkdir(exist_ok=True)
    with p.open('rb')as src,gzip.open(dest,'wb',compresslevel=6)as dst:shutil.copyfileobj(src,dst)
    packs.append(dict(flat_path=name,flat_sha256=sha(p),flat_bytes=p.stat().st_size,packed_path=str(dest.relative_to(T)),packed_sha256=sha(dest),packed_bytes=dest.stat().st_size))
save(T/'INVENTORY_PACK_MANIFEST.json',dict(files=packs,flat_files_LOCAL_ONLY=True,compressed_files_contain_complete_exact_inventory=True))

v=os.statvfs(R);storage=dict(measured_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),initial_scoped_files=initial['files'],initial_scoped_logical_bytes=initial['logical_bytes'],phase1_measured_free_gain_bytes=cleanup['measured_free_byte_change'],current_filesystem_free_bytes=v.f_bfree*v.f_frsize,current_user_available_bytes=v.f_bavail*v.f_frsize,net_free_gain_since_phase1_start_bytes=v.f_bfree*v.f_frsize-cleanup['before']['free_bytes'],canonical_workspace_allocated_bytes=int(subprocess.check_output(['du','-s','-B1',str(R)],text=True).split()[0]),old_worktrees_removed=0,original_unique_scientific_assets_deleted=0,Git_history_rewritten=False,remote_historical_branches_deleted=0)
save(T/'FINAL_STORAGE.json',storage)
text(T/'FINAL_STORAGE_REPORT.md','# 最终存储快照\n\n'+json.dumps(storage,indent=2,ensure_ascii=False)+'\n\n阶段1实测释放与最终净增加分别统计；新工作区、完整盘点元数据和重放产物占用部分新空间。没有把逻辑文件大小或Git当前树删除当远端历史释放。旧worktree有唯一资产或LOCAL_ONLY绑定，全部保留。')

report=f'''# TASK-MAINLINE-ASSET-CONSOLIDATION-001

**工程验收：PASS。原247项回归0失败/0跳过，Preflight、Contracts、Reuse Audit、Smoke通过，8/8关键模块从新路径重放并与冻结结果比较通过。科研状态仍为ACTIVE_RESEARCH_MAINLINE，绝非CERTIFIED_SCIENTIFIC_BASELINE。**

统一入口：{R}/mainline/README.md。实际代码在src/ring_first_3d（mainline/lineage版本隔离、native相机/HERO、frozen_registry原SHA数学来源）。完整配置、真实输入、编译库及checkpoint身份均有清单；执行audit拒绝从原实验工作区运行Python代码。

## 16项验收问题

1. 整理前：df显示197G文件系统已用187G、可用0；扫描{initial['files']}资产、逻辑{initial['logical_bytes']:,}字节（含重复，不等同物理占用）。环境/.git与其科研资产分别记录，原始命令见INITIAL_COMMANDS。
2. 阶段1实测释放{cleanup['measured_free_byte_change']:,}字节，即{cleanup['measured_free_byte_change']/2**30:.6f}GiB。最终净变化另见FINAL_STORAGE，包含新工作区及完整清单开销。
3. 清理了可再生成缓存及{by_action.get('DEDUPLICATED_PATH_PRESERVED',0)}个独立重复payload；硬链接去重保留每条历史路径、完整内容和引用。操作级分配块与实际文件系统空闲分别统计。没有删除唯一Mesh或官方权重。
4. TSDF/NeuralFusion/MonoSDF等冗余副本已去重；唯一中间checkpoint/负证据及依赖不明资产保留。两份大归档各含124个无独立副本成员，未删。MonoSDF仍是未完成充分训练，不能称充分训练后失败。
5. 保留Ring-First源码、官方HERO加载/推理/回投影、E1/E2九参数/完整Mask参考、013/014/015、Graph/SmoothARAP、Sweep/RMF/Union、T28旧深度与T30原生深度独立实现、A→B、P0、跨视频BA、重要负结论与代表图。原完整历史由commit及原路径追溯，不迁入所有运行目录。
6. 集中到{R}，README/PROJECT_HOME/mainline README/PIPELINE/MAINLINE_ASSET_MAP构成五个入口文件。mainline仅组织配置/运行/结果，代码继续在既有包。
7. Ring-First真实固定输入重放PASS，相机矩阵max abs={res['ring-first']['c2w_max_abs']:.3g}；不是独立pose GT。
8. HERO一次新官方原生推理PASS，深度逐bit相同，Raw顶点/面/PixelID相同；未用历史深度冒充推理。checkpoint未复制，官方源码实际核验commit为5bd49bba0992aa56060e1aa3bb40b2150b04726f；旧4483…是父项目身份误记，保留原纠正记录。
9. 初始化真实原013容器SHA相同、五类Mesh数组一致；Graph保存状态通过原函数实际生成Body，最大误差{max(x['max_vertex_error_mm']for x in res['body-update']['cases']):.12g}mm，SARAP能量实际计算。没有重新优化36轮或按病例改算法。
10. G01保存样条由新路径重建，真实Blender Union顶点误差0、面索引相同、全FIT投影变化误差0。总弧长2.530961、嵌入0.804116、外露1.726844mm；Ring双向不恶化，自交0。但近端截面0.047185mm局部露出及固定INITIAL→GT框架MAE恶化保持。
11. G03同样真实生成Union并重投影；PER_VIEW_PROTECTION拒绝被复现，005两视角下降0.023444/0.012446，正式柄长NaN，失败尝试/根审计保留。
12. A→B实际源面与原A RGB重投影PASS，RGBA/z/FaceID/重心/CAD深度/有效域逐bit相同；B颜色和Mask仅后评价，原位姿是条件性状态。
13. 原018 T30 PyTorch3D/native-depth前向、损失、梯度PASS；加权loss误差{res['depth-supervised-pytorch']['loss_abs_error']:.3g}，历史梯度相对误差{res['depth-supervised-pytorch']['gradient_relative_error']:.12g}（原阈值1e-4）。T28旧观察模型另存，未混成一个模块。
14. 对比明细如下；全部预冻结容差未放宽。路径适配通过逆变换AST比较，科学公式不变。
15. 外部依赖仍包括受保护原始观测/Mask/GT/相机缓存、官方MVS/DINO源码与checkpoint、既有venv、Open3D等官方库；本项目.runtime中的编译包已复制并核验，不依赖删掉的旧实验源码。逐资产大小、SHA和用途见EXTERNAL_INPUTS/RUNTIME_FILES；受控数据原位保留。
16. 跨机器尚需受控数据授权提供/路径重绑定、原HERO权重、Python/CUDA/PyTorch3D ABI及官方第三方源码；不能宣称空机器开箱即用。新科研优化还需新TASK/Policy授权，本轮仅checkpoint continuation和固定模块重放，未新接入HERO反向更新Body。

{equiv}

## 工程故障、复现版本与清理边界

新协议修订1保留了共享ARM.json错绑G03的失败；修订2保留了把后期重序列化cache当原013容器的SHA失败；修订3全部8项通过。两次均只修复输入身份/接口，没有改变数学参数或数值容差。源码/配置快照与失败JSON在REPLAY_PROTOCOL_REVISIONS，不覆盖原历史。

COPY_VERIFICATION逐文件记录原路径/任务/commit/原SHA/新路径/新SHA/是否适配/依赖。EXACT_COPY字节完全一致；ADAPTED_COPY只改路径，逆适配AST与原算法一致。完整原始Git历史、远端分支、其他项目及DXY保留。原工作区含唯一输入/证据和LOCAL_ONLY绑定，未冒险移除。新维护树仅保留规范算法、冻结协议与精选证据，新增冗余中间副本经PHASE7 manifest清除；原报告与原源目录未清理。

静态引用图没有声称覆盖任意动态调用；实际8项执行轨迹和旧源码执行拒绝补充了运行核验。所有原数据/权重仍可用，失败台账不自动晋升永久规则。硬链接历史资产禁止原地写入，新任务必须独立输出。

## 科研审计表

|审计项目|必须汇报|
|---|---|
|目标组数|物理组G01/G03共2；固定重放模块8；新科学训练0|
|本算法独立成功|本轮为维护，不产生新的科学预测；工程8/8重放通过。原G01只有自动门禁通过|
|本算法失败|保留原G03正式NaN及G01根部/固定框架缺陷；维护接线故障已留证修复|
|历史测量值回退|0；显式历史参数是重放输入与对照，不伪称新的独立测量|
|失败组及具体原因|mainline/results/FAILURE_REGISTRY.json及本任务FAILURE_REGISTRY.json|
|最终统计样本|8固定模块、2物理组；未新增科学精度统计或将8模块当8病例|
|是否使用GT选择算法|否；没有新优化/训练/GT调参，原科学GT评价原样保留|

入口与关键可视化：mainline/visualization/index.html；原完整G01/G03画廊在mainline/visualization/stalk_growth/index.html。全部使用实际图像和三角Mesh。工程通过不修改原科学结论。
'''
text(T/'TECHNICAL_REPORT.md',report)
save(T/'ACCEPTANCE.json',dict(engineering='PASS',regression_tests=247,regression_skipped=0,harness={k:v['status']for k,v in harness.items()},replays={k:v['status']for k,v in res.items()},copy_hash_verification=True,scientific_AST_unchanged=True,source_freeze_sha256=sha(freeze),actual_phase1_free_gain_bytes=cleanup['measured_free_byte_change'],scientific_state='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False,cross_machine_certified=False))
print('Published docs, reports, manifests and exact inventory archives')
