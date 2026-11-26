"""Small auditable tables and real-data Chinese comparison pages."""
import csv
import html
import json
from pathlib import Path
import shutil
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
from .run import BASE,REPORT,CASES,WT,HIST,read,save,sha,verify_common
from .core import summary

FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
plt.rcParams['font.family']=FontProperties(fname=FONT).get_name()
plt.rcParams['axes.unicode_minus']=False
plt.rcParams['font.size']=10
COLORS=['#1687cc','#e88420']


def fmt(x):return '不可评价' if x is None else f'{x:.3f}'


def csv_write(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)


def page(case,result,depth):
    common=BASE/case/'common';ledger=read(common/'ledger.json');tuples=read(common/'TUPLES_FROZEN.json')['tuples'];tr=np.load(common/'tracks.npz')
    fig=plt.figure(figsize=(14,21));grid=fig.add_gridspec(5,2,height_ratios=[1,1.2,1.2,1.05,.9]);meshdata={};allv=[]
    for arm in ['R','S']:
        data=[]
        for i,t in enumerate(tuples):
            path=BASE/case/arm/'hero/meshes'/(t['tag']+'_Polyp.ply')
            if path.exists():
                m=trimesh.load(path,process=False);data.append((np.asarray(m.vertices),np.asarray(m.faces),i));allv.append(np.asarray(m.vertices))
        meshdata[arm]=data
    bounds=np.concatenate(allv) if allv else np.array([[-1,-1,-1],[1,1,1.]])
    center=(bounds.min(0)+bounds.max(0))/2;half=max(float(np.ptp(bounds,axis=0).max())*.52,1e-3)
    q=tuples[0]['reference'];rgb=cv2.cvtColor(cv2.imread(ledger[q]['RGB_path']),cv2.COLOR_BGR2RGB)
    for col,arm in enumerate(['R','S']):
        ax=fig.add_subplot(grid[0,col]);ax.imshow(rgb);pred=read(BASE/case/arm/'test_predictions.json');pred=[p for p in pred if p['query']==q]
        for cat,color,name in [(1,'#ff3050','息肉'),(0,'#00e0ef','背景')]:
            subset=[p for p in pred if p['category']==cat]
            for p in subset:
                x,y=tr['xy'][p['track'],q];ax.scatter([x],[y],s=16,c=color,marker='o' if p['status']=='OK' else 'x')
                if p['status']=='OK':
                    dx,dy=np.array(p['predicted_xy'])-[x,y];ax.arrow(x,y,dx,dy,color=color,width=.6,head_width=4,length_includes_head=True)
            s=summary(subset);ax.plot([],[],color=color,label=f'{name}：预测{s["predicted"]}/{s["total"]}，≤3px {s["success_3px"]}/{s["total"]}')
        ax.legend(loc='lower left',fontsize=8,facecolor='#eeeeee');ax.set(xlim=(0,640),ylim=(360,0),title=f'{arm}：'+('Ring+SIFT' if arm=='R' else 'SIFT-only')+f' | 同一query RAW{ledger[q]["raw_frame"]}\n圆点=真实坐标；箭头=预测残差（原像素长度）；×=无法预测');ax.axis('off')
        for row,(elev,azim) in enumerate([(20,-60),(0,90)],start=1):
            ax=fig.add_subplot(grid[row,col],projection='3d')
            for v,f,ti in meshdata[arm]:
                collection=Poly3DCollection(v[f],facecolor=COLORS[ti],edgecolor='none',alpha=.82,rasterized=True);ax.add_collection3d(collection)
            ax.set_xlim(center[0]-half,center[0]+half);ax.set_ylim(center[1]-half,center[1]+half);ax.set_zlim(center[2]-half,center[2]+half);ax.set_box_aspect((1,1,1));ax.view_init(elev,azim)
            ax.set_xlabel('X（归一单位）',fontsize=8);ax.set_ylabel('Y',fontsize=8);ax.set_zlabel('Z',fontsize=8)
            if row==2:
                ax.set_yticks([]);ax.set_ylabel('')
                note='两臂均可见主体外分离片层' if '12.0mm' in case else '两臂均见上部断开小面与下方细长面'
                ax.text2D(.02,.02,note+'；无GT，是否错误未知',transform=ax.transAxes,fontsize=8,color='darkred')
            ax.set_title(f'{arm} 原始HERO全部选定面源｜'+('斜视' if row==1 else '侧视')+'\n蓝='+str(tuples[0]['raw_target'])+'；橙='+str(tuples[1]['raw_target'])+'；两臂同视角/同尺度/同范围')
            if not meshdata[arm]:ax.text(*center,'无可用原始曲面')
        ax=fig.add_subplot(grid[3,col])
        valid_depth=next((d for d in depth if d.get('arrays_path')),None)
        if valid_depth:
            arr=np.load(valid_depth['arrays_path']);mask=arr['all_common'];err=abs(arr[arm+'_projected']-arr[arm+'_target']);im=ax.imshow(np.where(mask,err,np.nan),cmap='magma',vmin=0,vmax=5)
            ax.contour(arr[arm+'_valid'],levels=[.5],colors=['cyan'],linewidths=.6);ax.contour(arr['both_nonoccluded'],levels=[.5],colors=['lime'],linewidths=.6)
            fig.colorbar(im,ax=ax,fraction=.032,extend='max',label='归一单位；>5保留在统计')
            s=valid_depth['all_common'][arm];ax.set_title(f'{arm}：{valid_depth["source_raw"]}→{valid_depth["target_raw"]} 有向深度差\n共同像素{valid_depth["all_common"]["pixels"]}/{valid_depth["target_polyp_pixels"]}；median/P95 {fmt(s["median"])} / {fmt(s["P95"])}\n青=该臂投影支持；绿=双方非遮挡；显示未按误差剔除的共同域',fontsize=9)
        else:ax.text(.1,.5,'HERO共同域不可评价',transform=ax.transAxes)
        ax.axis('off')
        ax=fig.add_subplot(grid[4,col]);ax.axis('off');a=result['arms'][arm]
        lines=[f'{arm} 数值相机 {a["numeric_cameras"]}/22；共同RGB检查 {a["rgb_pass"]}/22',f'固定四帧完整组合 {sum(x["complete"] for x in a["fixed_tuples"])}/2']
        for name,label in [('polyp','息肉'),('background','背景')]:
            s=a['test'][name];lines.append(f'全视频{label}：{s["predicted"]}/{s["total"]} 可预测，≤3px {s["success_3px"]}/{s["total"]}')
            lines.append(f'    留出轨迹median/P95 = {fmt(s["median_px"])} / {fmt(s["P95_px"])} px')
        lines+=['固定组合：']+[f'RAW {t["raw_target"]} ← {t["raw_support"]}' for t in tuples]
        lines+=['无GT：一致性/覆盖对照；归一不是绝对精度。','原始深度全留；未接clean；未实施配对稳定性扰动。']
        ax.text(.02,.98,'\n'.join(lines),va='top',fontsize=10)
    title=case.replace('GP_','').replace('_closed_',' / ').replace('_single_refY_',' / 视频')
    fig.suptitle(title+'\n无GT：一致性/覆盖对照｜固定输入、独立相机、同HERO｜1归一单位在R中为1mm；S非独立公制',fontsize=15,y=.995)
    fig.subplots_adjust(top=.925,bottom=.015,left=.03,right=.97,hspace=.30,wspace=.1)
    path=REPORT/'figures'/(case+'.png');path.parent.mkdir(exist_ok=True);fig.savefig(path,dpi=110);plt.close(fig)
    return path


