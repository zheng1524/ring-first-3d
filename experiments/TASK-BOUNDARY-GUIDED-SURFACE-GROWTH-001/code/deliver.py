from common import *
from html import escape
from urllib.parse import quote
def update(title,body):
    p=R/'TECHNICAL_REPORT.md';text=p.read_text()if p.exists()else '# 可信边界引导的增量可见表面生长\n\n状态：RUNNING / EXPERIMENTAL；GT模式NONE。\n\n中文摘要：本轮以连续原始三角面和真实观察边界为基本单位，从既有Cleaned F1恢复曲面，先按相机质量与连续支持面积选择主体，再检验重叠带、边界外延和逐轮更新。用户后续明确允许派生的局部联合配准与接缝优化；旧主体及已接纳补片不再被人为锁死，但原始资产和优化前版本保留。本报告将区分工程接纳、真实跨视角支持、几何变化与尚未认证的物理精度。\n'
    marker='\n## '+title+'\n';start=text.find(marker)
    if start>=0:
        end=text.find('\n## ',start+len(marker));text=text[:start]+(text[end:]if end>=0 else'')
    p.write_text((text+marker+'\n'+body).rstrip()+'\n')
def index():
    md='# 结果索引\n\n[技术报告](TECHNICAL_REPORT.md) · [本地HTML图库](visualizations/index.html) · [用户方向调整](USER_STEERING.md)\n\n本地目录：`'+str(R)+'`\n\n';h='<!doctype html><html lang="zh"><meta charset="utf-8"><title>Boundary Growth</title><meta name="viewport" content="width=device-width"><style>body{font:16px system-ui;max-width:1500px;margin:auto;padding:24px;background:#eee}article{background:white;margin:22px 0;padding:12px}img{width:100%;height:auto}button{padding:10px;margin:5px}</style><h1>可信边界引导的增量式可见表面生长</h1><p>真实XYZ与原始三角面；黑色CAD；优化前后分开。工程接纳不等于GT精度；G07不合格压力、G08有限相机。<a href="../TECHNICAL_REPORT.md">报告</a></p><nav>'
    for k in ['ALL','G01','G06','G07','G08','Fig','local']:h+='<button onclick="filter(\''+k+'\')">'+k+'</button>'
    h+='</nav>'
    for p in sorted((R/'figures').rglob('*.png')):
        rel=str(p.relative_to(R));md+='- ['+rel+']('+rel+')\n';h+='<article data-name="'+escape(rel)+'"><h2>'+escape(rel)+'</h2><a href="../'+quote(rel)+'"><img loading="lazy" src="../'+quote(rel)+'"></a></article>'
    md+='\n## 全部指标\n\n';h+='<h2>指标与几何索引</h2><ul>'
    for p in sorted((R/'metrics').glob('*.csv')):
        if any(sid in p.stem and not(R/f'local_results/scenes/{sid}_Final.json').exists()for sid in ['G01_004','G01_005','G06_004','G07_004','G08_005']):continue
        if p.stem=='new_HERO_sources'and any(not(R/f'local_results/scenes/{sid}_Final.json').exists()for sid in ['G01_004','G01_005','G06_004','G07_004','G08_005']):continue
        rel=str(p.relative_to(R));md+='- ['+p.stem+']('+rel+')\n';h+='<li><a href="../'+rel+'">'+escape(p.stem)+'</a></li>'
    for p in sorted((R/'local_results/glb').glob('*.glb'))if(R/'local_results/glb').exists()else[]:
        rel=str(p.relative_to(R));md+='- 本地GLB：`'+str(p)+'`\n';h+='<li><a href="../'+quote(rel)+'">'+escape(p.name)+'</a>（仅本地）</li>'
    h+='</ul><script>function filter(k){document.querySelectorAll("article").forEach(x=>x.hidden=k!=="ALL"&&!x.dataset.name.includes(k))}</script></html>'; (R/'visualizations/index.html').write_text(h);(R/'RESULT_INDEX.md').write_text(md)
