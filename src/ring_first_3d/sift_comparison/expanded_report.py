"""Ten-video evidence report; all observations remain descriptive and without GT."""
import csv
import html
import json
from pathlib import Path
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .run import BASE,HIST,REPORT,read,save,sha,verify_common
from .expansion import authorized_cases
from .report import csv_write,fmt,page

E=REPORT/'evidence_expanded'


def short(case):
    return case.replace('GP_','').replace('_closed_','/').replace('_single_refY_','/')


def med(values):
    a=[float(x) for x in values if x is not None and np.isfinite(x)]
    return float(np.median(a)) if a else None


def pose_figure(records):
    fig,axs=plt.subplots(2,2,figsize=(14,9));labels=[short(c) for c,_,_,_ in records];x=np.arange(len(labels))
    settings=[('all_common','position_norm','整段对齐后相机中心差（R尺度单位）'),('all_common','rotation_deg','整段对齐后旋转差（度）'),('roles','position_norm','HERO相对平移向量差（R尺度单位）'),('roles','rotation_deg','HERO相对旋转差（度）')]
    for ax,(subset,metric,title) in zip(axs.flat,settings):
        av=[];pv=[]
        for c,r,p,ring in records:
            if subset=='roles':s=p.get('role_pose_differences',{}).get('summary',{})
            else:s=p.get('summary',{}).get(subset,{})
            av.append(s.get(metric,{}).get('median'));pv.append(s.get(metric,{}).get('P95'))
        av=np.array([v if v is not None else np.nan for v in av]);pv=np.array([v if v is not None else np.nan for v in pv])
        ax.bar(x-.18,av,.36,label='中位数');ax.bar(x+.18,pv,.36,label='P95');ax.set_xticks(x,labels,rotation=55,ha='right',fontsize=8);ax.set_title(title);ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
        for i,v in enumerate(av):
            if np.isfinite(v):ax.annotate(f'{v:.2g}',(i-.18,v),fontsize=7,ha='center',va='bottom')
    fig.suptitle('两解分歧量级：同一个冻结Sim(3)，不再次拟合相机\n无GT；R中1尺度单位=1mm；不是相机精度或重复稳定性',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.93));path=REPORT/'figures/CAMERA_POSE_DISAGREEMENT.png';fig.savefig(path,dpi=125);plt.close(fig);return path


def ring_figure(records):
    fig,axs=plt.subplots(2,5,figsize=(18,8))
    for ax,(case,r,p,ring) in zip(axs.flat,records):
        for arm,color in [('R','#1782bd'),('S','#df7217')]:
            data=ring.get('arms',{}).get(arm,{})
            sweep=data.get('scale_sweep',[])
            ax.plot([s['scale'] for s in sweep],[s.get('ring',{}).get('median_frame_MAE_px',np.nan) for s in sweep],'-o',color=color,label=arm,markersize=3)
            yaw=data.get('yaw_control',{}).get('ring',{}).get('median_frame_MAE_px')
            if yaw is not None:ax.scatter([1],[yaw],marker='x',s=65,color=color)
        ax.set_title(short(case),fontsize=10);ax.set_xlabel('相机+点共同尺度倍数');ax.set_ylabel('Ring留出轮廓MAE（px）');ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Ring的额外信息：整体尺度变化不改变RGB投影，却通常改变固定尺寸CAD投影\n×=绕圆环轴共同旋转30°；轴对称Ring无法消除此自由度。曲线不用于选择尺度，无GT。',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.91));path=REPORT/'figures/RING_OBSERVABILITY.png';fig.savefig(path,dpi=120);plt.close(fig);return path


