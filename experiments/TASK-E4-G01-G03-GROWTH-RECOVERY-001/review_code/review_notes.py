"""Additional post-freeze geometric diagnostics; no model selection or updates."""
import json,sys
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from io_utils import read,dump,body,source_folder,load_inputs,sha
from ring_collision_gate import signed
from ring_first_3d.multisurface.geometry import scene,closest

def main():
    audit=read(TD/'evidence/POST_RUN_GEOMETRY_AUDIT.json');ev=read(TD/'EVALUATION.json');failure=read(TD/'FAILURE_REGISTRY.json');records=[]
    for r in audit['records']:
        case=r['case'];dest=TD/'review_assets'/case;sw=body(dest/'FINAL_SWEEP_PARAMETERS.npz');original=body(source_folder(case)/'STEP_024/BODY.npz')
        result=body(dest/('FINAL.npz'if r['status']=='NUMERIC'else'FAILED_ATTEMPT.npz'))
        origin=sw['centerline'][0];e1=sw['frame_r'][0];e2=sw['frame_s'][0];normal=sw['frame_t'][0]
        phi=signed(scene(original['V'],original['F_solid']),sw['V'][:16]);xy=(sw['V'][:16]-origin)@np.stack([e1,e2]).T
        fig,axes=plt.subplots(1,2,figsize=(10,4))
        allxy=[]
        for b,color,label in [(original,'gray','frozen STEP024 Body'),(result,'purple','actual final external union')]:
            seg=trimesh.intersections.mesh_plane(trimesh.Trimesh(b['V'],b['F_solid'],process=False),normal,origin)
            projected=(seg-origin)@np.stack([e1,e2]).T;allxy.append(projected)
            axes[0].add_collection(LineCollection(projected,colors=color,linewidths=1,label=label))
        loop=np.r_[xy,xy[:1]];axes[0].plot(loop[:,0],loop[:,1],c='orange',label='actual proximal ring')
        axes[0].scatter(xy[phi>0,0],xy[phi>0,1],c='red',s=30,label='outside original Body')
        span=max(np.linalg.norm(xy,axis=1).max()*1.5,1.)
        axes[0].set(xlim=(-span,span),ylim=(-span,span),xlabel='root-plane e1 mm',ylabel='root-plane e2 mm',title='Actual triangle / proximal-plane intersections');axes[0].set_aspect('equal');axes[0].legend(fontsize=7)
        axes[1].bar(range(16),phi,color=['red'if d>0 else'orange'for d in phi]);axes[1].axhline(0,c='black');axes[1].set(xlabel='proximal-ring vertex ID',ylabel='signed distance to original Body mm',title='negative = internal; positive = exposed')
        fig.suptitle(f'{case}: automatic {r["status"]}; partial proximal-section exposure {phi.max():.6f}mm',fontsize=10);fig.tight_layout();fig.savefig(TD/'visualization/figures'/(case+'_PROXIMAL_CAP_AUDIT.png'),dpi=125);plt.close(fig)
        oldscene=scene(original['V'],original['F_solid']);Q,_,face=closest(oldscene,result['V'][result['F_solid']].mean(1))
        tubephi=signed(oldscene,sw['V']);np.savez_compressed(dest/'SURFACE_PROVENANCE.npz',solid_face_operand=result['solid_face_operand'],nearest_original_face=face,
            original_face_distance_mm=np.linalg.norm(Q-result['V'][result['F_solid']].mean(1),axis=1),construction_tube_vertex_body_SDF_mm=tubephi,
            proximal_ring_signed_distance_mm=phi,root_proximal=origin,root_plane_e1=e1,root_plane_e2=e2)
        records.append(dict(id='GR001-ROOT-'+case,case=case,type='SCIENTIFIC_LIMITATION',symptom='PARTIAL_PROXIMAL_SECTION_EXPOSURE',confirmed_cause='Centerline C0 is internal, but the full elliptical proximal section is not internal. Bounding the center alone does not certify full-section embedding.',max_proximal_vertex_SDF_mm=float(phi.max()),
            evidence='visualization/figures/'+case+'_PROXIMAL_CAP_AUDIT.png',prediction_changed=False,repair='Retain actual geometry; do not tune embedding depth after GT. Review a full-section embedding constraint in a future protocol.',regression='Post-freeze deterministic SDF / actual triangle-plane audit',permanent_rule=False,review=dict(status='unreviewed')))
    records.append(dict(id='GR001-FIXED-GT-FRAME',case='G01',type='SCIENTIFIC_NEGATIVE',symptom='Shape-aligned GT distance improves while fixed-INITIAL-frame distance worsens',confirmed_cause='Measured on independently frozen output. Shape and deployment-frame diagnostics differ; no causal explanation asserted.',evidence='metrics/BODY_METRICS.csv',permanent_rule=False,review=dict(status='unreviewed')))
    records.append(dict(id='GR001-EMPTY-BOOLEAN',case='G01',type='ENGINEERING_ERROR_FIXED',symptom='AxisError after Blender returned empty EXACT union',confirmed_cause='Empty vertex/face arrays were passed to axis-1 centroid operations without validation',repair='Reject empty candidate, retain operands, use original backtracking, checkpoint accepted states',regression='test_actual_empty_backend_regression',evidence='evidence/ENGINEERING_REPAIR_001/ORIGINAL_FAILURE.json',permanent_rule=False,review=dict(status='unreviewed')))
    failure['post_freeze_review_records']=records;failure['frozen_runner_registry']='runs/LOCAL_002/visualization/FAILURE_REGISTRY.json';dump(TD/'FAILURE_REGISTRY.json',failure)
    note='''
## 冻结后的补充几何审阅（必须与自动门禁结论同时阅读）

本轮自动门禁数值输出为 **1/2（G01）**，G03正式预测与柄长为NaN；这不是“两组科学成功”。额外检查发现：中心线近端在Body内部，并不保证整个椭圆近端截面都在内部。G01近端截面顶点最大外露 **0.047185 mm**；G03失败尝试为 **1.449942 mm**。这些是真实缺陷，见新增根截面三角面求交和SDF图，不能称整个近端截面已完全隐入。原实现中“近端cap完全内部”的注释是过强陈述，实际证据以此审阅为准。

外部Boolean并集仍真实连接、闭合且无检测到的自交；上述缺陷是根部形态/近端截面约束不足，不能靠“闭合”掩盖。因此 **G01完成了自动门禁接受的连续柄生成，但不宣称已完全证明理想的内藏根部形态；G03未完成可接受恢复**。原冻结预测、原自动门禁记录及自动报告均未修改，本报告额外区分自动通过与更完整的几何审阅。没有根据这一发现调整嵌入深度、重新选择checkpoint或再次优化。

G01独立尺度固定SE(3)对齐MAE由0.334906降到0.303623 mm；固定INITIAL→GT框架下由0.335972升到0.356988 mm。故只能说轮廓及独立对齐后的形状距离改善，不能宣称原公制框架中的三维定位改善。G03失败尝试同样有独立对齐后距离下降、固定框架误差上升现象；不能将无效候选计入成功结果。

![G01近端截面实际检查](visualization/figures/G01_PROXIMAL_CAP_AUDIT.png)
![G03近端截面实际检查](visualization/figures/G03_PROXIMAL_CAP_AUDIT.png)

## 执行版本与恢复来源

|用途|完整提交或身份|
|---|---|
|原始已审计基线|238c2da1cd842c0eba710a4ec44db5f437bff8e4|
|原运行源码／G03实际优化源码|62c56097916e32da6dde3a3d9018912f76c69378|
|空Boolean工程修复／G01实际重放源码|abd4917f2074cb38e22db9b1b5f55b5ff56e6041|
|本轮算法单元及完整回归|247/247 PASS，包含原始35项与原212项集合|
|正式执行协议|protocols/ENGINEERING_REPAIR_001/TASK.yaml|
|有效完整运行|runs/LOCAL_002；LOCAL_001原样保留|

源码、初始化、相机、Mask、Ring、FIT/HOLDOUT及数据文件SHA256见inputs与TASK_FREEZE；正式Runner身份见RUN_MANIFEST。G03原123次试验经1240个文件SHA绑定恢复，没有第二次执行优化；G01工程重放的83次候选在同一冻结预算内，科学参数与旧协议逐项相同。没有重跑Body形变、没有新候选搜索、没有GT调参。未进行G05、HERO或DXY实验。
'''
    p=TD/'TECHNICAL_REPORT.md';text=p.read_text();text=text.replace('## 结论与逐组失败',note+'\n## 原冻结Runner报告：结论与逐组失败',1);p.write_text(text)
    (TD/'RESULT_CARD.md').write_text('''# RESULT_CARD — G01/G03 Growth Recovery

- 自动门禁输出：1/2；G01连续Boolean并集通过，G03投影保护失败，正式预测/柄长NaN。
- G01中心线：总弧长2.530961 mm，嵌入0.804116 mm，**外露柄长1.726844 mm**。新增体积13.331181 mm³；自交0、非流形边0，双向Ring变化0。
- G01 FIT/HOLDOUT IoU：0.892030/0.876787 → 0.932784/0.933253。
- G01独立SE(3)对齐GT MAE：0.334906→0.303623 mm；固定INITIAL→GT框架：0.335972→0.356988 mm（恶化）。
- G03：005两个视角IoU下降0.023444/0.012446，超过0.01门槛。失败尝试外露弧长5.428867 mm，仅诊断，不能作为正式柄长。
- **根部审阅缺陷：**G01/G03近端截面局部最大外露0.047185/1.449942 mm；中心线内嵌不等于整个根截面内藏。不能宣称两组完整科学成功，保留负证据，不事后调深度或重选结果。
- 247项回归全部通过；源码/输入/新协议冻结。G03恢复有效原阶段，G01仅重放工程失效阶段；没有其他组、相机、GT训练、HERO或DXY更新。

完整结果：[技术报告](TECHNICAL_REPORT.md) · [可视化](visualization/index.html) · [失败台账](FAILURE_REGISTRY.json)。
''')
    index=TD/'visualization/index.html';s=index.read_text();s=s.replace('</h1>','</h1><p><strong>自动门禁G01通过，G03失败；不能宣称两组完整科学成功。</strong>近端截面局部露出及固定GT框架误差恶化见技术报告补充审阅。<a href="../FAILURE_REGISTRY.json">完整失败台账（含工程与补充几何审阅）</a></p><img src="figures/G01_PROXIMAL_CAP_AUDIT.png"><img src="figures/G03_PROXIMAL_CAP_AUDIT.png">',1);index.write_text(s)
    print('Post-freeze review added; frozen predictions and Runner outputs unchanged.')

if __name__=='__main__':main()
