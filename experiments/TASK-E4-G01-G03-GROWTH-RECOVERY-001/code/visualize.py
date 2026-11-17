"""Actual triangles, real masks, explicit embedded/exposed length and all failures."""
from pathlib import Path
import json,html,shutil,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from io_utils import TD,OLD,source_folder,read,body,dump,load_inputs,sha
from lengths import spline
from ring_first_3d.synthetic.io import fetch,outputs
from ring_first_3d.synthetic.raster import ray_map
from ring_first_3d.multisurface.geometry import mesh_sections
from ring_gate import CurrentRingGate
from projection_gate import stats
from scipy.ndimage import binary_dilation

COLORS=['#999999','#3289b7','#df8d34','#8a39a5']
def mesh(ax,b,color,alpha=.6):
    p=Poly3DCollection(b['V'][b.get('F_solid',b['F'])],facecolor=color,alpha=alpha,linewidths=0);ax.add_collection3d(p)
def bounds(ax,lo,hi,elev=20,azim=-65):
    ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='x mm',ylabel='y mm',zlabel='z mm');ax.set_box_aspect(hi-lo);ax.view_init(elev,azim);ax.tick_params(labelsize=6)
def save(fig,path):fig.savefig(path,dpi=125,bbox_inches='tight');plt.close(fig)

