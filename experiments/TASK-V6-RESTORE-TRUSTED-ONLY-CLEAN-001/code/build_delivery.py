"""Build a compact Chinese delivery from frozen classification outputs."""
from pathlib import Path
import html
import re
import json
import shutil
from ring_first_3d.v6_raw.trusted_restore import T, O, W, read, save, sha, table, now

sources = read(T/'config/SOURCES_FROZEN.json')
results = read(T/'evidence/RESULTS.json')
p = read(T/'evidence/PROGRESS_FINAL.json')
rows = []
for i, (c, r) in enumerate(zip(sources['cases'], results), 1):
    R = Path(c['run'])
    rows.append(dict(source=i,group=c['group'],video=c['video'],target_RAW=c['raw_target'],support_RAW=json.dumps(c['raw_support']),origin='NEW',role=c['role'],selection_reason=c['selection_reason'],raw_video=c['raw_path'],raw_video_sha256=c['raw_video_sha256'],mesh=str(R/'meshes'/(c['tag']+'_Polyp.ply')),mesh_sha256=c['mesh_sha256'],native_depth=str(R/'raw'/(c['tag']+'.npz')),native_sha256=c['native_sha256'],camera=c['camera_path'],camera_sha256=c['artifacts'][c['camera_path']],CAD=c['cad_path'],CAD_sha256=c['artifacts'][c['cad_path']],model_sha256=c['model_sha256'],tuple_input_sha256=c['input_sha256'],HERO_execution_commit=c['hero_execution_commit'],clean_execution_commit=r['execution_commit'],clean_source_sha256=r['source_code_sha256'],adapter_sha256=r['input_adapter_sha256'],output=str(O/f'source{i}'),figure=f'figures/source{i}.png',all_artifact_identities='config/SOURCES_FROZEN.json'))
table(T/'SOURCE_MANIFEST.csv', rows)
metrics = []
for r in results:
    metrics += [dict(case=r['case'],subset='RAW',faces=r['raw']['faces'],area_mm2=r['raw']['area_mm2'],face_edge_components=r['raw']['face_edge_components'])]
    metrics += [dict(case=r['case'],subset=s['label'],faces=s['faces'],area_mm2=s['area_mm2'],face_edge_components=r['trusted']['face_edge_components'] if s['code']==0 else '') for s in r['states']]
    q=r['trusted_plus_uncertain_diagnostic'];metrics += [dict(case=r['case'],subset='0+1_DIAGNOSTIC_ONLY',faces=q['faces'],area_mm2=q['area_mm2'],face_edge_components='')]
table(T/'SURFACE_COUNTS.csv',metrics)
artifacts=[]
for path in sorted(O.glob('source*/*')):
    if path.is_file():artifacts.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path)))
table(T/'LOCAL_ARTIFACTS.csv',artifacts)
shutil.copyfile(O/'run.log',T/'evidence/CLASSIFICATION.log')
shutil.copyfile(O/'render.log',T/'evidence/RENDER.log')
space=shutil.disk_usage(W);local_bytes=sum(x['bytes'] for x in artifacts)
save(T/'evidence/SPACE.json',dict(checked_beijing=now(),filesystem_total_bytes=space.total,filesystem_used_bytes=space.used,filesystem_free_bytes=space.free,new_classification_artifact_bytes=local_bytes,original_large_assets_copied=False,concurrent_full_job=True))

