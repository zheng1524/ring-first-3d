"""Write negative-result delivery, provenance and integrity checks; no model calls."""
from common import *
import platform,importlib.metadata
def main():
    status=load(R/'STAGE_STATUS.json');assert status['F1']=='NOT_RUN_F0_STOP'
    assert not list(R.glob('*_F1_RUN.json'))and not list(R.glob('*_F2_RUN.json'))
    metrics={(m,v):load(R/f'{m}_{v}_F0_METRICS.json')for m in ['NN','O3D']for v in ['V6','V2']}
    runs={v:load(R/f'NN_{v}_F0_RUN.json')for v in ['V6','V2']}
    assert all(a['optimizer_steps']==0 and a['learned_parameters_bitwise_unchanged']for a in runs.values())
    frozen=load(R/'provenance/FROZEN_INPUTS.json')['sources'];originals=load(R/'provenance/ORIGINAL_SHA_START.json')['files']
    assert all(sha(a['original']['path'])==a['original']['sha256']==sha(a['frozen']['path'])for a in frozen)
    assert all(sha(a['path'])==a['sha256']for a in originals)
    checked=load(R/'provenance/OFFICIAL_CHECKED_FILES.json')['files'];assert all(sha(a['path'])==a['sha256']for a in checked)
    assert all(not load(R/f'provenance/NN_{v}_F0_ACCESS.json')['training_imported']for v in ['V6','V2'])
    assert all(load(R/f'provenance/BEFORE_NN_{v}_F0.json')['protocol']['sha256']==sha(R/'config/PREREGISTERED.json')for v in ['V6','V2'])
    # Re-read exported geometry; do not repair, smooth, merge or remove faces.
    mesh_checks=[]
    for method in ['NN','O3D']:
        for v in ['V6','V2']:
            a=output_mesh(method,v,'F0');p=R/'meshes'/f'{method}_{v}_F0_m.glb';b=trimesh.load(p,force='mesh',process=False)
            assert len(a.faces)==len(b.faces)
            assert np.array_equal(a.faces,b.faces)
            err=float(np.max(abs(np.asarray(b.vertices)*1000-np.asarray(a.vertices))));assert err<1e-5
            mesh_checks.append(dict(method=method,version=v,PLY_mm_GLTF_m_max_mm=err,original_output_face_N=len(a.faces),all_face_IDs_preserved=True))
    table('MESH_SERIALIZATION_CHECKS.csv',mesh_checks)
    validation=dict(input_SHA_unchanged=True,original_sources_cameras_CAD_SHA_unchanged=True,
        official_code_and_checkpoint_SHA_unchanged=True,protocol_SHA_frozen_before_both_forwards=True,
        GPU_pipeline_forward_N=2,translator_N=2,optimizer_steps=0,learned_parameters_unchanged=True,
        F1_F2_not_run=True,all_output_mesh_faces_preserved=True,GLB_SI_units_verified=True,
        no_GT=True,GT_accuracy='NOT_EVALUABLE',physical_reconstruction_success_N=0,
        engineering_dataflow_output_success_N=1,target_video_N=1,
        planned_primary_prefix_N=3,executed_primary_prefix_N=1,scientific_GATE_B='FAIL_F0_GEOMETRY',
        no_threshold_or_scale_search=True,old3px_test_not_used=True)
    save('FINAL_VALIDATION.json',validation)
    save('config/ENVIRONMENT.json',dict(python=platform.python_version(),torch=runs['V6']['torch'],GPU=runs['V6']['GPU'],
        numpy=np.__version__,Open3D=o3d.__version__,scipy=importlib.metadata.version('scipy'),
        task_local_dependencies=dict(scikit_image='0.23.2',tifffile='2024.8.30'),
        interpreter='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python',shared_environment_modified=False))
    rows=[]
    for method in ['NN','O3D']:
        for v in ['V6','V2']:
            a=metrics[method,v];s=a['rays'][0];value=a['ref08_current_input_values']
            rows.append(dict(method=method,version=v,current_native_visible_N=value['native_CAD_visible_N'],
                current_native_hit_fraction=value['native_hit_fraction'],
                current_native_p95_mm=value['native_depth_error_p95_including_misses_mm'],
                current_native_p95_status=value['native_depth_error_p95_status'],
                fixed_V2_visible_N=s['CAD_visible_N'],fixed_V2_hit_fraction=s['hit_fraction'],
                fixed_V2_agree_fraction=s['agree_fraction_fixed_visible'],fixed_V2_hit_only_MAE_mm=s['depth_error_hit_only_mm']['MAE'],
                fixed_V2_hit_only_p95_mm=s['depth_error_hit_only_mm']['p95'],
                Raw_ref08_area_retention=a['Raw_faces'][0]['area_retention_at_0p25mm'],
                output_area_mm2=a['topology']['area_mm2'],output_faces_N=a['topology']['faces_N'],F0_pass=a['F0_pass']))
    table('F0_SUMMARY.csv',rows)
    fmt=lambda a:'∞（MISS超过5%）'if a is None else f'{a:.3f}'
    summary='\n'.join(f"| {a['method']} | {a['version']} | {a['current_native_visible_N']} | {a['current_native_hit_fraction']:.2%} | {fmt(a['current_native_p95_mm'])} | FAIL |"for a in rows)
    paired='\n'.join(f"| {a['method']} | {a['version']} | {a['fixed_V2_hit_fraction']:.2%} | {a['fixed_V2_agree_fraction']:.2%} | {a['fixed_V2_hit_only_MAE_mm']:.3f} | {a['fixed_V2_hit_only_p95_mm']:.3f} | {a['Raw_ref08_area_retention']:.2%} |"for a in rows)
    holdout='\n'.join(f"| {a['source'].replace('G01_004_','')} | {'输入'if a['source_in_fusion']else'留出/共享上游RGB'} | {a['CAD_visible_N']} | {a['hit_N']} | {a['miss_N']} | {a['agree_fraction_fixed_visible']:.2%} | {a['depth_error_hit_only_mm']['p95']:.3f} |"for a in metrics['NN','V6']['rays'])
    report=f'''# TASK-E3-N0-GATE-B-NEURALFUSION-F0-F2-001

**结论：官方预训练F0推理工程运行成功，但V6和V2均未通过单视角几何门槛；F1/F2依预注册停机条件未执行。未训练、未更新权重、未读取GT。**

本轮继承研究者对V6的明确认可，以及对上一条两阶段任务第二阶段的授权。“开始训练”在该上下文中按已经明确限定的**预训练NeuralFusion有限推理**执行：官方固定网络和权重，optimizer.step()=0。没有扩展到重训或新增来源。

## 冻结输入与真实执行

从A3完成提交b114ee0b5470f98303f20f4e2bcd1ccd1f3e5ed7建立独立分支`exp/TASK-E3-N0-GATE-B-NEURALFUSION-F0-F2-001`。V6和V2各六来源的原生depth/valid与320×240裁剪全部冻结，24文件逐SHA相同。V6原生共103,100点，V2共105,156点；本轮实际各只融合ref08，未把其他五源偷偷用于预测。ref13/ref03只用于投影/原Raw评价，且共享HERO上游RGB，不能称严格盲测。

统一模型域沿用V4/V5/V6：O={cfg()['domain']['O_mm']} mm，L=27.959mm，128³，体素0.2184296875mm。所有版本保持相同模型域、裁剪A/K、原生ID、冻结c2w及12.4mm Ring CAD。公式：X_model=(X_mm−O)/L，Z_model=Z_mm/L，C_model=(C_mm−O)/L，旋转不变；没有逐视频/逐来源调尺度。12组输入坐标合同通过，真正官方GPU反投影最大偏差5.639e−6mm。

模型为[官方NeuralFusion](https://github.com/weders/NeuralFusion/tree/4f0c14f67ad9d2368b68cbeb78c237a6328971e5)，唯一主checkpoint为Gate A已经验证的ShapeNet noise005，SHA256=`3ac6dc9f219449e8aa5a26dec0a77691714e55d4e29da688c79630bf46068bff`，1,403,920参数，严格完整加载。没有使用Tanks权重。网络结构/推理配置不变，仅指定CUDA设备。直接调用官方FusionPipeline.forward及Translator；官方get_translation以AST原样提取，避免导入会读取GT的训练/数据库包装。该官方128³分支只译码非零latent的已观测索引，并按本次所有观测点一次查询归一count；未自行换成依赖分块的计数归一。

空latent[128,128,128,17]和count[128,128,128]全零，每版本独立reset。n_samples=±3，nearest提取/整合，SDF输出范围±0.04模型单位=±1.11836mm；eval()+inference_mode()，所有参数requires_grad=False，前后逐值一致。两次GPU融合前向分别0.491s/0.363s，融合+译码及保存约1.599s/1.278s（不含导入和CPU评价），峰值分配约644/658MiB。每版本仅一次真实参考前向，没有通过重复输入代替多视角。

## 预先冻结的F0门槛与结果

先冻结config/PREREGISTERED.json，再运行任何模型前向。非CAD遮挡的当前输入原生射线：命中≥90%，首层轴向误差p95≤0.20mm（MISS记+∞），点到输出面0.25mm内保留≥90%，坐标/有限性通过；任何失败停止F1/F2。误差相对原HERO观测，属于接口/几何保真门槛，不是物理GT。旧3px薄结构门槛未使用。参数冻结后没有改阈、缩域、重选像素或搜索。

| 方法 | 输入 | 当前可见原生分母 | 首层命中率 | 首层p95/mm，含MISS | 判断 |
| --- | --- | ---: | ---: | ---: | --- |
{summary}

V6 NN点到面保留96.39%，V2 NN95.86%，均通过；仍不能补偿首层错误。V6 NN当前输入p95=0.936mm明显超限，因此没有启动ref13→F1或ref03→F2。V2 F0是事先允许的同条件控制，不能用它绕过主方案停机。

Matched Open3D只做本轮两份F0控制：同Crop/Mask/K/c2w/顺序，0.2184296875mm体素、4体素截断、官方ScalableTSDFVolume、米制内部/毫米导出。它也没有通过原生首层覆盖门槛；不调成更细体素救PASS。历史D0未重建、未输入本路线，也不作为本次匹配控制。

## 共同分母与清理代价

公平比较固定在**V2 ref08全部13,574个合法原生观测**，其中CAD遮挡499、可见13,075；V6屏蔽的195个本来源点仍留在该分母。未命中单列，不把误差均值的样本自动缩小；下面MAE/p95明确只针对实际命中，不能单独当整体改善证据。

| 方法 | 版本 | 固定分母首层命中 | ≤0.25mm首层一致 | 命中MAE/mm | 命中p95/mm | 全原Raw ref08面积保留@0.25mm |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{paired}

固定分母下NN V6命中12,387、MISS688；V2命中12,480、MISS595，V6覆盖下降0.711个百分点，一致率也没有改善。V6含MISS的固定分母p95=∞，V2=1.240mm。**不能用V6当前较小分母下0.936mm对V2的1.240mm直接宣布清理改进了融合。** 两版共同仍可用的观测未被挑出用于替代主评价；源ID、availability、误差及类别全部保存。

原Raw面积保留分母为所有26,621个原ref08三角面及其原始面积154.977mm²，而非只取好看的主体。评价用Raw不回流预测。较高近面保留不意味着首层正确：一个额外薄层仍可能靠近原面，同时挡在它前方。

## 失败机制与真实射线

V6 NN实际Mesh20,658面、面积323.884mm²、64连通分量、全体闭合；matched Open3D7,274面、面积119.798mm²、60分量、1,196开放边。面积变多和闭合不能证明新增真实可见组织。图1显示NN出现台阶/条纹，主面附近保留但可见深度发生偏移。

官方译码未观测体素初值0不能当成零面。原始SDF/occupancy与known mask分开保存；MC前仅为复现官方导出将Unknown置+0.04哨兵，**没有向原深度填假值或声称Unknown为观测自由空间**。全部原输出面保留。按MC单元8角是否都已观测，12,594/20,658面（60.96%）邻接Unknown；FACE_VALIDITY.csv逐Face ID标注。这是边界可靠性代理，不是真错误标签。

固定ref08分母有4,495条已命中但首层偏差＞0.25mm，其中991条命中Unknown邻接面、3,504条落在8角已观测单元。因此，**首层失败不能只归因于Unknown闭合**；学习到的局部场/离散化同样未满足观测保真合同。分布域差异和稀疏Mask输入可能有关，但没有本轮因果消融证据，不将其写成已证实原因。

图3的最差当前有效ref08原生ID166099，HERO轴向深度40.970680mm，输出首次交点39.267303mm，偏差−1.703377mm。同一真实射线还在39.616440、40.630611、41.105537、41.228394、41.647175mm相交；没有靠删输出面制造单层PASS。曲线只插值已生成场，不再调用模型。原生图像和ID用于定位，未据此改相机或调输入。

## ref08→ref13与额外参考投影

| 参考 | 身份 | 固定可见分母 | 命中 | MISS | 首层≤0.25mm一致 | 命中误差p95/mm |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{holdout}

ref13存在约0.5–1mm及更大的HERO相对深度差异，图2完整展示；ref03也未与仅ref08的结果对齐。HERO本身不是真值，不能据此单独判相机错误或宣布模型物理失真；本轮不做参考级深度校正或姿态修正，也未删除困难参考。只有一视角被融合，因此无多视角接缝改善/新增表面/顺序效应的实验结论，均NOT_RUN。

## 交付与停止

- `meshes/*_mm.ply`：四份实际未删Mesh，毫米；`*_m.glb`：同Face ID的米制glTF，序列化误差＜1e−5mm。原infer产生的`*_mm.glb`仅为本地诊断，未作为标准glTF交付。
- `F0_SUMMARY.csv`、各RAYS/RAW_FACES表、FACE_VALIDITY、F0_FAILURE_DIAGNOSIS、STAGE_STATUS、FINAL_VALIDATION及固定源/坐标/权重SHA均提供。
- `local_results/`完整latent/count、SDF/occupancy/known、逐原ID射线及Raw面距离保留本地；不上传权重、视频或大型原始HERO。
- 图1：同相机同尺度Raw/Open3D/NN；图2：真实RGB与首层；图3：Unknown/真实射线失败；图4：V2/V6同尺度。
- 全部旧数据、V4/V5/V6源输入、Ring-First/HERO/CAD/P0/Dxy不变；不重训、不新增视角，不做后处理掩盖失败。

**当前不具备按原门槛推进F1/F2的条件。GPU代码可运行与科学几何就绪是两个判断；缺口是稳定的首层观测保真，以及Unknown边界/闭合层的可解释输出合同。已停止，等待研究者/PM审阅。**

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 1视频G01_004；主方案计划F0–F2三个前缀，实际只执行F0；V2做F0控制 |
| 本算法独立成功 | 1/1视频有数值Mesh（两版F0）；几何门槛通过0/1；多视角融合未执行 |
| 本算法失败 | G01_004 F0：首层p95超限；F1/F2=NOT_RUN；物理测量值/GT误差NaN |
| 历史测量值回退 | 0；原Raw只评价/展示；无历史融合参与预测 |
| 失败组及具体原因 | 本视频完整失败见FAILURE_LEDGER.md、Fig1–Fig4和逐原ID表 |
| 最终统计样本 | 固定V2原生观测ref08/ref13/ref03全部保留；ref0813,574、CAD可见13,075；未仅报告命中像素 |
| 是否使用GT选择算法 | 否；前向前协议SHA冻结。物理直径中位绝对相对误差/MAE/p95/max均NOT_EVALUABLE，未读GT |

![Mesh对照](figures/Fig1_Real_Mesh_Comparison_F0.png)
![真实投影](figures/Fig2_Real_Projection_First_Depth.png)
![失败射线](figures/Fig3_Unknown_Closure_And_Real_Ray.png)
![清理对照](figures/Fig4_V2_V6_Same_Scale_Control.png)
'''
    (R/'TECHNICAL_REPORT.md').write_text(report)
    (R/'FAILURE_LEDGER.md').write_text('''# Failure ledger

| ID | 状态 | 失败/限制 | 证据与处理 |
| --- | --- | --- | --- |
| S01 | FAIL / STOP | V6 F0当前输入首层p95=0.935719mm＞0.20；V2 F0=1.240241mm | 两版NN_*_F0_METRICS.json、Fig1/2；F1/F2未运行，不改阈 |
| S02 | OPEN | V6 12,594面邻接Unknown，整体闭合64分量；ref084495条错层中3504落在已观测单元 | FACE_VALIDITY.csv、F0_FAILURE_DIAGNOSIS.csv、Fig3；没有删除输出面或把闭合当准确 |
| S03 | LIMITATION | 清理后固定V2分母首层MISS595→688，覆盖减少0.711个百分点 | F0_SUMMARY.csv，Fig4；不以较小分母下p95减少宣称收益 |
| S04 | FAIL_CONTROL | matched Open3D V6原生命中88.22%，V2 87.89%，未过90%；命中精度较高不能掩盖MISS | O3D_*_METRICS.json；未加细体素重试 |
| S05 | UNRESOLVED | 留出ref13/ref03深度差异、相机和HERO不确定性 | Fig2、全部原生RAYS；不当物理GT，不校正深度/相机 |
| E01 | RESOLVED_BEFORE_GPU | 保存官方training/utils.py时多一个末尾换行，Git blob合同拒绝 | 恢复官方精确字节并核SHA；无执行该训练模块 |
| E02 | RESOLVED_BEFORE_GPU | 缺scikit-image导致推理脚本在import阶段退出，未调用模型 | 仅本任务runtime/python安装0.23.2/tifffile2024.8.30；共享环境未改 |
| E03 | RESOLVED_NUMERIC | MISS为Inf时NumPy线性分位数可能Inf−Inf→NaN | 保持相同分母/阈值，将跨MISS的p95显式记Inf及状态；Open3D判断仍FAIL |
| E04 | NON_SCIENTIFIC | 新worktree sparse-checkout缺lock目录 | 未改变历史分支，保留独立工作树；没有重置或清理其他工作树 |
| E05 | RESOLVED_DISPLAY | Fig2 colorbar覆盖图像 | 移至独立边栏，CPU重绘；未再次运行模型或改数值 |
| E06 | RESOLVED_EXPORT | 初始辅助GLB坐标为毫米，glTF标准按米解释 | 从原PLY另存*_m.glb并核Face ID及尺度；未交付*_mm.glb |

无训练、无权重更新、无GT/Oracle、无新增HERO、无位姿优化。所有失败保留；本轮没有补救搜索或放宽标准。
''')
    (R/'REPRODUCE.md').write_text(f'''# Reproduce

解释器：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`。官方commit/config/checkpoint及24份冻结输入SHA见provenance；原始私人数据需在对应路径可用，不复制大型模型/视频。CPU Open3D0.19来自已审计vendor，Torch2.7.1+cu128来自现有环境；task-local依赖仅scikit-image0.23.2与tifffile2024.8.30。

原执行依次为：prepare.py → infer.py V6 F0 → infer.py V2 F0；matched_open3d.py分别V6 F0/V2 F0；diagnose.py → figures.py → finalize.py。所有文件位于code/。推理脚本严格拒绝覆盖已有RUN，不可在本轮目录直接重复运行。F0失败后F1/F2会被明确拒绝。旧3px不检查。

实际官方model/translator未改，get_translation仅AST提取。下载可读helper时必须使用官方固定commit的training/utils.py，并校验Git blob997c7e67c5f3167fd6c084478ead72f2bdeaaf5e。隔离依赖安装命令见runtime要求；不得pip升级共享环境。

只读复核可运行：
```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B {R/'code/verify_delivery.py'}
```
该命令只检查已冻结输入、代码与模型SHA、原始资产保护、指标算术、PLY/GLB单位和阶段停止，不调用神经模型，不重新融合。

若需复跑，应在独立输出副本中保留相同source/crop/域/参数并移开副本的旧RUN结果；不能覆盖本目录或历史实验。数值来源与正式GPU执行前的代码哈希见provenance/BEFORE_NN_*.json。物理GT未读取，所有深度/面积指标只与同源HERO原观测比较，不是形状准确率。

PLY单位mm，标准GLB单位m；完整latent/count、两通道输出、known mask、逐像素和逐Face数组在local_results，仅本地保存。`sdf_raw`的未观测0必须和known共同解释，绝不能当零面。正式导出使用官方+0.04哨兵，Unknown邻接面完整保留并单独标记。
''')
    (R/'GPU_MVP_READINESS.md').write_text('''# GPU MVP decision

GPU运行兼容性：PASS。ShapeNet官方30个state tensors严格加载，固定1,403,920参数前后逐值一致；两次F0各一次融合/译码，不是训练。

单视角几何门槛：FAIL。V6当前输入p95=0.936mm，V2=1.240mm，均＞0.20mm。固定共同分母也未改善。Unknown邻接闭合面及已观测区首层偏移均未解决。

F1/F2：NOT_RUN_F0_STOP。F3–F5、逆序和训练仍未执行。当前不冻结可正式科学推进的多视角方案，不以新增视角遮盖单视角失败；只提交F0负结果和完整对照，等待研究者审阅。
''')
    print('NEGATIVE_RESULT_DELIVERY_WRITTEN',validation,flush=True)
if __name__=='__main__':main()
