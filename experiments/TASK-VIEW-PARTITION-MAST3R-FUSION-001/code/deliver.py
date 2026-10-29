"""Incremental one-report publication and local-only asset gallery."""
from common import *
from html import escape
from urllib.parse import quote
def update(stage,body):
    p=R/'TECHNICAL_REPORT.md';text=p.read_text()if p.exists()else '# 视角分区与MASt3R辅助选择性聚合\n\n状态：RUNNING / EXPERIMENTAL。四批次连续授权；GT模式NONE。仅新增派生结果，旧P0/相机/HERO权重/Dxy冻结。物理精度尚未认证。\n\n中文摘要：本轮按真实相机与息肉中心代理方向组织视角块，采用既有绝对密度T2与细小结构保护生成Cleaned，使用官方MASt3R匹配和Ring约束派生配准，再对新方向运行冻结HERO，最后进行方向负责制聚合。相机未筛选场景与照片保持候选身份，成功与失败均保留。报告在各批次以同一文件更新，不将数值输出、展示、融合验收和物理测量混为一谈。\n'
    marker='\n## '+stage+'\n';start=text.find(marker)
    if start>=0:
        end=text.find('\n## ',start+len(marker));text=text[:start]+(text[end:]if end>=0 else'')
    p.write_text((text+marker+'\n'+body).rstrip()+'\n')
def index():
    figs=sorted((R/'figures').rglob('*.png'));md='# 结果索引\n\n[技术报告](TECHNICAL_REPORT.md) · [HTML图库](visualizations/index.html) · [代码复用](CODE_REUSE_AUDIT.md)\n\n本地根目录：`'+str(R)+'`\n\n'
    h='<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>View Partition / MASt3R</title><style>body{font:16px system-ui;max-width:1500px;margin:auto;padding:24px;background:#eee}article{background:white;padding:12px;margin:20px 0}img{width:100%;height:auto}button{margin:6px;padding:8px}nav{position:sticky;top:0;background:white}</style><h1>四组视角分区与选择性聚合</h1><p>真实XYZ；黑色CAD；照片/未验证跨视频关系仅候选；背景DISPLAY_ONLY，无GT。<a href="../TECHNICAL_REPORT.md">报告</a> · <a href="../RESULT_INDEX.md">全部结果</a></p><nav>'
    for tag in ['ALL','G01','G06','G07','G08','P0','P1','P2','P3','P4','P5','P6','P7','P8','P9']:h+='<button onclick="filter(\''+tag+'\')">'+tag+'</button>'
    h+='</nav>'
    for p in figs:
        rel=str(p.relative_to(R));md+='- ['+rel+']('+rel+')\n';href='../'+quote(rel);h+='<article data-name="'+rel+'"><h2>'+escape(rel)+'</h2><a href="'+href+'"><img loading="lazy" src="'+href+'"></a></article>'
    md+='\n## 指标与状态（完整索引）\n\n'
    h+='<section><h2>指标与最终身份</h2><p>工程完成；跨视频 NOT FUSED；真实新增表面/物理精度未认证。G07压力测试、G08有限相机。灰色/深度图皆实际XYZ。</p><ul>'
    for p in sorted((R/'metrics').glob('*.csv')):
        rel=str(p.relative_to(R));md+='- ['+p.stem+']('+rel+')\n';h+='<li><a href="../'+quote(rel)+'">'+escape(p.stem)+'</a></li>'
    h+='</ul></section>'
    md+='\n## 本地完整几何（未公开上传）\n\n';h+='<section><h2>本地可旋转GLB（未上传GitHub）</h2><p>真实点原语，GLB米、精确NPZ毫米；来源ID在metadata中。相应NPZ/PLY同目录。点击下载后可用本地3D查看器旋转。</p><ul>'
    model_index=R/'metrics/GLB_INDEX.json'
    if model_index.exists():
        for item in load(model_index):
            p=Path(item['path']);rel=str(p.relative_to(R));md+='- `'+str(p)+'` — '+item['method']+'\n';h+='<li><a href="../'+quote(rel)+'">'+escape(p.name)+'</a> ('+str(round(item['bytes']/1e6,2))+' MB)</li>'
    h+='</ul></section><p><a href="../REPRODUCE.md">复现说明</a> · <a href="../provenance/OUTPUT_INDEX.json">全部本地资产路径与SHA</a>。figures/local仅本地；GitHub仅精选P0–P9核心PNG。</p>'
    md+='\n## 复现与来源\n\n- [复现说明](REPRODUCE.md)\n- [完整本地资产路径与SHA](provenance/OUTPUT_INDEX.json)\n- [最终源码与来源SHA](provenance/FINAL_CODE_AND_SOURCE_MANIFEST.json)\n- [逐层参数](provenance/LAYER_DISPLAY_PARAMETERS.json)\n- [最终审计](provenance/FINAL_REVIEW.json)\n\nfigures/local和完整几何仅本地可用；公开核心PNG均在P0–P9目录。\n'
    h+='<script>function filter(k){document.querySelectorAll("article").forEach(a=>a.hidden=k!=="ALL"&&!a.dataset.name.includes(k))}</script></html>'; (R/'visualizations/index.html').write_text(h);(R/'RESULT_INDEX.md').write_text(md)