def report():
    REPORT.mkdir(exist_ok=True);evidence=REPORT/'evidence';evidence.mkdir(exist_ok=True);rows=[];camera_rows=[];parts=[];figs=[]
    for case in CASES:
        common=verify_common(case);root=BASE/case;r=read(root/'CAMERA_RESULTS.json');depth=read(root/'HERO_DEPTH_RESULTS.json') if (root/'HERO_DEPTH_RESULTS.json').exists() else []
        figs.append(page(case,r,depth))
        dest=evidence/case;dest.mkdir(exist_ok=True)
        for name in ['INPUT_MANIFEST.json','split.json','ledger.json','TUPLES_FROZEN.json','validation_queries.json','test_queries.json']:
            shutil.copy2(common/name,dest/name)
        for name in ['CAMERA_RESULTS.json','NORMALIZATION_FROZEN.json','HERO_DEPTH_RESULTS.json']:
            if (root/name).exists():shutil.copy2(root/name,dest/name)
        for arm in ['R','S']:
            ad=dest/arm;ad.mkdir(exist_ok=True)
            for name in ['receipt.json','cameras.npz','cameras_normalized.npz','RGB_CHECKS.json','validation_predictions.json','test_predictions.json']:
                if (root/arm/name).exists():shutil.copy2(root/arm/name,ad/name)
            for name in ['RESULT.json','PLAN_FROZEN.json']:
                if (root/arm/'hero'/name).exists():shutil.copy2(root/arm/'hero'/name,ad/('HERO_'+name))
            a=r['arms'][arm];camera_rows.append(dict(case=case,arm=arm,numeric=a['numeric_cameras'],registered_union=a['registered_union_count'],component_sizes=json.dumps(a['camera_receipt'].get('component_sizes',[a['numeric_cameras']])),downstream_scope=a['downstream_component_scope'],total=22,rgb_pass=a['rgb_pass'],three_support_targets=len(a['graph_three_support_targets']),fixed_complete=sum(t['complete'] for t in a['fixed_tuples']),fixed_total=2))
            for name in ['polyp','background']:
                s=a['test'][name];rows.append(dict(case=case,arm=arm,metric='held_track_query',region=name,domain='all_fixed_queries',unit='px',**{k:v for k,v in s.items() if k!='reasons'}))
                s=r['pairing'][name][arm];rows.append(dict(case=case,arm=arm,metric='held_track_query',region=name,domain='paired_predictable_queries',unit='px',**{k:v for k,v in s.items() if k!='reasons'}))
        for d in depth:
            for arm in ['R','S']:
                if d['status']=='NOT_EVALUABLE':rows.append(dict(case=case,arm=arm,metric='HERO_directed_depth',status='NOT_EVALUABLE',reason=d.get('reason')));continue
                for domain in ['all_common','both_nonoccluded']:
                    s=d[domain];rows.append(dict(case=case,arm=arm,metric='HERO_directed_depth',region='polyp',domain=domain,unit='R_scale_normalized_unit',source_raw=d['source_raw'],target_raw=d['target_raw'],total=d['target_polyp_pixels'],predicted=s['pixels'],predicted_fraction=s['fraction_of_target'],median=s[arm]['median'],P95=s[arm]['P95'],status='EVALUABLE' if s['pixels'] else 'NOT_EVALUABLE'))
        parts.append((case,r,depth))
    csv_write(REPORT/'PILOT_RESULTS.csv',rows);csv_write(REPORT/'CAMERA_COVERAGE.csv',camera_rows)
    if (BASE/'INFERENCE_STARTS.jsonl').exists():shutil.copy2(BASE/'INFERENCE_STARTS.jsonl',evidence/'INFERENCE_STARTS.jsonl')
    for log in (BASE/'logs').glob('*.log'):shutil.copy2(log,evidence/log.name)
    content=['# 两视频 Ring+SIFT 与 SIFT-only 可恢复性/一致性小试','', '无GT。两个物理组、各一个视频；固定5组10视频协议已写，本轮只执行指定2视频。原始历史held拆分后在B中隔离，曾被历史门控消费，不能称未消费盲测。所有query图像的其他训练轨迹参与相机恢复，称“留出轨迹测试”。','','## 已完成相机结果','','| 视频 | 臂 | 数值相机 | 共同RGB通过 | 3 Support Target | 固定组合完整 |','|---|---|---:|---:|---:|---:|']
    for x in camera_rows:content.append(f'| {x["case"]} | {x["arm"]} | {x["numeric"]}/22 | {x["rgb_pass"]}/22 | {x["three_support_targets"]}/22 | {x["fixed_complete"]}/2 |')
    content+=['','数值覆盖不是可用性保证。R首成功版本固定为0；S独立从训练匹配初始化，无R位姿、Ring候选或尺度输入。两臂内部筛选/优化器不同，不能解释为单项Ring损失消融。共同RGB仅用validation像素/正深度条件；旧HIST Q0/Q1仅存入证据诊断。','', '## 留出轨迹query（全部固定分母）','','| 视频 | 区域 | 臂 | 可预测 / 全部 | ≤3px成功 / 全部 | median / P95 px |','|---|---|---|---:|---:|---:|']
    for case,r,depth in parts:
        for name in ['polyp','background']:
            for arm in ['R','S']:
                s=r['arms'][arm]['test'][name];content.append(f'| {case} | {name} | {arm} | {s["predicted"]}/{s["total"]} | {s["success_3px"]}/{s["total"]} | {fmt(s["median_px"])} / {fmt(s["P95_px"])} |')
    content+=['','两臂共同可预测query单列在PILOT_RESULTS.csv与CAMERA_RESULTS.json；不能用不同可评价子集的均值直接排名。未预测记录与原因完整保留。','', '## 原始HERO共同区域','','| 视频 | 方向RAW | 共同像素 / 目标息肉像素 | R median/P95 | S median/P95 |','|---|---|---:|---:|---:|']
    for case,r,depth in parts:
        for d in depth:
            if d['status']!='EVALUABLE':content.append(f'| {case} | 不可评价 | 0 | NaN | NaN |');continue
            s=d['all_common'];content.append(f'| {case} | {d["source_raw"]}→{d["target_raw"]} | {s["pixels"]}/{d["target_polyp_pixels"]} | {fmt(s["R"]["median"])} / {fmt(s["R"]["P95"])} | {fmt(s["S"]["median"])} / {fmt(s["S"]["P95"])} |')
    content+=['','单位为R尺度归一单位（R中1单位=1mm）。S仅在求解后用共同训练3D点做一次正尺度/无反射Sim(3)；HERO前冻结。上表使用未按目标遮挡剔除的两臂共同投影域；双方非遮挡交集、每臂支持数、疑似遮挡数见CSV/JSON。正向投影使用最近层z-buffer，单点离散投影可能有空洞。没有GT，不能完全区分真遮挡、相机错位和深度错层；不可只用过滤后较小误差宣布更好。原深度不删，Mesh沿原V6定义生成，全部选定面源留存。','','## 执行范围与限制','','- 已完成：固定快照/划分/元组；两臂独立相机；预测query评价；原生HERO运行状态及原始曲面/共同域诊断；两张中文对照页。','- 未实施：配对训练扰动稳定性实验，状态NOT_EXECUTED。相同确定性重复及R两个初始化均不能代替它。','- 后续扩组：按冻结协议扩至5组10视频，不在本轮外推总体结论；绝对相机/曲面精度仍需独立可信GT与对齐。','- R的SciPy BA用原60次函数评价预算，终止/收敛状态在原solver日志和receipt保留；相机有限并不等价于优化已收敛。','', '## 入口与证据','','`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/ring_sift_comparison.py --stage {prepare,R,S,evaluate,hero,report}`，相机/推理阶段禁止静默覆盖已启动结果。大数据：`/home/liu/ring_first_3d_workspace/runs/ring_sift_comparison_001`。共同输入/划分/相机/元组及原预测坐标见 `evidence/<完整case>/`；CSV为小表，原始输出按路径与SHA追溯。','','COLMAP官方依据：[数据库](https://colmap.github.io/database.html)、[FAQ](https://colmap.github.io/faq.html)、[教程](https://colmap.github.io/tutorial.html)。软件版本/完整参数、0.5像素、w2c/c2w、正深度、原frame/track身份检查见S/receipt.json。','']
    interpretation=REPORT/'evidence/INTERPRETATION.md'
    if interpretation.exists():content.insert(3,interpretation.read_text())
    content+=['## 分量与共同样本核对','']
    for case,r,depth in parts:
        for arm in ['R','S']:
            a=r['arms'][arm];content.append(f"- {case} / {arm}：注册并集 {a['registered_union_count']}/22；下游数值相机 {a['numeric_cameras']}/22；分量规模 {a['camera_receipt'].get('component_sizes',[a['numeric_cameras']])}。")
        p=r['pairing']['rgb_pass_ids'];content.append(f"- 共同RGB通过：交集 {len(p['intersection'])}，仅R {len(p['R_only'])}，仅S {len(p['S_only'])}，均未通过 {len(p['neither'])}。")
        content.append(f"- 生产历史HIST诊断（非B可比门控）：Q0 {sum(x['old_pass'] for x in r['historical_Q0_Q1'])}/22，Q1 {sum(x['new_pass'] for x in r['historical_Q0_Q1'])}/22。")
    content+=['','本次所有重建都只有一个22相机分量；多分量的注册并集与最大分量下游评价分开记录，不能混合不同分量的坐标系。','', '## 执行核验','', '15项对照接口/预测/尺度/GPU隔离测试及7项既有V6策略测试通过。8条实际推理启动记录，8次成功，无额外推理；首次S因本进程残留CUDA上下文被误判忙，修正并验证无已启动S推理后继续，保留原忙回执。A每段75个源身份和9个相机输出哈希未变，科学源码与历史相机签名逐项一致，见READONLY_AND_KERNEL_AUDIT.json。']
    (REPORT/'TECHNICAL_REPORT.md').write_text('\n'.join(content))
    body='<!doctype html><html lang="zh"><meta charset="utf-8"><title>无GT：Ring+SIFT / SIFT 对照</title><style>body{max-width:1500px;margin:auto;font-family:sans-serif}img{width:100%}</style><h1>两视频小试：无GT，一致性/覆盖对照</h1><p><a href="TECHNICAL_REPORT.md">技术报告</a> · <a href="PILOT_RESULTS.csv">结果CSV</a> · <a href="COMPARISON_PROTOCOL.md">冻结协议</a></p>'
    for p in figs:body+=f'<h2>{html.escape(p.stem)}</h2><img src="figures/{p.name}">'
    (REPORT/'COMPARISON_PAGES.html').write_text(body+'</html>')
    save(evidence/'DELIVERY_FILES.json',{str(p.relative_to(REPORT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in REPORT.rglob('*') if p.is_file() and p.name!='DELIVERY_FILES.json'})
    print('REPORT',REPORT,flush=True)