def p0():
    seeds=load(R/'metrics/engineering_seeds.json');scores=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'];body='4物理组/5视频/14既有参考均核验来源。基于用户最新补充，本轮允许局部联合刚体调整已有及新增曲面；旧版本只读保留，不以保护旧结果不变代替几何接纳。\n\n主体按相机质量×(0.55最大连续可靠法向/非留出Mask支持面积＋0.20连续面积比例＋0.15邻帧支持＋0.10法向可靠比例)选择，绝非只按总面积。选中：'+str(scores)+'。分母和逐参考评分见main_surface_scores.csv。\n\nG06/G07/G08工程种子恢复：\n\n|组|Cleaned F1整源点|F2点|F2完整原面|完整原面mm²|原面分量|\n|---|---|---|---|---|---|\n'
    for s in seeds:body+='|'+s['group']+'|'+str(s['Cleaned_F1_source_points'])+'|'+str(s['F2_accepted_points'])+'|'+str(s['F2_complete_original_faces'])+'|'+f'{s["F2_complete_original_face_area_mm2"]:.6f}'+'|'+str(s['face_components'])+'|\n'
    body+='\nENGINEERING_ACCEPTED_SEED表示人工认可局部展示，不是几何GT。没有把整片F1蓝面提升为可信。原始点索引/接受mask/完整面索引与SHA已冻结；新派生位置可在本轮授权下调整。主体全部Cleaned原面保留，最大主分量参与外边界生长，其他原小分量单列保护，不自动作为外部生长边界。源/几何原始版本不改。\n\n边界由只使用一次的原面边提取，按真实Mask/Ring、原网格与Cleaned拓扑区分外部观测终止、Ring遮挡、原深度断裂、清理内孔和选面切口/未知。Ring边界只有另一真实观察能够支持时才可尝试；不是形态先验补面。\n\n本轮重新先行冻结非参考图像评价帧，核查历史HERO源帧身份。G06/G07/G08旧HERO源列表未完整记录，故评价标记历史来源不完全可审计，不虚称全流程盲测。评价帧不参与本轮新的推理/选源/生长。没有GT/Oracle。\n\n![认可新增区域核对](figures/Fig1_engineering_seed_recovery.png)\n\n![G01边界](figures/Fig2_G01_initial_frontiers.png)\n\n![基线与初始场景](figures/Fig3_F1_F2_selected_initial.png)\n'
    update('P0/P1 — 来源、工程种子和实际边界',body);index()