names=['Ip12 / R5 / 004 / RAW301','Ip10.3 / R5 / 005 / RAW579','IIa22 / R10 / 005 / RAW640','Ip4 / R10 / 004 / RAW68']
observations=[
 '远处下方细条／小片在四态图中主要为灰色 UNKNOWN，少量黄色 UNCERTAIN；这些离散原分量在可信图中消失。原先最大的主面经筛选分成两个较大可信片（91.015、11.372 mm²），Ring附近原分量仍保留13.722 mm²，不能将分裂或孤片全部称为修复。图中下方仍有主面分离出的可信片。外缘及细窄连接也被削减，是否含真实结构须人工判断。',
 '远处右下细碎片均为 UNKNOWN，导出后消失；但图中近主体下方的独立片含811个 TRUSTED 原面、3.565 mm²，仍然保留。这个原分量总面积6.341 mm²，另有0.862 mm² UNCERTAIN和1.914 mm² UNKNOWN被排除。因此“远端小片减少”可直接观察，“孤立片已清干净”不成立。原主面和Ring附近分量也有边缘缩减及少量分裂。',
 '宽主面大部分为 TRUSTED；右缘较大的黄色 UNCERTAIN 区和灰色 UNKNOWN 区被排除，可信图出现明显缺口，少量细碎可信面仍在。共享边分量从3增至8，最大的两个为147.860和53.709 mm²，说明删面也增加了碎裂。左侧正常观感边缘同样退缩；缺口是否去掉伪面、是否误伤真实薄结构，当前没有真值可判定。',
 '较正常对照仍为一个面连通分量，主体形态保留；边缘黄色／灰色带仍被排除，总面积从16.700降至13.769 mm²（减少17.55%）。它说明“正常观感来源也会损失边界”，不能以画面更整齐或仍单连通证明没有误删。图中CAD遮挡面不能据这两个视角判真伪。'
]
counts_header='| 来源 | Raw 面数 / mm² | TRUSTED 面数 / mm² | UNCERTAIN 面数 / 排除mm² | UNKNOWN 面数 / 排除mm² | REJECTED 面数 / mm² | 面连通分量 Raw→可信 |\n|---|---:|---:|---:|---:|---:|---:|'
lines=[counts_header]
for name,r in zip(names,results):
    s=r['states'];fmt=lambda q:f"{q['faces']} / {q['area_mm2']:.3f}"
    lines.append(f"| {name} | {fmt(r['raw'])} | {fmt(s[0])} | {fmt(s[1])} | {fmt(s[3])} | {fmt(s[2])} | {r['raw']['face_edge_components']}→{r['trusted']['face_edge_components']} |")