def unavailable_coverage(case,n,reason):
    return [dict(case=case,physical_group=case.rsplit('_',1)[0],arm=arm,selected_frames=n,
                 numeric_cameras=None,registered_union=None,component_sizes='[]',rgb_pass=None,
                 rgb_fraction=None,graph_three_support_targets=None,fixed_camera_complete=None,
                 fixed_targets=2,normalization_status='NOT_EVALUABLE',native_success=0,native_planned=2,
                 native_attempted=0,hero_status='NOT_EXECUTED',evaluation_status=reason) for arm in ['R','S']]


def report_expanded():
    E.mkdir(exist_ok=True);(REPORT/'figures').mkdir(exist_ok=True)
    records=[];coverage=[];projection=[];pose_rows=[];role_rows=[];pose_summaries=[];ring_checks=[];ring_scales=[];hero_depth=[];manifest=[];state=[]
    for case in authorized_cases('expanded'):
        root=BASE/case;common=root/'common';dest=E/case;dest.mkdir(exist_ok=True)
        if not (root/'CAMERA_RESULTS.json').exists():
            reason='NOT_EVALUABLE_CAMERA_RESULTS_MISSING'
            n=len(read(HIST/'prepared'/case/'PREPARED.json')['frames'])
            coverage.extend(unavailable_coverage(case,n,reason))
            for arm in ['R','S']:
                for region in ['polyp','background']:
                    for domain in ['all_fixed_queries','common_predictable_queries']:
                        projection.append(dict(case=case,physical_group=case.rsplit('_',1)[0],arm=arm,region=region,domain=domain,test_tracks=None,total=None,predicted=None,success_3px=None,success_fraction=None,predicted_fraction=None,median_px=None,P95_px=None,status=reason))
            state.append(dict(case=case,status=reason));continue
        verify_common(case);r=read(root/'CAMERA_RESULTS.json');p=read(root/'POSE_DIFFERENCES.json') if (root/'POSE_DIFFERENCES.json').exists() else {};ring=read(root/'RING_DIAGNOSTIC.json') if (root/'RING_DIAGNOSTIC.json').exists() else {}
        records.append((case,r,p,ring));n=r['frames'];meta=read(common/'meta.json');split=read(common/'split.json');tr=np.load(common/'tracks.npz')
        for f in ['INPUT_MANIFEST.json','split.json','TUPLES_FROZEN.json','ledger.json']:shutil.copy2(common/f,dest/f)
        for f in ['POSE_DIFFERENCES.json','ROLE_POSE_DIFFERENCES.json','RING_DIAGNOSTIC.json','NORMALIZATION_FROZEN.json','HERO_DEPTH_RESULTS.json']:
            if (root/f).exists():shutil.copy2(root/f,dest/f)
        # Compact camera evidence; full original receipt and predictions remain hash-addressed locally.
        compact={k:v for k,v in r.items() if k not in ['arms','historical_Q0_Q1']};compact['arms']={}
        for arm in ['R','S']:
            a=r['arms'][arm];compact['arms'][arm]={k:v for k,v in a.items() if k!='camera_receipt'}
            receipt=a['camera_receipt'];components=receipt.get('component_sizes',[len(c) for c in receipt.get('components',[])])
            h=read(root/arm/'hero/RESULT.json') if (root/arm/'hero/RESULT.json').exists() else {'status':'NOT_EXECUTED'}
            runs=h.get('runs',[]);native=sum(x.get('success',False) for x in runs)
            cov=dict(case=case,physical_group=case.rsplit('_',1)[0],arm=arm,selected_frames=n,numeric_cameras=a['numeric_cameras'],registered_union=a['registered_union_count'],component_sizes=json.dumps(components),rgb_pass=a['rgb_pass'],rgb_fraction=a['rgb_pass']/n,graph_three_support_targets=len(a['graph_three_support_targets']),fixed_camera_complete=sum(x['complete'] for x in a['fixed_tuples']),fixed_targets=2,normalization_status=r['normalization']['status'],native_success=native,native_planned=2,native_attempted=len([x for x in runs if x.get('failure')!='ALTERNATE_NOT_NEEDED']),hero_status=h['status'],evaluation_status='EVALUATED')
            coverage.append(cov)
            for region,cat in [('polyp',1),('background',0)]:
                for domain,s in [('all_fixed_queries',a['test'][region]),('common_predictable_queries',r['pairing'][region][arm])]:
                    projection.append(dict(case=case,physical_group=cov['physical_group'],arm=arm,region=region,domain=domain,test_tracks=int((tr['category'][split['test']]==cat).sum()),total=s['total'],predicted=s['predicted'],success_3px=s['success_3px'],success_fraction=s['success_fraction'],predicted_fraction=s['predicted_fraction'],median_px=s['median_px'],P95_px=s['P95_px'],status=s['status']))
            ringa=ring.get('arms',{}).get(arm,{})
            conflict=ringa.get('common_rgb_ring_conflict',{});nominal=ringa.get('nominal',{})
            ring_checks.append(dict(case=case,arm=arm,median_frame_MAE_px=nominal.get('median_frame_MAE_px'),median_frame_P95_px=nominal.get('median_frame_P95_px'),**{k:v for k,v in conflict.items() if k!='criterion'}))
            for sweep in ringa.get('scale_sweep',[]):
                sc=sweep.get('ring',{});rgb=sweep.get('rgb_invariance',{});ring_scales.append(dict(case=case,arm=arm,scale=sweep['scale'],ring_median_frame_MAE_px=sc.get('median_frame_MAE_px'),ring_median_frame_P95_px=sc.get('median_frame_P95_px'),ring_evaluable_frames=sc.get('evaluable_frames'),rgb_projection_max_change_px=rgb.get('max_change_px'),rgb_evaluable_observations=rgb.get('evaluable_observations')))
            for fp in [root/arm/'cameras.npz',root/arm/'cameras_normalized.npz',root/arm/'receipt.json',root/arm/'test_predictions.json',root/arm/'hero/RESULT.json',root/arm/'hero/PLAN_FROZEN.json']:
                if fp.exists():manifest.append(dict(case=case,arm=arm,path=str(fp),sha256=sha(fp),bytes=fp.stat().st_size))
            (dest/arm).mkdir(exist_ok=True)
            for f in ['cameras.npz','cameras_normalized.npz','RGB_CHECKS.json','STARTED.json']:
                if (root/arm/f).exists():shutil.copy2(root/arm/f,dest/arm/f)
            if (root/arm/'hero/RESULT.json').exists():shutil.copy2(root/arm/'hero/RESULT.json',dest/arm/'HERO_RESULT.json')
        save(dest/'CAMERA_RESULTS_COMPACT.json',compact)
        for row in p.get('per_frame',[]):
            pose_rows.append(dict(case=case,**{k:v for k,v in row.items() if k not in ['position_delta']},position_delta=json.dumps(row.get('position_delta'))))
        for subset,s in p.get('summary',{}).items():
            for metric in ['position_norm','rotation_deg']:
                pose_summaries.append(dict(case=case,subset=subset,metric=metric,unit='R_scale_unit' if metric=='position_norm' else 'degree',**s.get(metric,{})))
        roles=p.get('role_pose_differences',{})
        for row in roles.get('per_role',[]):role_rows.append(dict(case=case,**{k:(json.dumps(v) if isinstance(v,(list,dict)) else v) for k,v in row.items() if k not in ['relative_R','relative_S']}))
        for metric in ['position_norm','rotation_deg','translation_error_percent']:
            if metric in roles.get('summary',{}):pose_summaries.append(dict(case=case,subset='frozen_target_support_roles',metric=metric,**roles['summary'][metric]))
        if (root/'HERO_DEPTH_RESULTS.json').exists():
            for d in read(root/'HERO_DEPTH_RESULTS.json'):
                for arm in ['R','S']:
                    for domain in ['all_common','both_nonoccluded']:
                        s=d.get(domain,{});v=s.get(arm,{})
                        hero_depth.append(dict(case=case,arm=arm,domain=domain,source=d.get('source_raw',d.get('source')),target=d.get('target_raw',d.get('target')),pixels=s.get('pixels',0),target_polyp_pixels=d.get('target_polyp_pixels'),fraction_of_target=s.get('fraction_of_target'),median=v.get('median'),P95=v.get('P95'),status='EVALUABLE' if s.get('pixels',0) else 'NOT_EVALUABLE',reason='' if s.get('pixels',0) else d.get('reason','NO_COMMON_PIXELS'),unit='R_scale_unit'))
        state.append(dict(case=case,status='CAMERAS_EVALUATED',pose_status=p.get('status','NOT_EXECUTED'),ring_status=ring.get('status','AVAILABLE' if ring else 'NOT_EXECUTED')))
        # Reuse old pages; new pages only if native outputs actually exist in both arms.
        figpath=REPORT/'figures'/(case+'.png')
        if not figpath.exists() and all((root/a/'hero/RESULT.json').exists() and read(root/a/'hero/RESULT.json').get('status')=='COMPLETED' for a in ['R','S']):
            page(case,r,read(root/'HERO_DEPTH_RESULTS.json'))
    for name,rows in [('EXPANDED_COVERAGE.csv',coverage),('EXPANDED_RESULTS.csv',projection),('CAMERA_POSE_DIFFERENCES.csv',pose_rows),('HERO_RELATIVE_POSE_DIFFERENCES.csv',role_rows),('POSE_DIFFERENCE_SUMMARY.csv',pose_summaries),('RING_CHECK_DIAGNOSTIC.csv',ring_checks),('RING_SCALE_DIAGNOSTIC.csv',ring_scales),('EXPANDED_HERO_DEPTH.csv',hero_depth),('EXPANDED_SOURCE_MANIFEST.csv',manifest)]:csv_write(REPORT/name,rows)
    groups=[]
    for group in sorted({x['physical_group'] for x in coverage}):
        for arm in ['R','S']:
            cs=[x for x in coverage if x['physical_group']==group and x['arm']==arm]
            ps=[x for x in projection if x['physical_group']==group and x['arm']==arm and x['region']=='polyp' and x['domain']=='common_predictable_queries']
            groups.append(dict(physical_group=group,arm=arm,videos_evaluated=sum(x['evaluation_status']=='EVALUATED' for x in cs),videos_total=2,numeric_observed=sum(x['numeric_cameras'] or 0 for x in cs),numeric_nonevaluable_videos=sum(x['numeric_cameras'] is None for x in cs),frames=sum(x['selected_frames'] for x in cs),median_video_rgb_fraction=med([x['rgb_fraction'] for x in cs]),median_video_polyp_query_error_px=med([x['median_px'] for x in ps]),polyp_evaluable_videos=sum(x['median_px'] is not None for x in ps)))
    csv_write(REPORT/'EXPANDED_GROUP_SUMMARY.csv',groups)
    for filename in ['EXPANSION_CPU_STATUS.json','EXPANSION_HERO_STATUS.json','INFERENCE_STARTS.jsonl']:
        if (BASE/filename).exists():shutil.copy2(BASE/filename,E/filename)
    save(E/'REPORT_STATUS.json',dict(expected_videos=10,independent_physical_groups=5,evaluated_videos=len(records),cases=state,coverage=coverage))
    posefig=pose_figure(records);ringfig=ring_figure(records)
    lines=['# Ring+SIFT / SIFT-only：10视频扩组与相机分歧','',f'本轮授权扩至5物理组、10视频。已得到相机评价 {len(records)}/10 视频；不是10个独立物理组。无GT，所有相机差值是两解分歧，不能判断哪臂位置/姿态正确。','', '## 覆盖率（失败与排队保留分母）','','| 视频 | 臂 | 数值相机 | RGB检查 | 三Support Target | 固定组合完整 | HERO成功/计划 | HERO状态 |','|---|---|---:|---:|---:|---:|---:|---|']
    for c in coverage:lines.append(f'| {short(c["case"])} | {c["arm"]} | {c["numeric_cameras"]}/{c["selected_frames"]} | {c["rgb_pass"]}/{c["selected_frames"]} | {c["graph_three_support_targets"]}/{c["selected_frames"]} | {c["fixed_camera_complete"]}/2 | {c["native_success"]}/2 | {c["hero_status"]} |')
    lines+=['','数值相机、共同RGB通过、能组成四帧输入及原生输出是不同覆盖层次。S注册并集/分量大小在CSV；后续评价只用最大连通分量，不混合坐标系。','', '## 投影一致性（息肉/背景分别、共同可预测query）','','| 视频 | 区域 | 共同query数 | R median/P95 px | S median/P95 px | R ≤3px / 全部 | S ≤3px / 全部 |','|---|---|---:|---:|---:|---:|---:|']
    for case,r,p,ring in records:
        for region in ['polyp','background']:
            pair=r['pairing'][region];a,b=pair['R'],pair['S'];ra,sa=r['arms']['R']['test'][region],r['arms']['S']['test'][region]
            lines.append(f'| {short(case)} | {region} | {pair["common_predicted"]}/{pair["total"]} | {fmt(a["median_px"])} / {fmt(a["P95_px"])} | {fmt(b["median_px"])} / {fmt(b["P95_px"])} | {ra["success_3px"]}/{ra["total"]} | {sa["success_3px"]}/{sa["total"]} |')
    lines+=['','旧held曾参与历史门控：这里只保证B内train/validation/test隔离，不是历史未消费盲测。相同query图像的训练轨迹参与相机恢复，因此称留出轨迹测试；不是整图独立测试。','', '## 相机位置姿态差值量级','','所有位置数值单位均为R尺度归一单位（R中1单位=1mm），S不是独立毫米恢复；旋转单位为度。只用HERO前冻结的训练点Sim(3)，不再拟合相机来压低差值。','', '| 视频 | 共同相机/全部 | 中心差median/P95 | 旋转差median/P95 | HERO相对平移差median/P95 | HERO相对旋转差median/P95 |','|---|---:|---:|---:|---:|---:|']
    for case,r,p,ring in records:
        g=p.get('summary',{}).get('all_common',{});role=p.get('role_pose_differences',{}).get('summary',{})
        def two(s,k):return fmt(s.get(k,{}).get('median'))+' / '+fmt(s.get(k,{}).get('P95'))
        lines.append(f'| {short(case)} | {g.get("count",0)}/{r["frames"]} | {two(g,"position_norm")} | {two(g,"rotation_deg")} | {two(role,"position_norm")} | {two(role,"rotation_deg")} |')
    lines+=['','HERO相对位姿按每个冻结Target–Support角色计算，共6角色/视频；同一帧对在两个组合出现仍保留角色身份，不能当独立样本。逐对baseline与平移差占baseline百分比见HERO_RELATIVE_POSE_DIFFERENCES.csv。共同RGB通过帧和固定HERO帧子集的统计见POSE_DIFFERENCE_SUMMARY.csv。整体坐标分歧与局部元组分歧不同，较小相对分歧可以解释外观看起来接近，但本次不是因果识别。','', '## Ring的意义：RGB自洽无法解决所有几何歧义','','固定扰动实验把整段相机中心和三维点同时缩放，保持所有RGB投影；Ring CAD物理尺寸不随重建缩放，留出轮廓残差可变化。该实验展示已知尺寸物体提供了RGB没有的尺度信息，不说明名义1.0一定正确，不用扰动结果改尺度、选相机或重跑HERO。','', '| 视频 | 臂 | 名义Ring MAE/P95中位 px | 两臂RGB均通过但Ring不一致 / 两臂RGB均通过 | 缩放RGB最大变化px |','|---|---|---:|---:|---:|']
    for case,r,p,ring in records:
        for arm in ['R','S']:
            a=ring.get('arms',{}).get(arm,{});nom=a.get('nominal',{});con=a.get('common_rgb_ring_conflict',{});rgb=[s.get('rgb_invariance',{}).get('max_change_px') for s in a.get('scale_sweep',[])];rgb=[x for x in rgb if x is not None]
            lines.append(f'| {short(case)} | {arm} | {fmt(nom.get("median_frame_MAE_px"))} / {fmt(nom.get("median_frame_P95_px"))} | {con.get("conflict_frames","NA")} / {con.get("common_rgb_pass_frames","NA")} | {max(rgb):.3g} |' if rgb else f'| {short(case)} | {arm} | 不可评价 | 不可评价 | 不可评价 |')
    lines+=['','轴对称对照：共同绕Ring轴转30°也保持RGB与Ring投影（离散轮廓采样有小误差）。Ring不能消除绝对绕轴yaw，不能单凭Ring一致性证明完整6DoF。留出Ring不一致是额外约束冲突，可能来自相机、原Mask、K假设或CAD/遮挡；不是已知真假标签。S的Ring坐标依赖与R的训练点归一，Ring满足度不能用来宣布R胜出。Ring q_held也曾用于历史门控，非全新盲测。','', '## 交付与可复现状态','','[扩组可视化入口](EXPANDED_COMPARISON.html) · [相机分歧图](figures/CAMERA_POSE_DISAGREEMENT.png) · [Ring观测性图](figures/RING_OBSERVABILITY.png)。原两段小试在提交4bea8e94完整保留，本轮不重写其相机、元组、深度。','', '入口：`tools/ring_sift_comparison.py --cohort expanded --stage cpu-batch`；GPU阶段`--stage hero-batch`，A调度器活跃时只登记排队；报告`--stage expanded-report`。数据根：`/home/liu/ring_first_3d_workspace/runs/ring_sift_comparison_001`。','', '配对训练扰动稳定性仍NOT_EXECUTED。尚无绝对相机/形状GT。排队HERO不计成功、不计推理失败；失败原始记录保留。覆盖、投影、位姿、Ring曲线都不用于删面、换Support或测试集调参。']
    interpretation=E/'EXPANDED_INTERPRETATION.md'
    if interpretation.exists():lines.insert(3,interpretation.read_text())
    (REPORT/'TECHNICAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    body='<!doctype html><html lang="zh"><meta charset="utf-8"><title>扩组覆盖率、相机差值与Ring意义</title><style>body{max-width:1500px;margin:auto;font-family:sans-serif}img{width:100%}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:5px}</style><h1>无GT：10视频扩组、相机分歧与Ring观测性</h1><p><a href="TECHNICAL_REPORT.md">技术报告</a> · <a href="EXPANDED_COVERAGE.csv">覆盖率</a> · <a href="EXPANDED_RESULTS.csv">投影指标</a> · <a href="CAMERA_POSE_DIFFERENCES.csv">逐帧位姿差</a> · <a href="HERO_RELATIVE_POSE_DIFFERENCES.csv">HERO相对位姿差</a></p>'
    body+='<p>已评价相机：'+str(len(records))+'/10视频，5独立物理组。HERO状态以报告为准，旧两段输出不等于新增八段已推理。</p>'
    for f in [posefig,ringfig]:body+=f'<img src="figures/{f.name}">'
    for case,r,p,ring in records:
        fp=REPORT/'figures'/(case+'.png')
        if fp.exists():body+=f'<h2>{html.escape(short(case))}：已有原生HERO对照</h2><img src="figures/{fp.name}">'
    (REPORT/'EXPANDED_COMPARISON.html').write_text(body+'</html>')
    print('EXPANDED_REPORT',len(records),'videos',flush=True)