def visualize(t,attempt):
    root=attempt.parents[1];ep=fetch(root,'G2_evaluate','EVALUATION.json');ev=read(ep);failure=read(fetch(root,'G2_evaluate','FAILURE_REGISTRY.json'))
    figdir=attempt/'figures';figdir.mkdir();allinfo=[];case_images={}
    for case in ['G01','G03']:
        initial,views,ring,base,chart,source=load_inputs(case);pred=ev['predictions'][case];old=source_folder(case)
        models=[initial,body(old/'STEP_024/BODY.npz'),body(old/'GROWTH_PROPOSAL_024/BODY.npz')];names=['INITIAL','ITERATION_024','OLD_REJECTED']
        p=fetch(root,'G1_'+case,'PREDICTIONS_FROZEN.json').parent/case/'DEFORM_SWEEP_RECOVERY'
        if 'mesh_relative'in pred:final=body(fetch(root,'G1_'+case,pred['mesh_relative']));models.append(final);names.append('RECOVERY'if pred['status']=='NUMERIC'else'FAILED_ATTEMPT_DIAGNOSTIC')
        else:final=models[1]
        u=read(p/'UPDATES.json')if(p/'UPDATES.json').exists()else{};chosen=u.get('chosen');length=chosen.get('length')if chosen else None
        sw=body(p/'FINAL_SWEEP_PARAMETERS.npz')if(p/'FINAL_SWEEP_PARAMETERS.npz').exists()else None
        status='ACCEPTED GROWTH'if pred['status']=='NUMERIC'else'FAILED; not a valid recovered prediction'
        config=read(t['recovery']['configuration']['path'])[case]
        VV=np.concatenate([b['V']for b in models]+[ring['V']]);lo=VV.min(0)-.4;hi=VV.max(0)+.4
        images=[]
        for title,elev,azi in [('FRONT',15,-90),('BACK',15,90),('LEFT',10,0),('RIGHT',10,180)]:
            fig=plt.figure(figsize=(15,4))
            for j,(name,b)in enumerate(zip(names,models)):
                ax=fig.add_subplot(1,4,j+1,projection='3d');mesh(ax,b,COLORS[j]);mesh(ax,ring,'black',.25);bounds(ax,lo,hi,elev,azi);ax.set_title(name,fontsize=8)
            fig.suptitle(case+' '+title+' | actual full Mesh | fixed STEP024 Body / mm | '+status,fontsize=9);fn=case+'_'+title+'.png';save(fig,figdir/fn);images.append(fn)
        if sw is not None:
            curve=spline(sw['control']);parameter=np.linspace(0,1,1025);C=curve(parameter);exit_u=length['exit_parameter']if length else 0.
            inside=parameter<=exit_u;exposed=parameter>=exit_u;exit_point=curve(exit_u)
            center=np.array(config['exit_reference']);span=max(1.,config['root_radius_mm']*1.7);rootlo=center-span;roothi=center+span
            fig=plt.figure(figsize=(14,4))
            for j,(elev,azi)in enumerate([(20,-65),(5,25),(80,-90)]):
                ax=fig.add_subplot(1,3,j+1,projection='3d');mesh(ax,models[1],'gray',.2);mesh(ax,final,'purple',.22)
                ax.plot(*C[inside].T,color='orange',lw=3,label='embedded (excluded)');ax.plot(*C[exposed].T,color='cyan',lw=3,label='exposed stalk')
                ax.scatter(*exit_point,c='red',s=30,label='length starts: first exit');bounds(ax,rootlo,roothi,elev,azi);ax.legend(fontsize=6)
            fig.suptitle(case+' ROOT | frozen original surface + actual Boolean union | '+status,fontsize=9);fn=case+'_ROOT.png';save(fig,figdir/fn);images.append(fn)
            fig=plt.figure(figsize=(14,4));ax=fig.add_subplot(131,projection='3d');mesh(ax,models[1],'gray',.1);ax.plot(*C[inside].T,c='orange',label='embedded');ax.plot(*C[exposed].T,c='purple',label='exposed');ax.scatter(*exit_point,c='red',s=20);bounds(ax,lo,hi);ax.legend(fontsize=7)
            ax=fig.add_subplot(132);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(C,axis=0),axis=1))];ax.plot(parameter,arc);ax.axvline(exit_u,c='red',linestyle='--');ax.set(xlabel='cubic parameter u',ylabel='centerline arc length mm',title='First exit separates embedded/exposed')
            ax=fig.add_subplot(133);stations=np.linspace(0,1,16);ax.plot(stations,2*sw['axes'][:,0],label='nominal axis1 diameter');ax.plot(stations,2*sw['axes'][:,1],label='nominal axis2 diameter');ax.scatter([1],[0],c='black',label='analytic terminal tip');ax.set(xlabel='spline station',ylabel='diameter mm');ax.legend(fontsize=6)
            fig.suptitle(case+' | '+(f'total {length["total_centerline_length_mm"]:.4f} / embedded {length["embedded_length_mm"]:.4f} / EXPOSED {length["exposed_stalk_length_mm"]:.4f} mm'if length else'UNIQUE EXIT NOT EVALUABLE')+' | '+status,fontsize=9);fn=case+'_CENTERLINE_SECTIONS.png';save(fig,figdir/fn);images.append(fn)
        fig,axes=plt.subplots(1,4,figsize=(14,4));center=np.array(config['exit_reference']);r=config['root_radius_mm']
        for ax,(axis,value)in zip(axes,[(0,center[0]-.3*r),(0,center[0]+.3*r),(2,center[2]-.5*r),(2,center[2]-r)]):
            keep=[j for j in range(3)if j!=axis]
            for b,name,color in zip(models,names,COLORS):
                seg=mesh_sections(b['V'],b['F_solid'],axis,value)
                if len(seg):ax.add_collection(LineCollection(seg[:,:,keep],colors=color,linewidths=.8,label=name))
            ax.set(xlim=(lo[keep[0]],hi[keep[0]]),ylim=(lo[keep[1]],hi[keep[1]]),xlabel='mm',ylabel='mm',title=f'{"xyz"[axis]}={value:.3f}mm');ax.set_aspect('equal')
        axes[0].legend(fontsize=6);fig.suptitle(case+' | actual full-triangle plane intersections; internal rejected surfaces remain visible');fn=case+'_TRIANGLE_SECTIONS.png';save(fig,figdir/fn);images.append(fn)
        # Every original FIT view, no deletion or renaming. HOLDOUT metrics remain independent.
        support=set(next(g for g in read(old/'UPDATES.json')['growth']if g['iteration']==24)['candidates'][0]['support_views'])
        for v in views:
            if v['role']!='FIT':continue
            fig,axes=plt.subplots(1,5,figsize=(15,3));axes[0].imshow(v['RGB']);axes[0].set_title('native RGB',fontsize=8)
            axes[1].imshow(v['labels'],vmin=0,vmax=2,cmap='viridis');axes[1].set_title('real Polyp / Ring Mask',fontsize=8)
            ringmap=ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape);known=~binary_dilation(v['labels']==2,iterations=3)
            for ax,b,name in zip(axes[2:],[initial,models[2],final],['INITIAL','OLD REJECTED','RECOVERY'if pred['status']=='NUMERIC'else'FAILED ATTEMPT']):
                rm=ray_map(b['V'],b['F'],v['K'],v['C'],v['labels'].shape);pp=rm['valid']&(rm['z']>0)&(rm['z']<ringmap['z']-.05)
                target=v['labels']==1;rgb=np.zeros((*target.shape,3));rgb[target&~pp&known]=[1,.2,.1];rgb[pp&~target&known]=[.1,.4,1];rgb[~known]=[.4,.4,.4]
                ax.imshow(rgb);ax.contour(target,levels=[.5],colors=['lime'],linewidths=.5);ax.contour(pp,levels=[.5],colors=['white'],linewidths=.5);s=stats(pp,target,known);ax.set_title(f'{name}\nIoU {s["IoU"]:.4f} boundary {s["Boundary_MAE_px"]:.2f}px',fontsize=7)
            for ax in axes:ax.set_axis_off()
            fig.suptitle(f'{case} {v["id"]} {v["video"]} | '+('FROZEN GROWTH SUPPORT'if v['id']in support else'BODY PROTECTION')+' | red missing / blue excess / gray Ring unknown | '+status,fontsize=8)
            fn=case+'_'+v['id']+'_PROJECTION.png';save(fig,figdir/fn);images.append(fn)
        # Full per-view change and Ring before/after with fixed CAD material probe identity.
        summary={(d['case'],d['arm']):d for d in ev['summary']};entries=[d for d in ev['detail']if d['case']==case];prior=next(d for d in entries if d['arm']=='ITERATION_024');last=entries[-1]
        oldviews={v['id']:v for v in prior['projection']};fig,axes=plt.subplots(2,1,figsize=(13,5),sharex=True)
        delta=[v['IoU']-oldviews[v['id']]['IoU']for v in last['projection']];db=[v['Boundary_MAE_px']-oldviews[v['id']]['Boundary_MAE_px']for v in last['projection']]
        axes[0].bar(range(len(delta)),delta);axes[0].axhline(-.01,c='black',ls='--');axes[0].set_ylabel('IoU change');axes[1].bar(range(len(db)),db);axes[1].axhline(1,c='black',ls='--');axes[1].set_ylabel('Boundary MAE delta px');axes[1].set_xticks(range(len(db)),[v['id']+' '+v['role']for v in last['projection']],rotation=75,fontsize=5)
        fig.suptitle(case+' | all original FIT + independent HOLDOUT | '+status);fn=case+'_PER_VIEW.png';save(fig,figdir/fn);images.append(fn)
        rg=CurrentRingGate(models[1],ring);before=rg.reference;after=rg.measure(final);fig,axes=plt.subplots(1,3,figsize=(14,4))
        for ax,key in zip(axes,['max_mm','area_mm2','energy_mm4']):
            for i,direction in enumerate(['body','ring']):ax.bar([3*i,3*i+1],[before[direction+'_'+key],after[direction+'_'+key]],label=direction+'->other')
            ax.set_xticks([0,1,3,4],['B before','B after','R before','R after'],rotation=30);ax.set_title(key)
        fig.suptitle(case+' | bidirectional Ring collision; current-state delta only | '+status);fn=case+'_RING.png';save(fig,figdir/fn);images.append(fn)
        fig=plt.figure(figsize=(15,7));gt=body(ep.parent/case/'GT.npz');evnames=names
        allgt=[body(ep.parent/case/(n+'_GT_ALIGNED.npz'))for n in evnames];common=[body(ep.parent/case/(n+'_INITIAL_GT_FRAME.npz'))for n in evnames];gg=np.concatenate([gt['V']]+[b['V']for b in allgt+common]);glo=gg.min(0)-.3;ghi=gg.max(0)+.3
        for row,group in enumerate([allgt,common]):
            for j,(n,b)in enumerate(zip(evnames,group)):
                ax=fig.add_subplot(2,4,row*4+j+1,projection='3d');mesh(ax,gt,'gray',.2);mesh(ax,b,COLORS[j],.65);bounds(ax,glo,ghi);s=summary[case,n]
                mae=s['Chamfer_MAE_mm']if row==0 else s['fixed_INITIAL_GT_Chamfer_MAE_mm'];ax.set_title(f'{n}\nMAE {mae:.4f}mm',fontsize=7)
        fig.suptitle(case+' | top: actual independent scale1 SE(3); bottom: fixed INITIAL->GT frame | evaluation copies only',fontsize=9);fn=case+'_GT_EVALUATION.png';save(fig,figdir/fn);images.append(fn)
        allinfo.append(dict(case=case,prediction=pred,length=length,chosen=chosen,embedding_configuration=config));case_images[case]=images
    dump(attempt/'SUMMARY.json',dict(cases=allinfo,metrics=ev['summary'],target_groups=2,accepted_growth=sum(p['prediction']['status']=='NUMERIC'for p in allinfo)))
    dump(attempt/'FAILURE_REGISTRY.json',failure);write_reports(t,attempt,ev,allinfo,failure)
    lines=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>G01/G03 Growth Recovery</title><style>body{font:16px sans-serif;max-width:1500px;margin:auto}img{max-width:100%}details{margin:1em}</style><h1>G01/G03 实际拒绝候选恢复</h1><p><a href="../TECHNICAL_REPORT.md">技术报告</a> · <a href="../RESULT_CARD.md">结果卡</a> · <a href="FAILURE_REGISTRY.json">失败台账</a></p><p>全部为实际 Mesh / 原生 Mask 数据。橙色嵌入段不计入柄长；青色外露段从首次穿出点开始。失败候选明确保留，不能当作有效重建。未运行 G05 或 HERO。</p>']
    for c,images in case_images.items():
        lines+=['<h2>'+c+'</h2>',f'<img src="figures/{c}_ROOT.png">'if(c+'_ROOT.png')in images else'',f'<img src="figures/{c}_FRONT.png">']
        for image in images:
            if image in [c+'_ROOT.png',c+'_FRONT.png']:continue
            lines.append(f'<details><summary>{html.escape(image)}</summary><img loading="lazy" src="figures/{image}"></details>')
    (attempt/'index.html').write_text('\n'.join(lines)+'</html>')
    return outputs(attempt,dict(status='PASS',cases=2,figures=sum(map(len,case_images.values())),scientific_failures=failure['records']))

