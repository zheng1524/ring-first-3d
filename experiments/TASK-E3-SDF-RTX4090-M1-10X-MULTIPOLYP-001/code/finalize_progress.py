"""Publish only audited existing progress; never starts an optimizer."""
from pathlib import Path
import json,csv,hashlib,shutil
R=Path(__file__).resolve().parents[1];B=R/'bundle'


def asset(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)


def main():
    for folder in ['figures','metrics','local_results','provenance']:(R/folder).mkdir(exist_ok=True)
    names=['Progress_Fig1_HERO_and_M1_Stages.png','Progress_Fig2_M1_4000_Six_Views.png',
        'Progress_Fig3_Observed_Inferred.png','Progress_Fig4_Real_RGB_First_Depth.png']
    for name in names:shutil.copy2(B/'figures'/name,R/'figures'/name)
    source=B/'groups/G01_004';summaries=[];reference=[]
    for step in [0,1000,2000,4000]:
        m=json.loads((source/'metrics'/f'single_M1_step{step:06d}_GEOMETRY.json').read_text());rr=m['rays'];den=sum(a['fixed_visible_N']for a in rr)
        summaries.append(dict(step=step,fixed_visible_original_native_N=den,
            hit_N=sum(a['hit_N']for a in rr),hit_fraction=sum(a['hit_N']for a in rr)/den,
            first_agreement_N=sum(a['agreement_N']for a in rr),first_agreement_fraction=sum(a['agreement_N']for a in rr)/den,
            cleaned_HERO_retention_fraction=sum(a['cleaned_HERO_retained_0p25_N']for a in rr)/sum(a['cleaned_visible_N']for a in rr),
            multi_4plus_N=sum(a['multi_4plus_N']for a in rr),multi_4plus_fraction=sum(a['multi_4plus_N']for a in rr)/den,
            negative_grid_volume_mm3=m['negative_grid_volume_mm3'],components_N=m.get('components_N'),
            largest_component_area_fraction=m.get('largest_component_area_fraction'),mesh_area_mm2=m.get('area_mm2'),faces_N=m['faces_N']))
        reference+=rr
    for name,items in [('ACTUAL_STAGE_PROGRESS',summaries),('ACTUAL_PER_REFERENCE',reference)]:
        (R/'metrics'/(name+'.json')).write_text(json.dumps(items,indent=2)+'\n')
    with(R/'metrics/ACTUAL_STAGE_PROGRESS.csv').open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(summaries[0]));writer.writeheader();writer.writerows(summaries)
    evidence=json.loads((B/'metrics/STEP4000_DISPLAY_EVIDENCE.json').read_text())
    (R/'metrics/STEP4000_DISPLAY_EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
    for name in ['MIGRATION_RESTORE_AND_EXTRACTION.json','single_M1_step004000_GEOMETRY.json']:
        shutil.copy2(source/'metrics'/name,R/'metrics'/name)
    mesh=source/'local_results/single_M1_step004000/raw_mm.ply';dest=R/'local_results/G01_M1_step004000_raw_mm.ply';shutil.copy2(mesh,dest)
    assert asset(mesh)['sha256']==asset(dest)['sha256']
    index=dict(status='PROGRESS_REPORTED_NOT_TRAINING_COMPLETE',local_G01_M1_optimizer_steps=4000,
        remote_additional_optimizer_steps=0,remote_extract_only=True,G06_M1='NOT_RUN',G08_M1='NOT_RUN',
        cloud_training_job_published=False,figures=[asset(R/'figures'/name)for name in names],
        raw_mesh=asset(dest),checkpoint=asset(R/'checkpoints/M1_HANDOFF_G01_step004000.pt'),
        portable_bundle=str(B),GT='NOT_EVALUABLE')
    (R/'provenance/ACTUAL_PROGRESS_DELIVERY.json').write_text(json.dumps(index,indent=2)+'\n')
    report=['# 额度中断后的实际进度与可视化','',
        '**本地 G01_004 M1 已完成4000次真实Adam更新；4090新增训练更新0。G06/G08训练NOT_RUN。** 上次中断位于环境迁移阶段，远端长程训练任务尚未发布，不能声称已完成10倍或多息肉实验。','',
        '本轮仅检查状态、读取已有参数、官方零面提取和CPU绘图，optimizer.step=0。服务器仍可连接，独立Python/PyTorch环境安装已完成；未因额度问题自动追加云端训练。', '',
        '## 已保全状态','',
        'G01检查点包含37个模型张量、Adam、scheduler、loss step、完整配置、CPU/CUDA/Python/NumPy RNG和采样位置，4000步状态SHA256：`63a1b05b681fd47929afe2b05437f18bc5ccb9ad28c63056179315cb00859985`。本地累计训练约1675秒（27.9分钟，含阶段提取/监测）。旧M0不计入M1次数。','',
        '远端RTX4090 24564MiB、driver560.35.03、Python3.12.16、PyTorch2.7.1+cu126、Open3D0.19。原本地PyTorch同版cu128，迁移只调整CUDA构建包以匹配现有驱动，未更换网络、损失或数据。官方源码commit12513009。所有选定资产和官方源码SHA通过，真实模型参数在提取前后逐项不变。', '',
        '4000步固定raw SDF的CPU/GPU最大差3.43323e−5mm，低于预先设置的2e−4mm；这证明迁移读取与数值相容，不是训练效果认证。0/1000步复用此前真实导出，2000/4000步在4090用同一官方256³iso0流程重新提取；各阶段相同公制域与显示方式。', '',
        '## 固定原生分母','',
        '|阶段|首层命中|首层≤.25mm|清理HERO点保留|≥4层交点|连通组件|','|---:|---:|---:|---:|---:|---:|']
    for s in summaries:report.append(f'|{s["step"]}|{s["hit_fraction"]:.2%}|{s["first_agreement_fraction"]:.2%}|{s["cleaned_HERO_retention_fraction"]:.2%}|{s["multi_4plus_fraction"]:.2%}|{s["components_N"]}|')
    report+=['',
        '分母始终为三参考原始合法native Polyp 50265，CAD遮挡1624单列，可见48641；清理屏蔽与未命中均不从评价分母删除。条件HERO/相机不是GT，绝对精度NOT_EVALUABLE。', '',
        '2000→4000：主面最近点保留65.48%→67.96%，首层一致43.78%→43.49%基本持平略降，≥4层交点7.89%→22.80%，组件4→12，负区代理体积782.96→733.46mm³（约−6.3%）。最大连通分量仍占99.44%面积，因此小组件增加不等于主体完全碎裂。原生ref08/ref13首层一致有所提高，ref03下降。不能仅凭较完整的外观或近点保留认定整体重建改善。当前同时存在HERO贴合与重复层/小碎片风险，未完成目标训练，不能据此否定MonoSDF路线。', '',
        '## 四张核心图','',
        '![HERO与真实阶段](figures/Progress_Fig1_HERO_and_M1_Stages.png)',
        '![4000步六视角](figures/Progress_Fig2_M1_4000_Six_Views.png)',
        '![观测与推断](figures/Progress_Fig3_Observed_Inferred.png)',
        '![真实投影与首层](figures/Progress_Fig4_Real_RGB_First_Depth.png)', '',
        '图1：0为未训练官方网络初始化，不称重建结果。Raw/Cleaned对照显示原归档面，cleaned按已冻结native有效性映射筛选原面，未移动XYZ；原始完整文件未裁剪，所有列仅使用同一固定毫米显示窗口。', '',
        '图2：268462个原始零面三角形的六视角，无平滑、删组件、补洞或几何后处理，黑色实体为实际Ring CAD。', '',
        '图3：绿色74826面为真实相机首次可见、原Mask/合格HERO深度±.25mm支持的代理；橙色31578面为可见但无支持/冲突；紫色162058面为未见/遮挡，不认证为真实息肉。另有19313面存在至少一个视角BG Mask反证。这些类别并非物理真值。新增自身首层容差.01mm和CAD .002mm仅用于展示诊断，不回写或修改历史评价。所有面保留。', '',
        '图4：三个真实源的原RGB/Mask、真实SDF Mesh首次深度及相对原生HERO轴向误差；MISS/CAD后方留空，不补假深度。绿色是真实Mask，红色是4000步模型可见投影。', '',
        '## 仍未完成','',
        '4090训练性能短测、4000→目标继续优化、G06/G08独立训练及1x/2x/5x/10x长程比较仍未运行。已固定比较N=2000、最低目标20000，但不能将本次提取/绘图算作优化步。控制器代码是未执行候选，不代表已发布远程任务。', '',
        '|审计项目|必须汇报|','|---|---|','|目标组数|3：G01/G06/G08|','|本算法独立成功|现有G01已产生真实4k SDF/Mesh，工程产物1/3；本轮10倍训练完成0/3|','|本算法失败|G06/G08为NOT_RUN，不伪造；物理准确度三组NaN/NOT_EVALUABLE|','|历史测量值回退|0，未读其他路线预测填补|','|失败组及具体原因|额度中断发生在迁移/发布前；没有NaN/OOM训练故障证据|','|最终统计样本|当前仅G01三参考固定原生48641可见观测，不将其算三物理组|','|是否用GT选算法|否；源、配置、源码冻结，GT/Oracle不读|', '',
        '物理MedARE/MAE/p95/max及共同成功组物理配对全部NOT_EVALUABLE。相机仍是原资格，三份G01均INSUFFICIENT_EVIDENCE，仅条件研究入组。']
    (R/'TECHNICAL_REPORT.md').write_text('\n'.join(report)+'\n')
    (R/'FAILURE_LEDGER.md').write_text('# 进度中断与限制\n\n- 用户报告执行额度中断；客观状态为环境已安装、数据已传输、云端优化未启动。\n- 本地M1已完成4000，完整状态已双端保全；G06/G08尚未训练，保持NOT_RUN。\n- 2k→4k多层交点和组件增加，保留风险，不因显示更完整宣布改善。\n- 初次绘图因bundle/metrics目录不存在报错，已创建任务内目录并重跑；模型/评价标准不变，原日志保留。\n- 图4标题曾超出图框，已仅缩短展示标题并重画，未改数据。\n- CUDA12.8→12.6为环境差异，固定raw SDF数值检查通过；不是训练或科学准确性通过。\n- 原场、全部零面、参数、相机、Mask、HERO、CAD、DXY及历史结果均保留，GT未使用。\n')
    print('ACTUAL_PROGRESS_REPORT_AND_FOUR_FIGURES_READY')


if __name__=='__main__':main()