def p2():
    import numpy as np
    summary=[s for s in load(R/'metrics/growth_summary.json')if s['group']in ['G06','G07','G08']];ev=load(R/'metrics/crossframe_comparison.json');tri=load(R/'metrics/actual_triangle_crossframe_support.json');nov=load(R/'metrics/joint_created_novelty_audit.json');sampling=load(R/'metrics/sampling_vs_surface_change.json');body='本轮按最新授权实际实现完整原面补片生长＋有界局部联合配准，**没有把旧主体锁死，也没有仅重跑旧F2点级筛选**。主面/补片均按原始连通分量保持刚性，允许SE(3)派生位置变化；Raw、历史F1/F2、S0、每轮快照、同样选中面片的PreJoint与Joint独立版本均保留。\n\n新参考先按当前可见边界与≥3°未利用方向排序，再运行冻结HERO；不再执行旧配置中的每视频最多1参考限制。新增原面从连接带沿真实共享原边的面邻接图扩展（每轮有限1.5mm），连接带不整片重复显示；EXPLAINED、NOVEL、OCCLUDED、CONFLICT、UNKNOWN完整保留。源像素、原点/面ID和派生H均可回溯，没有补面、重采样或自由形变。\n\n'
    body+='|场景|条件|实际新HERO|接受轮数|新增完整原面mm²代理|最大新增完整源分量mm²|旧S0点位移p95 mm|联合调整轮数|停止|\n|---|---|---|---|---|---|---|---|---|\n'
    for s in summary:body+='|'+s['scene']+'|'+s['condition']+'|'+str(s['new_HERO_attempts'])+'|'+str(s['accepted_steps'])+'|'+f'{s["new_complete_original_face_area_mm2"]:.4f}'+'|'+f'{s["largest_new_complete_source_component_mm2"]:.4f}'+'|'+f'{s["old_geometry_movement_mm"]["p95"]:.4f}'+'|'+str(s['accepted_joint_steps'])+'|'+s['stop_reason']+'|\n'
    body+='\n面积是不同来源原始完整面暴露量的累计，非去重解剖真面积。97轮并不意味着97个有效新视角：G08仅4次新推理，后期很多轮是微小的补片边缘增量。每一轮及零接纳的参考试验都在growth_steps / patch_candidates / view_search表中。NO_VALID_NEW_VIEW表示在冻结的方向和可见边界规则下没有新候选，不能等同原始视频没有更多信息。\n\n### 配准和接缝\n\n原始面的局部重叠带使用Open3D GICP；法向近乎平行时退化为稳健点到平面的单法向偏移，以避免虚构切向自由度。只检查有限一次候选，不调参搜索。校正按刚度3:1（主体/新面）或2:1（已有补片/新面）在新旧分量间分配；原始分量形状、尺度和CAD不变。主体累计平移界0.75mm，其他派生分量1.5mm，旋转界5°；源和非留出邻帧Mask约束用于有限工程接纳，独立目标RGB误差不参与选解。G06实际有GICP将旧分量移动约0.171mm、新面约0.514mm的记录，证明并非仅让新面贴合冻结旧主体。\n\n### 相同冻结真实帧比较\n\n每视频2帧。所有数值以完整B Polyp Mask为分母，逐帧和共同支持像素数见[crossframe_comparison.csv](metrics/crossframe_comparison.csv)。原历史点中心协议未改；三角面射线命中仅作为新增独立口径，不能混作点覆盖率或精度。G07不合格压力测试、G08有限条件均单列。\n\n|场景|方法|点中心平均覆盖%|实际原面命中覆盖%|点支持RGB MAE/255|\n|---|---|---|---|---|\n'
    for s in summary:
        sid=s['scene']
        for method in ['Initial_S0','Historical_F2','F3_PreJoint_SameFaces','F3_Joint']:
            rr=[x for x in ev if x['scene']==sid and x['method']==method];tt=[x for x in tri if x['scene']==sid and x['method']==method];body+='|'+sid+'|'+method+'|'+f'{100*np.mean([x["coverage"]for x in rr]):.3f}'+'|'+f'{100*np.mean([x["coverage"]for x in tt]):.3f}'+'|'+f'{np.mean([x["RGB"]["MAE"]for x in rr]):.3f}'+'|\n'
    body+='\nPreJoint与Joint使用完全相同的选中原面，前者恢复原坐标，并不是另行用目标误差调参得到的替代算法。G06实际原面命中覆盖S0约93.76%→Joint96.45%；G08约85.10%→86.01%，但其PreJoint86.22%略高于Joint，表明接缝拟合好并不必然改善另一视角。\n\n### 重要反例：点采样与几何覆盖不能混淆\n\n|场景|旧点中心支持消失/目标%|旧实际原面支持消失/目标%|接纳面中调整前已被解释面积mm²|\n|---|---|---|---|\n'
    for s in summary:
        sid=s['scene'];ss=[x for x in sampling if x['scene']==sid];nn=[x for x in nov if x['scene']==sid];body+='|'+sid+'|'+f'{100*np.mean([x["point_center_old_support_lost_fraction"]for x in ss]):.3f}'+'|'+f'{100*np.mean([x["triangle_old_support_lost_fraction"]for x in ss]):.3f}'+'|'+f'{sum(x["already_explained_before_joint_area_mm2"]for x in nn):.4f}'+'|\n'
    body+='\n例如G06旧点中心支持消失约11.78个百分点，而完整原面支持损失约0.41个百分点：小的刚体位移会改变离散点落入哪些像素。两者均保留，不以三角面数值覆盖原指标。另有G06约1.835mm²接纳面在联合调整前已被解释，说明一部分“新增”来自位置改变后的投影空缺，不能算新观察方向的信息增量。新增来源、旧面移动及独有支持已分开统计。\n\n工程实现得到更多有来源的连续原面，但物理精度、真实唯一新增面积与整体优于历史方法尚未认证。旧S0的面ID没有被删掉，然而几何位置和投影支持确实改变，不能把ID保留说成几何无损。逐帧三方法完全相同支持集的RGB比较另见[identical_common_support_RGB.csv](metrics/identical_common_support_RGB.csv)；光照和反光也会影响颜色差异。\n\n'
    for n,sid in [(4,'G06_004'),(5,'G07_004'),(6,'G08_005')]:body+='!['+sid+'逐轮生长](figures/Fig'+str(n)+'_'+sid+'_incremental_growth.png)\n\n'
    body+='![局部联合调整前后](figures/Fig7_local_joint_before_after.png)\n\n所有逐轮单张图和优化前后GLB保留本地，见[HTML图库](visualizations/index.html)。四种人工审查状态为ACCEPTED（仅工程）、CANDIDATE（未连接/条件不足但保留）、CONFLICT（几何不一致）、REJECTED（本次不进入展示，非永久删除）。G01正在同一冻结框架下实际实验，不用上述正面结果代替复杂Ip验证。\n'
    update('P2/P3/P4 — 优先三组的连续生长和联合调整',body);index()
if __name__=='__main__':p0()if len(sys.argv)>1 and sys.argv[1]=='P0'else p2()if len(sys.argv)>1 and sys.argv[1]=='P2'else index()
