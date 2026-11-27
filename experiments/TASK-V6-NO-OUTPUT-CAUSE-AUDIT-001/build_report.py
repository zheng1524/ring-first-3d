"""Render the audit's existing evidence as a local Chinese report."""
from pathlib import Path
import csv, html, json, shutil
from markdown_it import MarkdownIt
T=Path(__file__).resolve().parent
B=Path('/home/liu/ring_first_3d_workspace/runs/v6_full_run_001')
rows=list(csv.DictReader((T/'VIDEO_CAUSES.csv').open()))
alternatives=[dict(case=r['case'],primary_version=r['primary_version'],primary_Q1_cameras=r['q1_cameras'],other_saved_version_Q1_cameras=r['alternative_max_admitted'],not_recovered=True) for r in rows if r['status']=='DONE' and r['renderable']=='0' and int(r['alternative_max_admitted'])>=3]
assert len(alternatives)==10
with (T/'ALTERNATIVE_INITIALIZATIONS.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,list(alternatives[0]),lineterminator='\n');w.writeheader();w.writerows(alternatives)
labels=dict(NO_ADMITTED_CAMERAS='相机均未准入',FEWER_THAN_THREE_ADMITTED_CAMERAS='准入相机不足3张',INSUFFICIENT_SHARED_TRACK_SUPPORT='共同轨迹Support不足',GRAPH_DISCONNECTED='位姿图断连',EMPTY_RING_VALIDATION_TYPEERROR='Ring空观测＋验证异常')
def table(headers, entries):
    return '<table><thead><tr>'+''.join('<th>'+html.escape(str(h))+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in entries)+'</tbody></table>'
negative=[r for r in rows if r['renderable']=='0'];assert len(negative)==37
details=table(['视频（原注册身份）','直接阻断原因','Q1相机','最大Support数','另一已存版本Q1相机','硬门槛失败帧数（可重叠）'],[[r['case'],labels[r['cause']],r['q1_cameras'] or '未进入准入',r.get('max_supports','') or '未调度',r.get('alternative_max_admitted','') or '未生成验证表',r.get('gate_counts','') or r.get('graph_components','') or '22帧Ring轮廓为空'] for r in negative])
body=MarkdownIt('commonmark',{'html':False}).enable('table').render((T/'TECHNICAL_REPORT.md').read_text())
image='/prepared/GP_Is_18.0mm_closed_R5_single_refY_005/raw_000000.png'
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V6 无输出与失败原因审计</title><style>body{font-family:system-ui,sans-serif;max-width:1280px;margin:30px auto;padding:0 22px;color:#182335;line-height:1.7}table{border-collapse:collapse;width:100%;font-size:14px;display:block;overflow-x:auto;margin:18px 0}th,td{border:1px solid #ccd3dd;padding:9px;vertical-align:top}th{background:#edf2f8}code{background:#edf2f8;padding:2px 4px;overflow-wrap:anywhere}a{color:#174da0}h2{margin-top:38px}img{max-width:100%}nav{padding:15px;background:#edf2f8}td{overflow-wrap:anywhere}figure{margin:20px 0}figcaption{font-size:14px}</style>'''
page+='<nav><a href="/index.html">全量图集</a> · <a href="TECHNICAL_REPORT.md">报告原文</a> · <a href="GROUP_CAUSES.csv">39组表</a> · <a href="VIDEO_CAUSES.csv">79视频表</a> · <a href="FRAME_GATES.csv">逐帧指标</a> · <a href="ALTERNATIVE_INITIALIZATIONS.csv">另一初始化诊断</a> · <a href="evidence/SUMMARY.json">核验摘要</a></nav>'
page+=body+'<h2>原图证据：Is18/R5/005，RAW第0帧</h2><figure><img src="'+image+'" alt="Is18 R5 005 RAW第0帧原始RGB"><figcaption>原始RGB，640×360像素；R5物理内径为5mm。Ring可见，但当前掩膜规则把全部邻息肉边界列为遮挡顺序不明。未重绘图像、未使用GT，图像不是毫米坐标视图。</figcaption></figure><h2>全部37段零输出视频逐项索引</h2>'+details+'</html>'
(T/'index.html').write_text(page)
dest=B/'failure_audit';dest.mkdir(exist_ok=True)
names=['TECHNICAL_REPORT.md','index.html','VIDEO_CAUSES.csv','GROUP_CAUSES.csv','FRAME_GATES.csv','ALTERNATIVE_INITIALIZATIONS.csv']
for name in names:shutil.copyfile(T/name,dest/name)
(dest/'evidence').mkdir(exist_ok=True)
for p in (T/'evidence').glob('*.json'):shutil.copyfile(p,dest/'evidence'/p.name)
print('REPORT_READY http://127.0.0.1:8957/failure_audit/index.html')