count_table='\n'.join(lines)
active='；'.join(x['case']+' / '+x['current_stage'] for x in p['active']) or '快照时无活动阶段'
failures='\n'.join('- '+x['case']+'：两个初始化候选均报 `Ring pose graph disconnected; no free SfM fallback`，随后无可用相机。' for x in p['failures'])
progress=f"检查时间 **{p['checked_beijing']}（北京时间）**。实际注册分母 **39组、79视频**（38组各2视频，Ip4/R5为3视频）。全量仍运行，以下均为阶段值：正常结束且有输出 **{p['normal_completed_with_output']}**，正常结束无输出 **{p['normal_completed_without_output']}**，失败 **{p['failed']}**，运行中 **{p['running']}**，待运行 **{p['pending']}**，其他 **{p['other']}**。已正常结束 {p['normal_completed_with_output']+p['normal_completed_without_output']}/79，含失败的已终结 {p['normal_completed_with_output']+p['normal_completed_without_output']+p['failed']}/79。\n\n非空HERO输出 **{p['videos_with_nonempty_hero']}视频、{p['groups_with_nonempty_hero']}组、{p['single_source_surfaces']}个单来源曲面**；阶段视频输出覆盖率 **{p['videos_with_nonempty_hero']}/79={p['phase_video_output_coverage']:.2%}**，组覆盖率 **{p['groups_with_nonempty_hero']}/39={p['phase_group_output_coverage']:.2%}**。输出统计同时包含全量任务依法复用和新推理的来源；本轮4例全部为NEW。任务完成数、面源数、输出覆盖和几何正确性是不同量，以上不表示几何合格率。\n\n当前阶段：`{active}`。最近日志更新时间 `{p['latest_log']['modified_beijing']}`，最近已检查产物更新时间 `{p['latest_artifact']['modified_beijing']}`；具体路径及日志尾部见 [进度JSON](evidence/PROGRESS_FINAL.json)，逐视频状态见 [VIDEOS_FINAL.csv](evidence/VIDEOS_FINAL.csv)。快照为只读扫描，时间边界内队列可能推进，不是对运行器加锁的事务。"
note='共享整条边的三角面连通分量用于上表；仅接触一个顶点的不合并。JSON另保留共享顶点的components诊断，不能与此混用。未引用孤立顶点不计曲面分量。面积单位mm²；无GT，不报告清理正确率或误删率。'
report=f"""# TASK-V6-RESTORE-TRUSTED-ONLY-CLEAN-001 技术报告

已在4份当前全量新推理面源上恢复017分类＋冻结gap＋018 `state==0`导出，并完成4张中文单来源图。历史方法已正确复用；本轮4源REJECTED与确认gap边均为0，可见变化来自排除UNKNOWN/UNCERTAIN。没有将方法自动应用到全量输出。

本地可视化：**http://127.0.0.1:8959/index.html**。全量原图集仍为 http://127.0.0.1:8957/index.html 。[方法表](METHOD.md) · [本轮索引](index.html) · [逐源身份](SOURCE_MANIFEST.csv) · [完整冻结身份](config/SOURCES_FROZEN.json) · [本地大资产位置与SHA](LOCAL_ARTIFACTS.csv)。

## 实际全量进度

{progress}

具体失败：

{failures}

以上失败保留在79视频分母；本轮未修改、切换或重启全量。运行器PID `{p['runner_pid']}`，全量执行快照 `da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`。

## 新来源与实际统计

样本冻结于 **{sources['frozen_beijing']}**，在本轮分类之前。4个不同组／视频，R5与R10各2例；依据既有Raw图和原拓扑选择，非依据分类结果。每源均核验NEW状态、实际INFERENCE_STARTS、HERO_COMPLETE、原深度与PLY哈希；原相机、真实Target/3Support、RGB/Mask/CAD及模型哈希均保存在冻结清单，没有读取旧三例标签。

{count_table}

{note}

四态总数／面积严格覆盖Raw。所有原始边界邻接面均因历史边界警告或未知而排除，4源对应面积分别 **19.681、16.037、18.123、2.331 mm²**；这是规则行为，不是已证实错误面积。

诊断 `state in {{0,1}}` 的面数／面积分别为 {', '.join(str(r['trusted_plus_uncertain_diagnostic']['faces'])+' / '+format(r['trusted_plus_uncertain_diagnostic']['area_mm2'],'.3f')+'mm²' for r in results)}，仅用于区分待定面的影响，不称为018规则。完整主分量面积、每个原分量四态及位置代理统计见 [RESULTS.json](evidence/RESULTS.json)。

## 逐源图与判断

"""
for i,(name,c,obs,r) in enumerate(zip(names,sources['cases'],observations,results),1):
    report+=f"### {name}\n\n[中文三列图](figures/source{i}.png)，Support RAW `{c['raw_support']}`。选样理由：{c['selection_reason']}。\n\n{obs}\n\n主要可信面连通分量面积：{', '.join(format(v,'.3f') for v in r['trusted']['largest_component_areas_mm2'])} mm²。\n\n"
