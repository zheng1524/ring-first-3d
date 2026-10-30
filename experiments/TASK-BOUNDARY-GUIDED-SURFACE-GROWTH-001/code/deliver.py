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
        rel=str(p.relative_to(R));md+='- ['+p.stem+']('+rel+')\n';h+='<li><a href="../'+rel+'">'+escape(p.stem)+'</a></li>'
    for p in sorted((R/'local_results/glb').glob('*.glb'))if(R/'local_results/glb').exists()else[]:
        rel=str(p.relative_to(R));md+='- 本地GLB：`'+str(p)+'`\n';h+='<li><a href="../'+quote(rel)+'">'+escape(p.name)+'</a>（仅本地）</li>'
    h+='</ul><script>function filter(k){document.querySelectorAll("article").forEach(x=>x.hidden=k!=="ALL"&&!x.dataset.name.includes(k))}</script></html>'; (R/'visualizations/index.html').write_text(h);(R/'RESULT_INDEX.md').write_text(md)
def p0():
    seeds=load(R/'metrics/engineering_seeds.json');scores=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'];body='4物理组/5视频/14既有参考均核验来源。基于用户最新补充，本轮允许局部联合刚体调整已有及新增曲面；旧版本只读保留，不以保护旧结果不变代替几何接纳。\n\n主体按相机质量×(0.55最大连续可靠法向/非留出Mask支持面积＋0.20连续面积比例＋0.15邻帧支持＋0.10法向可靠比例)选择，绝非只按总面积。选中：'+str(scores)+'。分母和逐参考评分见main_surface_scores.csv。\n\nG06/G07/G08工程种子恢复：\n\n|组|Cleaned F1整源点|F2点|F2完整原面|完整原面mm²|原面分量|\n|---|---|---|---|---|---|\n'
    for s in seeds:body+='|'+s['group']+'|'+str(s['Cleaned_F1_source_points'])+'|'+str(s['F2_accepted_points'])+'|'+str(s['F2_complete_original_faces'])+'|'+f'{s["F2_complete_original_face_area_mm2"]:.6f}'+'|'+str(s['face_components'])+'|\n'
    body+='\nENGINEERING_ACCEPTED_SEED表示人工认可局部展示，不是几何GT。没有把整片F1蓝面提升为可信。原始点索引/接受mask/完整面索引与SHA已冻结；新派生位置可在本轮授权下调整。主体全部Cleaned原面保留，最大主分量参与外边界生长，其他原小分量单列保护，不自动作为外部生长边界。源/几何原始版本不改。\n\n边界由只使用一次的原面边提取，按真实Mask/Ring、原网格与Cleaned拓扑区分外部观测终止、Ring遮挡、原深度断裂、清理内孔和选面切口/未知。Ring边界只有另一真实观察能够支持时才可尝试；不是形态先验补面。\n\n本轮重新先行冻结非参考图像评价帧，核查历史HERO源帧身份。G06/G07/G08旧HERO源列表未完整记录，故评价标记历史来源不完全可审计，不虚称全流程盲测。评价帧不参与本轮新的推理/选源/生长。没有GT/Oracle。\n\n![认可新增区域核对](figures/Fig1_engineering_seed_recovery.png)\n\n![G01边界](figures/Fig2_G01_initial_frontiers.png)\n\n![基线与初始场景](figures/Fig3_F1_F2_selected_initial.png)\n'
    update('P0/P1 — 来源、工程种子和实际边界',body);index()
if __name__=='__main__':p0()if len(sys.argv)>1 and sys.argv[1]=='P0'else index()
