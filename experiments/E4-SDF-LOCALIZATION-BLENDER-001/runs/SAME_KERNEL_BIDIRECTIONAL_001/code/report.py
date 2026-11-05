"""One concise paired report; old experiment artifacts remain immutable."""
from pathlib import Path
import json,hashlib,csv,datetime,platform
PAIR=Path(__file__).resolve().parents[1]
def load(p):return json.loads(Path(p).read_text())
def asset(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,v):(PAIR/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    cases=[];summary=[]
    for name in ['A_expansion','B_contraction']:
        r=PAIR/'cases'/name;e=load(r/'metrics/GEOMETRY_EVALUATION.json');v=load(r/'metrics/VOLUME_VALIDATION.json');d=load(r/'metrics/GT_OBJECTIVE_DIAGNOSTIC.json');run=load(r/'metrics/FIT_FINISHED.json');g=load(r/'metrics/PROJECTION_GATE.json');b=load(r/'metrics/BLENDER_PHYSICAL_AUDIT.json');offset=load(r/'metrics/GT_PIXEL_CONTOUR_OFFSET.json');n=load(r/'metrics/NORMAL_RAY_VALIDATION.json');f=e['stages'][-1];i=e['stages'][0]
        passed=e['all_numeric_gates_pass']and b['passed']and g['passed'];status='PASS_REGISTERED_CONTROL_GATES'if passed else'PARTIAL_RECOVERY_PHYSICAL_AMPLITUDE_FAILED';cases.append(dict(name=name,r=r,e=e,v=v,d=d,run=run,g=g,b=b,offset=offset,normal=n,f=f,i=i,passed=passed,status=status))
        summary.append(dict(case=name,status=status,iterations=run['iterations'],function_evaluations=run['function_evaluations'],seconds=run['seconds'],fit_IoU_initial=i['fit_IoU'],fit_IoU_final=f['fit_IoU'],holdout_IoU_initial=i['holdout_IoU'],holdout_IoU_final=f['holdout_IoU'],center_error_mm=f['parameter_center_error_mm'],Z_error_mm=f['center_Z_error_mm'],region_IoU=f['region_IoU'],direction_agreement=f['direction_agreement'],GT_region_MAE_mm=f['GT_region_error_mm']['MAE'],GT_region_p95_mm=f['GT_region_error_mm']['p95'],GT_region_max_mm=f['GT_region_error_mm']['maximum'],GT_physical_peak_mm=f['GT_directional_peak_mm'],pred_physical_peak_mm=f['pred_directional_peak_mm'],non_target_p95_mm=f['non_target_motion_mm']['p95'],non_target_max_mm=f['non_target_motion_mm']['maximum'],GT_volume_change_mm3=v['GT_signed_volume_change_mm3'],pred_volume_change_mm3=v['pred_signed_volume_change_mm3'],volume_region_IoU_proxy=v['quadrature']['changed_volume_IoU'],genuine_volume_deletion=v['genuine_volume_deletion'],GT_loss=d['GT_loss'],final_loss=d['final_loss'],GT_clearly_better=d['GT_clearly_better']))
    prior=load(PAIR/'assets_index/PRIOR_EXPERIMENT_FREEZE.json');priorchecks=[dict(path=x['path'],unchanged=hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'])for x in prior['files']];assert all(x['unchanged']for x in priorchecks)
    reuse=load(PAIR/'assets_index/ALGORITHM_REUSE.json');assert all(x['parent_sha256']==x['copy_sha256']for x in reuse['identical_files'])
    files=[asset(p)for c in cases for folder in ['inputs','audit_only','local_results']for p in sorted((c['r']/folder).rglob('*'))if p.is_file()];save('assets_index/LOCAL_DATA_INDEX.json',dict(files=files,large_meshes_fields_GT_local_only=True,units='mm except BODY_m.glb in meters'))
    save('assets_index/PRIOR_IMMUTABILITY_FINAL.json',dict(passed=True,files_N=len(priorchecks),checks=priorchecks))
    save('PAIRED_SUMMARY.json',dict(controls=summary,independent_physical_cases=1,total_controls=2,numerical_outputs=2,registered_success=sum(c['passed']for c in cases),both_accurate=False,old_results_unchanged=True,GT_parameter_restart=False,optimizer_or_loss_changed=False,additional_groups_started=False,stopped=True))
    with (PAIR/'PAIRED_SUMMARY.csv').open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator='\n');w.writeheader();w.writerows(summary)
    A,B=cases;a=A['f'];b=B['f'];va=A['v'];vb=B['v'];da=A['d'];db=B['d'];allgates=[x for c in cases for x in c['g']['rows']]
    text=f'''# 同核双向局部几何恢复：技术报告

**结论：收缩组通过本控制的冻结数值门槛，扩张组仍严重欠恢复，未实现两组同时准确恢复。** 两组采用相同初始SDF、Wendland C4、半径、DMTet及原优化器，只改变预登记幅值符号。三维GT不进入优化，预测冻结后才代入原目标做诊断。A的拟合Mask IoU已达{a['fit_IoU']:.4f}，但真实峰值扩张仅为GT的{a['pred_directional_peak_mm']/a['GT_directional_peak_mm']:.1%}，Z偏差仍为{a['center_Z_error_mm']:.3f}mm。B定位和删除区域较好，实际删除{abs(vb['pred_signed_volume_change_mm3']):.4f}mm³，不能将两组的差异解释为单纯的核/离散表达不匹配。未更改损失、参数、预算或阈值，完成两次即停。

## 冻结与公平性

- 当前父目录内新增 `runs/SAME_KERNEL_BIDIRECTIONAL_001`，原149份源码、协议、审计、输入和结果的SHA全部保持。原FINAL未覆盖。
- 两组共享原BASE_FIELD字节、h=0.15mm的64,239节点/137,184四面体、R=1.8200001027435067mm。GT中心复用原先预登记位置，**不使用上一轮拟合中心**；幅值A=−0.39、B=+0.39mm，内负外正。位置/参数仅供生成和冻结后审计。
- 初始、GT及预测均经同一原样Kaolin DMTet提取；不再把原CAD顶点Mesh当本轮GT，也不作GT法向顶点形变。BASE_FIELD中原V/F仅为历史元信息；原seed中使用其均值时a=0，因此不改变实际初始零面。
- `model.py / renderer.py / fit.py / projection_gate.py`与父实验逐字节一致；common只改独立运行目录。相同四参数、初始化、目标、Powell与12轮/500评价预算，未按GT重启或选择更好检查点。3拟合obs01/03/05、2留出obs00/04及固定Ring CAD均保持。
- **A/B分别重跑** BASE/TARGET×5相机的主体、Ring与点投影门禁，全部通过；最差主体IoU={min(x['body_IoU']for x in allgates):.6f}、Ring IoU={min(x['Ring_IoU']for x in allgates):.6f}，未跳过或降低0.99门槛。原Blender/CV/像素中心转换保持。

## 两组结果

| 指标 | A：扩张 | B：收缩 |
|---|---:|---:|
| 正式迭代 / 函数评价 / CPU秒 | {A['run']['iterations']} / {A['run']['function_evaluations']} / {A['run']['seconds']:.1f} | {B['run']['iterations']} / {B['run']['function_evaluations']} / {B['run']['seconds']:.1f} |
| 拟合全可见Mask IoU 初→终 | {A['i']['fit_IoU']:.6f}→{a['fit_IoU']:.6f} | {B['i']['fit_IoU']:.6f}→{b['fit_IoU']:.6f} |
| 留出全可见Mask IoU 初→终 | {A['i']['holdout_IoU']:.6f}→{a['holdout_IoU']:.6f} | {B['i']['holdout_IoU']:.6f}→{b['holdout_IoU']:.6f} |
| 核中心三维误差 / Z有符号误差 mm | {a['parameter_center_error_mm']:.6f} / {a['center_Z_error_mm']:.6f} | {b['parameter_center_error_mm']:.6f} / {b['center_Z_error_mm']:.6f} |
| 实际更新质心误差 mm | {a['update_centroid_error_mm']:.6f} | {b['update_centroid_error_mm']:.6f} |
| 表面实际更新区域IoU | {a['region_IoU']:.6f} | {b['region_IoU']:.6f} |
| GT区域方向一致率（面积加权） | {a['direction_agreement']:.3%} | {b['direction_agreement']:.3%} |
| GT / 预测物理峰值绝对值 mm | {a['GT_directional_peak_mm']:.6f} / {a['pred_directional_peak_mm']:.6f} | {b['GT_directional_peak_mm']:.6f} / {b['pred_directional_peak_mm']:.6f} |
| 物理峰值相对误差 | {a['relative_physical_peak_error']:.2%}，FAIL | {b['relative_physical_peak_error']:.2%} |
| GT区域位移MAE / p95 / 最大 mm | {a['GT_region_error_mm']['MAE']:.6f} / {a['GT_region_error_mm']['p95']:.6f} / {a['GT_region_error_mm']['maximum']:.6f} | {b['GT_region_error_mm']['MAE']:.6f} / {b['GT_region_error_mm']['p95']:.6f} / {b['GT_region_error_mm']['maximum']:.6f} |
| 非目标区位移p95 / 最大 mm | {a['non_target_motion_mm']['p95']:.6f} / {a['non_target_motion_mm']['maximum']:.6f} | {b['non_target_motion_mm']['p95']:.6f} / {b['non_target_motion_mm']['maximum']:.6f} |
| 邻面角p95 初→终（度） | {A['i']['quality']['normal_angle_deg']['p95']:.3f}→{a['quality']['normal_angle_deg']['p95']:.3f} | {B['i']['quality']['normal_angle_deg']['p95']:.3f}→{b['quality']['normal_angle_deg']['p95']:.3f} |

函数评价数为SciPy返回的nfev。原函数缓存仅记录未缓存参数：A为{da['trace_evaluations']}条、B为{db['trace_evaluations']}条；OBJECTIVE_TRACE保留这些实际几何评价，不将重复缓存调用伪作新的几何采样。

主表对GT和预测使用**同一**初始DMTet面上全部11,374顶点的有符号最近曲面距离变化，正向外、负向内；GT实际区固定为|d_GT|>0.01mm，各为A {a['GT_region_N']}、B {b['GT_region_N']}点。没有混用材料顶点位移。SDF系数不等于真实表面位移：相同|a_GT|=0.39mm，GT向外峰值约0.297mm，向内约0.485mm，本就不具相同物理/图像信号幅度。

独立同法线射线核验亦使用GT/预测相同算子，未命中NaN；A最终共同有效11,374/11,374，B为11,023/11,374，未命中351（GT区域832/1176有效）。收缩后原法线可失去同层交点，不能将该子集读数当全部材料点位移，更不能补入GT。完整分母与所有轮次的粗糙度、Ring间隙、连通性见各组 `ROUND_GEOMETRY.csv`。

## 收缩是否真正删除体积？

**是，但“删除发生”与“删除位置准确”分开评价。** B预测节点φ相对初始处处不减，负区为初始负区子集；封闭真实Mesh体积由{vb['initial_mesh_mm3']:.6f}降至{vb['final_mesh_mm3']:.6f}mm³，删除{abs(vb['pred_signed_volume_change_mm3']):.6f}mm³；GT应删除{abs(vb['GT_signed_volume_change_mm3']):.6f}mm³，预测未新增体积。固定同四面体积分的删除区IoU约{vb['quadrature']['changed_volume_IoU']:.6f}，错误删除代理体积{vb['quadrature']['off_target_changed_volume_mm3']:.6f}mm³。积分为固定548,736点的离散代理，Mesh体积差另报，不能冒称精确交集体积。

A实际新增{va['pred_signed_volume_change_mm3']:.6f}mm³，GT新增{va['GT_signed_volume_change_mm3']:.6f}mm³；新增区体积IoU代理仅{va['quadrature']['changed_volume_IoU']:.6f}。高Mask IoU和表面区域重叠掩盖了明显欠扩张。所有保存轮次均闭合、单连通且无FCL检出Ring交叠；初始、GT和最终的独立Blender EXACT交集均0。未平滑、删面或补洞。

## 冻结后的GT目标值诊断

| 原样目标 | A扩张 | B收缩 |
|---|---:|---:|
| GT参数损失 | {da['GT_loss']:.9f} | {db['GT_loss']:.9f} |
| 最终参数损失 | {da['final_loss']:.9f} | {db['final_loss']:.9f} |
| 最终−GT | {da['final_minus_GT']:+.9f} | {db['final_minus_GT']:+.9f} |
| GT是否“明显更优” | 否 | 否 |

按运行前门槛max(0.002, 0.1×|L_GT|)，A的GT损失虽略低，差额未达“明显”；B最终错误几何的目标值反而比GT低。GT的前向Mask重投影仍通过0.99门禁，所以这不是同核GT不能被渲染，而是**原轮廓采样/目标与准确几何不严格一致**。B的Mask XOR项比GT差，轮廓项改善却抵消了它；分项原数值保留，未改权重。

GT几何边缘相对“最内一圈前景像素中心轮廓”的向外偏移均值约0.21–0.37px，是目标存在内缩偏好的机制线索；不是重估相机的理由，也未通过新对照证明唯一因果。相同|a|的拟合目标相对初始净面积变化为A +134像素、B −542像素，收缩信号更强，不能把系数对称当信息量对称。

A初始化中心误差{da['initial_center_error_mm']:.3f}mm，初始Z偏{da['initial_Z_error_mm']:.3f}mm；实际搜索最接近GT中心为{da['closest_visited_center_error_mm']:.3f}mm，但无0.1mm内样本。B分别为{db['initial_center_error_mm']:.3f}、{db['initial_Z_error_mm']:.3f}mm，曾有{db['visited_centers_within_0p1mm_N']}个中心样本在0.1mm内。中心邻近不等于四参数同时正确；初始化、耦合搜索和局部极小仍可能参与，当前诊断不能排除。没有用GT重启、延长预算或按更好中间轮选模。

## 图与复现

![初始、同核GT、最终真实Mesh](figures/Fig1_Paired_Actual_Meshes.png)

![两组五视角目标Mask及预测轮廓](figures/Fig2_Paired_Five_View_Contours.png)

![两组GT与实际更新区域、同算子位移](figures/Fig3_Paired_GT_vs_Predicted_Regions.png)

![逐轮中心、Mask、几何误差、粗糙度和GT损失](figures/Fig4_Paired_Roundwise_Diagnostics.png)

[汇总CSV](PAIRED_SUMMARY.csv) · [完整指标JSON](PAIRED_SUMMARY.json) · [协议](PROTOCOL.md) · [复现](REPRODUCE.md) · [失败记录](FAILURE_LEDGER.md)。输入、场、GT和真实Mesh留本地，路径/SHA见assets_index/LOCAL_DATA_INDEX.json。正式代码冻结提交fceeef8；官方Kaolin原样复用，未部署PyTorch3D或运行GPU训练。

## 固定审计表

| 审计项目 | 汇报 |
|---|---|
| 目标组数 | 2个控制、1个独立物理主体，不冒充2个息肉 |
| 本算法独立成功 | 数值输出2/2；冻结控制门槛B通过1/2；两组同时准确恢复未达成 |
| 本算法失败 | 数值硬失败0/2；A物理幅度失败1/2；临床直径指标NaN/NOT_EVALUABLE |
| 历史测量值回退 | 0；只用获准初始SDF和核验过的底层资产 |
| 失败及具体原因 | A欠扩张/Z偏置，原目标对GT几何不严格最优；见Fig3/4和GT_OBJECTIVE_DIAGNOSTIC |
| 最终统计样本 | 两控制均保留；各5视角、11,374共同表面点，GT区域及射线失效另列，不只报告B |
| 是否使用GT选算法 | 否；GT参数仅生成/授权投影门禁/预测冻结后诊断；原算法字节相同，无半径/优化器消融 |

位移误差中位绝对、MAE、p95、最大与共同样本均见逐轮CSV；直径ARE/MAE/p95/最大NOT_EVALUABLE，本轮不是测量任务。控制结果不认证真实病例、全局唯一性或所有形态。最终[交付完整性检查](assets_index/DELIVERY_VALIDATION.json)核对历史149文件、本轮冻结输入及全部预测SHA，不再次拟合；检查通过不改变扩张失败的科学结果。

**本轮停止。** 同核后收缩较好但扩张仍失败，不能支持“上轮位置偏差主要由表达不匹配造成”的充分结论。前轮GT物理改动不同，也不能用前后误差差直接量化原因；本轮没有继续改目标、重启搜索、开展Ip/Is或其他对照。
'''
    (PAIR/'TECHNICAL_REPORT.md').write_text(text)
    ledger='''# 失败与限制记录

| 编号 | 观察 | 处置 |
|---|---|---|
| A01 | A物理扩张峰值仅GT约42%，Z偏−0.476mm，新增体积不足一半 | 保留失败，不因Mask IoU>0.995宣布成功，不改阈值/半径 |
| B01 | B通过冻结门槛，但物理峰值较GT约大16.7%，仍有非目标位移 | 同时报告最大误差与区域误差，不宣称精确GT重现 |
| D01 | GT参数在原损失下并非严格最优；B最终损失比GT更低 | 记录GT前向投影与轮廓/XOR分项，未修改原目标 |
| D02 | A/B初始化均偏向原视轮廓生成点，搜索与终值不保证全局最优 | 完整保存轨迹；GT诊断后不重启，不挑最佳中间轮 |
| D03 | B同法线交点共同缺失351/11374，含GT区344点 | 保留NaN/完整分母，不用GT或其他距离补齐；主表统一最近面距离 |
| E01 | 事后evaluate.py首次解析存在多余右括号，尚未读取GT或写审计 | 修复并AST检查；不涉及优化代码、预测、标准或第二次拟合 |
| L01 | 四面体积分为固定四点指示函数近似，非精确布尔交集 | 同报封闭Mesh体积差；Ring用独立全三角面FCL及Blender EXACT |
| L02 | 一个IIa主体、两个符号控制，没有Ip/Is/其他位置或方法 | 不外推多主体性能，完成后停止 |

此前父目录149个文件SHA保持，旧FINAL、审计与协议未覆盖。GT参数目标值诊断仅在各自预测冻结后执行，未反向影响任何优化。
'''
    (PAIR/'FAILURE_LEDGER.md').write_text(ledger)
    save('ACCEPTANCE.json',dict(status='MIXED_A_UNDER_EXPANSION_B_PASS',controls=[dict(case=c['name'],status=c['status'],gates=c['e']['gates'],Blender=c['b']['passed'])for c in cases],both_accurate=False,scientific_generalization=False,previous_expression_mismatch_main_cause_established=False,old_parent_files_unchanged=len(priorchecks),stopped=True,no_followup_started=True))
    print('PAIRED_REPORT_WRITTEN',[(c['name'],c['status'])for c in cases],flush=True)
if __name__=='__main__':main()