def write_reports(t,attempt,ev,info,failure):
    lines=['# TASK-E4-G01-G03-GROWTH-RECOVERY-001','','![G01 根部真实连接](visualization/figures/G01_ROOT.png)','','## 结论与逐组失败', '']
    for r in info:
        c=r['case'];p=r['prediction'];length=r['length'];accepted=p['status']=='NUMERIC'
        lines.append(f'**{c}：'+('通过全部冻结门禁，形成嵌入式外部统一Mesh。'if accepted else'未完成可接受生长；最终尝试只作为失败诊断，正式预测/柄长为NaN。'))
        if length:lines.append('最后接受/尝试中心线：总弧长 %.5f mm，嵌入弧长 %.5f mm，外露弧长 %.5f mm；实际SDF嵌入深度 %.5f mm；首次穿出点 %s。只有外露弧长是柄长。'%(length['total_centerline_length_mm'],length['embedded_length_mm'],length['exposed_stalk_length_mm'],length['embedding_depth_SDF_mm'],length['exit_point']))
        lines.append('门禁原因：'+json.dumps(p.get('failure_reasons',[]),ensure_ascii=False))
    lines+=['','## 方法与冻结边界','','基线为238c2da1cd842c0eba710a4ec44db5f437bff8e4，核验远端一致；其相对已审计执行源码cadde3e9没有科学代码新增。本轮仅两组、单臂DEFORM_SWEEP_RECOVERY。G01 seed54、G03 seed544均来自iteration24保存的UPDATES，不重新搜索候选，不读取GT调整方向或Patch。','通过16点三次B-spline和半轴softplus逆变换最小二乘恢复5控制点/两轴参数；保存的RMF初始法向复现Double Reflection。历史BODY含被拒绝的临时Graph更新，先用其临时旧顶点完整复现，再记录平移重基准至STEP024。正式Body固定STEP024，未恢复或重训Graph。Adam重新初始化，明确标记REJECTED_CANDIDATE_WARM_START；未声称恢复旧Adam。','嵌入深度预先按min(.5*根部几何平均半径,.25*双向射线局部厚度)确定。近端C0固定，另外4控制点和5×2轴参数参与同一PyTorch优化；沿用三次5控制/16站×16角度与Double Reflection RMF，终端为解析收尖。三阶段外露目标比例.35/.7/1，每阶段8次局部更新，固定回缩与信赖域；不重跑36轮Body。','柄长用冻结STEP024实体SDF的唯一首次内→外穿出点分割，SciPy对B-spline导数范数数值积分；总长=嵌入弧长+外露弧长，不用端点弦长。交界附近的已声明局部嵌入区允许构造性重叠，其他区域/远端回入与Sweep自身相交仍拒绝。','外部Mesh使用既有Blender5.0.1 EXACT Boolean UNION，不使用GT场景、体素重建或事后补洞。布尔接缝仅以预冻结1e-8mm阈值合并数值重合顶点并作BEAUTY三角化，保留RAW_EXACT_BOOLEAN；没有按自交检测结果删除面片。最终完整执行非流形、重复面、闭合、绕序、退化、自交、基底和有效旧表面保留检查。','[Blender官方布尔文档](https://docs.blender.org/manual/en/5.0/modeling/modifiers/generate/booleans.html)。成熟后端仍可能出现无效结果，不能以Boolean返回成功代替完整几何验收。','二维对应复用002 ProjectionGate的双向、mutual NN、法向、可见性、40px和Ring unknown。区别旧/替代根部/新外露面，保留区域覆盖不因合法替代根部而误判坍缩。新柄部须产生至少3个原支持FIT视角且同时覆盖004/005的有效新外露对应，两视频数据项均真实改善；所有FIT继续参与且相对STEP024保护ΔIoU≥-.01、Boundary增量≤1px，同时维持历史初始好视角保护。','PyTorch轮廓梯度使用实际Boolean新面的冻结Face/bary局部代理，并非可微精确Boolean算子。每个接受候选重新执行Boolean、全部FIT渲染和全部对应/门禁，绝不以旧对应或总代价下降替代真实投影验证。记录梯度和所有回缩拒绝；HOLDOUT只在两组预测冻结后评价。','Ring门禁只比较candidate-current，两方向最大穿透、面积、面积加权能量及局部CAD面严重程度；初始仅诊断，不再施加initial/current逐点更严上界。重复SDF查询和float32 ULP预先确定深度容差，面积/能量容差由同一长度容差与面积界推导。它是采样的detached门禁，不给Body或柄部提供排斥梯度；不宣称连续碰撞完备证明。','', '## 定量结果（固定两组分母）','','|病例|状态/臂|FIT IoU|HOLDOUT IoU|GT MAE mm|GT P95 mm|GT覆盖@.5|F-score@.5|固定初始GT框架MAE mm|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in ev['summary']:
        if r['status']=='FAILED_NAN':lines.append(f'|{r["case"]}|RECOVERY FAILED|NaN|NaN|NaN|NaN|NaN|NaN|NaN|');continue
        keys=['FIT_IoU','HOLDOUT_IoU','Chamfer_MAE_mm','Chamfer_P95_mm','GT_coverage_at0p5mm','Fscore_at0p5mm','fixed_INITIAL_GT_Chamfer_MAE_mm']
        lines.append('|'+r['case']+'|'+r['arm']+' ('+r['status']+')|'+'|'.join(f'{r[k]:.5f}'for k in keys)+'|')
    count=sum(r['prediction']['status']=='NUMERIC'for r in info)
    lines+=['','每方向固定12000面积样本并查询真实三角面；报告MAE/median/P95/max和覆盖，Chamfer为双向非平方距离。先冻结两组全部输出，后读GT；沿用best_rigid015尺度固定独立SE(3)评价副本，并额外使用历史INITIAL→GT固定矩阵诊断。两种评价均保留，不根据GT挑结果，不回写训练模型/相机。新的拓扑没有伪称共享材料Face身份；固定诊断指固定坐标框架和样本分母。','', '嵌入、穿出点、根部双轴及16站截面、新顶点/面数、净新增面积/体积、实际完整几何检查见GROWTH_METRICS.csv与每次GATES.json；双向Ring更新前后及差值见RING_COLLISION_METRICS.csv。失败候选的数值仅作为诊断，不能计入独立成功覆盖率。','', '## 固定审计表','','|审计项目|必须汇报|','|---|---|','|目标组数|2：G01、G03；单臂各一次局部恢复|',f'|本算法独立成功|{count}/2门禁通过输出；不等同于GT三维正确|',f'|本算法失败|{2-count}/2；正式预测/柄长NaN，最后尝试Mesh和定量诊断保留|','|历史测量值回退|0；指定历史实际候选是本轮授权起点，未读取其他路线补全|','|失败组及具体原因|Failure Registry及各组UPDATES/GATES；不自动晋升永久规则|','|最终统计样本|完整2组分母，成功组配对，失败不隐藏；表面MAE/median/P95/max见CSV，直径相对误差N/A|','|是否使用GT选择算法|否；源码、配置、输入、嵌入深度与容差预冻结；两组预测冻结后独立GT评价|','', '## 测试、资产与审阅入口','','回归包含既有35基线、上一轮212项集合及本轮嵌入、布尔融合、唯一穿出弧长、双向Ring和隔离测试。完整实测计数见recovery_regression/result.json；原始开发测试故障也保留，不通过删测试或关闭自交获得通过。旧工作树及全部历史失败只读，本轮不执行G05/HERO/DXY/相机更新。','', '所有原FIT逐视角原图/Mask/投影、正背左右完整Mesh、根部内部/外露和第一次穿出标记、真实三角面切面、截面尺寸、Ring差值和GT对齐副本均在离线visualization/index.html。失败状态写在每张相关图中。','', '工程存储就绪曾遇磁盘满，仅清理可再生成的HTTP/缩略图/浏览器缓存，没有删除科研文件或模型权重。新工作树稀疏检出初始化错误已在开跑前纠正；缓存、错误与修复日志均留存evidence。']
    (attempt/'TECHNICAL_REPORT.md').write_text('\n'.join(lines)+'\n');(attempt/'RESULT_CARD.md').write_text('# RESULT_CARD\n\n'+'\n\n'.join(lines[6:12])+f'\n\n独立成功{count}/2；失败正式预测NaN。完整指标与拒绝记录见TECHNICAL_REPORT.md。未执行HERO或其他组。\n')