def batch_a_report():
    a=load(R/'metrics/cleaned_input_audit.json');v=load(R/'metrics/view_distribution.json');p=load(R/'metrics/view_partition.json');n=load(R/'metrics/new_reference_plan.json');body='P0–P3已实算：4独立物理组、5视频、9归档P0；62个冻结视频相机候选与3张位姿未知照片；21个方向块。G07为UNQUALIFIED_CAMERA_STRESS。下表方向仅在各视频独立Ring局部坐标内成立，不等同位姿真值；候选坏位姿可能产生虚假的方向跨度。\n\n|组|Raw点|Cleaned点|方向块|新HERO计划|\n|---|---|---|---|---|\n'
    for g in ['G01','G06','G07','G08']:body+='|'+g+'|'+str(sum(x['raw_N']for x in a if x['group']==g))+'|'+str(sum(x['clean_N']for x in a if x['group']==g))+'|'+str(sum(x['group']==g for x in p))+'|'+', '.join(x['reference_view']for x in n if x['group']==g)+'|\n'
    body+='\nG01 T2为004=49.21594809052892、005=58.17189372286792点/mm²。其他组三组统一实验性迁移49.21594809052892，不按组调参。保护可能细柄代理、Ring邻近与原完整小分量；不移动XYZ、不补孔。Cleaned始终实验候选，损伤与孔洞统计完整保留，不采用上轮被拒绝的角度法。\n\n方向用(c−息肉中心代理)/距离；中心由已清理源点上部60%源像素的中位XYZ确定，无GT。Complete-link 10°，邻接18°和冻结参考投影Mask支持≥35%。Core/Transition/Holdout身份已在正式匹配及图像误差评价前冻结；孤立块无独立留出时明确无验证。三照片没有公制位姿，不进入精确方向聚类。\n\n预选5份新参考是与旧P0方向差最大的非留出真实帧，差约10.19°/12.50°/16.54°/18.96°/20.35°；这些方向差依赖冻结候选相机，**不证明新真实表面存在**。G01_005、G06/G08新目标仍含MODEL_PREDICTED相机，Batch B必须检查派生PnP；不把它们升级为已认证位姿。G07全部压力测试，仍实际尝试新增参考。\n\n已核实本地官方MASt3R权重SHA与HERO原权重SHA，GPU6GB，磁盘约6GB余量；模型不复制、不下载、不训练。官方实现与许可依据：[MASt3R](https://github.com/naver/mast3r)、[许可](https://github.com/naver/mast3r/blob/main/LICENSE)；代码/权重只读，匹配点图不充作公制P0。\n\n'
    for path in ['P1_cleaning/G01.png','P2_view_distribution/G06.png','P2_view_distribution/G07_G08.png','P3_view_partition/G01.png']:body+='!['+path+'](figures/'+path+')\n\n'
    body+='每个P0/P1/P2/P3阶段另有3张真实复合图，覆盖四组，见图库。下一批固定使用这些分区和帧身份进行MASt3R全图/ROI及历史对照，不按最终RGB误差选配对。';update('Batch A — Cleaned与方向分区',body);index()
if __name__=='__main__':batch_a_report()if len(sys.argv)>1 and sys.argv[1]=='A'else index()