report+=f"""## 验证与运行身份

分类执行提交 **{results[0]['execution_commit']}**；分类及输入适配源码SHA逐源保存在RESULTS。历史规则来自 `62c286fcbf39cbba9ec5adb148bd50ba9dc94093`。展示阶段仅修正source2箭头，使其指向下方原始独立片；没有重跑分类或改变标签，绘图身份见 [RENDER_RECEIPT](evidence/RENDER_RECEIPT.json)。

[验证脚本](code/verify_delivery.py)和[实际回执](evidence/VERIFICATION.json)核验76项冻结资产、历史7函数AST与参数、Target/Support、相机／原生内参、完整原V/F/颜色、原Face/Vertex ID、互补排除集、面数／面积、4图SHA全部通过。相关单元检查20项通过。另一次只读审查未发现阻断或重要问题，明确采用面共享边连通定义。四图固定原Raw+CAD范围，最多两个相同视角，尺度未独立缩放；异常与潜在边界损伤均展示。

运行：4源顺序处理，OMP/BLAS线程1，nice=10；既有渲染器内部射线线程2，无GPU清理任务。分类日志见 [CLASSIFICATION.log](evidence/CLASSIFICATION.log)。独立输出 `{O}`，本轮分类资产合计 **{local_bytes/1024**2:.2f} MiB**；原Raw、模型和大网格未重复打包进Git。空间检查可用 **{space.free/1024**3:.2f} GiB**，全量并行运行会继续改变余量；[SPACE.json](evidence/SPACE.json)给出字节与检查时刻。

只读输入的原面建面过滤不计本轮收益。没有GT或深度MAE门控，没有C1、OBS_TRUSTED额外过滤或Body优化。UNKNOWN不代表错误；删面比例不能作精度提升。后续应由研究者审阅残留与结构损失，本轮停在4例恢复与展示，不推广全量。
"""
(T/'TECHNICAL_REPORT.md').write_text(report)
parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>历史TRUSTED-only：四个新来源</title><style>body{max-width:1500px;margin:2em auto;padding:0 20px;font-family:system-ui;color:#172a3b;background:#f2f5f7}section{background:white;padding:20px;margin:24px 0}img{width:100%;height:auto}table{border-collapse:collapse}td,th{border:1px solid #bdcad4;padding:8px}a{color:#145b9d}p{line-height:1.7}.scroll{overflow:auto}</style><h1>历史 TRUSTED-only：4个本轮新来源</h1><p><b>仅保留 TRUSTED；UNKNOWN、UNCERTAIN、REJECTED 同时排除。</b> 四例REJECTED=0、确认gap边=0；删面来自未知与待定，不能视作已证实错误被移除。</p><p><a href="TECHNICAL_REPORT.md">中文技术报告</a> · <a href="METHOD.md">历史方法表</a> · <a href="SOURCE_MANIFEST.csv">来源清单</a> · <a href="SURFACE_COUNTS.csv">面数/面积</a> · <a href="evidence/VERIFICATION.json">验证回执</a> · <a href="LOCAL_ARTIFACTS.csv">本地资产路径与哈希</a></p>']
progress_html=html.escape(progress).replace('\n\n','</p><p>').replace('**','')
progress_html=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',progress_html)
progress_html=re.sub(r'`([^`]+)`',r'<code>\1</code>',progress_html)
parts+=['<section><h2>全量任务阶段快照</h2><p>'+progress_html+'</p><p>此页为本轮交付快照，不自动刷新；<a href="http://127.0.0.1:8957/index.html">全量图集</a>独立更新。</p></section>']
parts+=['<div class="scroll"><table><tr><th>来源</th><th>Raw 面/mm²</th><th>可信 面/mm²</th><th>待定 面/mm²</th><th>未知 面/mm²</th><th>拒绝 面/mm²</th><th>面分量 Raw→可信</th></tr>']
for name,r in zip(names,results):
    entries=[r['raw'],r['states'][0],r['states'][1],r['states'][3],r['states'][2]]
    parts+=['<tr><td>'+name+'</td>'+''.join(f"<td>{q['faces']} / {q['area_mm2']:.3f}</td>" for q in entries)+f"<td>{r['raw']['face_edge_components']}→{r['trusted']['face_edge_components']}</td></tr>"]
parts+=['</table></div><p>'+note+'</p>']
for i,(name,c,obs) in enumerate(zip(names,sources['cases'],observations),1):
    parts+=[f'<section id="source{i}"><h2>{name}</h2><p>Support RAW {c["raw_support"]}；{html.escape(c["selection_reason"])}</p><a href="figures/source{i}.png"><img loading="lazy" alt="{name}：原始、四态、可信子集固定范围对照" src="figures/source{i}.png"></a><p>{obs}</p><p>数值产物：<code>{O}/source{i}/</code>；原始大资产见来源清单，不在Git重复复制。</p></section>']
parts+=['<p>四个来源均为当前全量任务NEW推理，实际原面与坐标完整保存。没有GT正确率、没有自动推广全量。</p></html>']
(T/'index.html').write_text('\n'.join(parts))
# CSV fields are unchanged; normalize record newlines for repository checks.
for csv_path in T.rglob('*.csv'):
    csv_path.write_bytes(csv_path.read_bytes().replace(b'\r\n', b'\n'))
print('BUILT: report, index, source/count/artifact manifests; 4 figures referenced')
