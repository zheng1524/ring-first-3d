"""Data-driven PNGs, exact triangle-plane cuts, full Mesh GLBs; plain local file list."""
from pathlib import Path
import json,shutil,html
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
from ring_first_3d.synthetic.io import fetch,save_json,outputs
from ring_first_3d.multisurface.geometry import mesh_sections,plane_coordinates
from data_adapter import simulation_data,real_data
from body_update import ray_map,ring_maps


def draw_mesh(ax,m,color,alpha=.6):
    poly=Poly3DCollection(m['V'][m['F']],facecolor=color,edgecolor='none',alpha=alpha);ax.add_collection3d(poly)


def world_axes(ax,lo,hi):
    ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(hi-lo);ax.view_init(elev=22,azim=-65);ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm')


def export_scene(path,models):
    s=trimesh.Scene()
    for name,m,color in models:
        mesh=trimesh.Trimesh(np.asarray(m['V'])*.001,m['F'],process=False);mesh.visual.face_colors=color
        s.add_geometry(mesh,node_name=name,geom_name=name)
    s.metadata.update(unit='m',source_coordinate_unit='mm',export_scale_from_source=.001)
    s.export(path)


def body_figures(case,views,ring,initial,deform,final,gt,training,fig,models):
    allV=np.concatenate([m['V'] for m in [initial,deform,final]+([gt] if gt is not None else [])]+[ring['V']]);lo=allV.min(0)-.5;hi=allV.max(0)+.5
    f=plt.figure(figsize=(19,5))
    panels=[('EXACT013 INITIAL',initial),('DEFORMATION ONLY',deform),('DEFORMATION + GROWTH',final)]+([('GT independent evaluation',gt)] if gt is not None else [])
    for j,(name,m) in enumerate(panels):
        ax=f.add_subplot(1,4,j+1,projection='3d');
        if gt is not None:draw_mesh(ax,gt,'gray',.18)
        draw_mesh(ax,m,'purple' if j<3 else 'gray',.55);draw_mesh(ax,ring,'black',.15);world_axes(ax,lo,hi);ax.set_title(case+' '+name)
    f.suptitle('Actual full triangle Meshes; common physical Ring frame; no GT registration in C0');f.tight_layout();f.savefig(fig/(case+'_BODY_3D.png'),dpi=150);plt.close(f)
    # Show vertex displacement and actual new faces distinctly.
    f=plt.figure(figsize=(12,5));ax=f.add_subplot(121,projection='3d');draw_mesh(ax,initial,'gray',.15);n=len(initial['V']);d=final['V'][:n]-initial['V'];a=ax.scatter(*final['V'][:n].T,c=np.linalg.norm(d,axis=1),cmap='inferno',s=8);f.colorbar(a,ax=ax,label='original vertex displacement mm');take=np.arange(0,n,max(1,n//48));ax.quiver(*initial['V'][take].T,*d[take].T,color='purple',length=1,normalize=False);world_axes(ax,lo,hi);ax.set_title('Original vertices: actual 3D deformation')
    ax=f.add_subplot(122,projection='3d');new=(final['F']>=n).any(1);draw_mesh(ax,dict(V=final['V'],F=final['F'][~new]),'gray',.4)
    if new.any():draw_mesh(ax,dict(V=final['V'],F=final['F'][new]),'orange',.9)
    world_axes(ax,lo,hi);ax.set_title('New structure orange: '+str(int(new.sum()))+' actual faces');f.tight_layout();f.savefig(fig/(case+'_DEFORMATION_GROWTH.png'),dpi=150);plt.close(f)
    # Four fixed exact Mesh cross sections, no sampled/averaged outline.
    f,axs=plt.subplots(4,3,figsize=(14,16));planes=[(0,0.),(1,0.),(2,-2.),(2,-6.)]
    audit=[]
    for row,(axis,offset) in enumerate(planes):
        coords=[k for k in range(3) if k!=axis]
        for col,(name,m) in enumerate([('Initial',initial),('Deform',deform),('Deform+grow',final)]):
            ax=axs[row,col]
            for label,mesh,color,style in ([('GT',gt,'black','solid')] if gt is not None else [])+[('Body',m,'purple','solid'),('Ring',ring,'gray','dotted')]:
                seg=mesh_sections(mesh['V'],mesh['F'],axis,offset);xy=plane_coordinates(seg,axis)
                if len(seg):ax.add_collection(LineCollection(xy,colors=color,linewidths=.8,linestyles=style,label=label))
                audit.append(dict(case=case,method=name,plane_axis=axis,offset_mm=offset,Mesh=label,actual_triangle_intersections=len(seg)))
            ax.set(xlim=(lo[coords[0]],hi[coords[0]]),ylim=(lo[coords[1]],hi[coords[1]]),xlabel='XYZ'[coords[0]]+' mm',ylabel='XYZ'[coords[1]]+' mm',title=f'{name}: {"XYZ"[axis]}={offset:g}mm');ax.set_aspect('equal');ax.grid(alpha=.15)
    f.suptitle(case+' actual triangle-plane intersections; fixed mm limits');f.tight_layout();f.savefig(fig/(case+'_ACTUAL_MESH_SECTIONS.png'),dpi=150);plt.close(f)
    save_json(fig/(case+'_SECTION_AUDIT.json'),audit)
    for name,m in [('INITIAL',initial),('DEFORM_ONLY',deform),('DEFORM_GROW',final)]:
        export_scene(models/(case+'_'+name+'.glb'),[(case+'_'+name,m,[150,30,190,180]),('Ring_CAD',ring,[0,0,0,140])]+([('GT_EVALUATION_ONLY',gt,[150,150,150,100])] if gt is not None else []))
    # Every inherited view, including failures, actual native Mask and full-Mesh projection.
    rz=ring_maps(views,ring)
    for index in range(0,len(views),4):
        vv=views[index:index+4];f,axs=plt.subplots(len(vv),3,figsize=(15,3.4*len(vv)),squeeze=False)
        for row,v in enumerate(vv):
            r0=ray_map(initial['V'],initial['F'],v['K'],v['C'],v['labels'].shape);r1=ray_map(final['V'],final['F'],v['K'],v['C'],v['labels'].shape)
            p0=r0['valid']&(r0['z']<rz[v['id']]-.05);p1=r1['valid']&(r1['z']<rz[v['id']]-.05);target=v['labels']==1
            for j in range(3):axs[row,j].imshow(v['RGB']);axs[row,j].set_xlim(0,target.shape[1]);axs[row,j].set_ylim(target.shape[0],0);axs[row,j].set_aspect('equal')
            axs[row,0].contour(target,levels=[.5],colors=['lime'],linewidths=.8);axs[row,0].contour(p0,levels=[.5],colors=['magenta'],linewidths=.8);axs[row,0].set_title(v['id']+' '+v['role']+' INITIAL')
            overlay=np.zeros((*target.shape,4));overlay[target&~p0]=[1,.6,0,.65];overlay[p0&~target]=[0,.4,1,.65];axs[row,1].imshow(overlay)
            pp=training/('STEP_000/'+v['id']+'.npz')
            if pp.exists():
                a=np.load(pp);ok=np.flatnonzero(a['accepted']);ix=ok[np.linspace(0,len(ok)-1,min(14,len(ok)),dtype=int)] if len(ok) else ok
                for b,q,face in zip(a['projected_uv'][ix],a['target_uv'][ix],a['face'][ix]):
                    axs[row,1].annotate('',xy=q,xytext=b,arrowprops=dict(arrowstyle='->',color='yellow',lw=.7));axs[row,1].text(b[0],b[1],str(face),color='white',fontsize=5)
            axs[row,1].set_title('R+ orange / R- blue; actual Face arrows' if v['role']=='FIT' else 'HOLDOUT: evaluation only, no update correspondences')
            axs[row,2].contour(target,levels=[.5],colors=['lime'],linewidths=.8);axs[row,2].contour(p1,levels=[.5],colors=['magenta'],linewidths=.8);axs[row,2].set_title('FINAL actual3D projection; no image warp')
        f.suptitle(case+' fixed native px; green observed / magenta predicted; Ring unknown retained');f.tight_layout();f.savefig(fig/(case+'_VIEW_%02d.png'%index),dpi=140);plt.close(f)


def real_gt_panels(root,case,gt,fig,models):
    aligned={a:dict(np.load(fetch(root,'G7_real_evaluate',case+'/'+a+'_GT_ALIGNED.npz'))) for a in ['INITIAL','DEFORM_ONLY','DEFORM_GROW']}
    allV=np.concatenate([gt['V']]+[m['V'] for m in aligned.values()]);lo=allV.min(0)-.5;hi=allV.max(0)+.5;f=plt.figure(figsize=(16,5))
    for j,(name,m) in enumerate(aligned.items()):
        ax=f.add_subplot(1,3,j+1,projection='3d');draw_mesh(ax,gt,'gray',.25);draw_mesh(ax,m,'purple',.65);world_axes(ax,lo,hi);ax.set_title(case+' '+name+' actual scale1 GT SE3')
        np.savez_compressed(models/(case+'_'+name+'_GT_ALIGNED.npz'),**m)
        export_scene(models/(case+'_'+name+'_GT_ALIGNED.glb'),[(name+'_ALIGNED_EVALUATION_ONLY',m,[160,25,190,170]),('GT',gt,[150,150,150,100])])
    f.suptitle('Independent best_rigid015 evaluation copies; transforms never enter Body/HERO training');f.tight_layout();f.savefig(fig/(case+'_GT_ALIGNED_COMPARISON.png'),dpi=150);plt.close(f)


def hero_figures(root,case,source,initial,final,ring,fig,models):
    data=[v for v in source['views'] if v['role']=='FIT'];methods=['M0','RAY_INITIAL','RAY_UPDATED'];allmeshes={}
    for method in methods:
        allmeshes[method]=[dict(np.load(fetch(root,'G6_hero_relocate',case+'/'+method+'/'+v['id']+'.npz'))) for v in data]
        body=final if method=='RAY_UPDATED' else initial
        nodes=[('FROZEN_BODY',body,[150,150,150,100]),('Ring_CAD',ring,[0,0,0,160])]
        for v,m in zip(data,allmeshes[method]):
            color=[220,25,25,160] if v['video']=='004' else [25,60,230,160];nodes.append((v['id'],m,color))
            np.savez_compressed(models/(case+'_'+method+'_'+v['id']+'.npz'),**m)
        export_scene(models/(case+'_'+method+'_FULL_HERO.glb'),nodes)
    allV=np.concatenate([initial['V'],final['V'],ring['V']]+[m['V'] for vv in allmeshes.values() for m in vv]);lo=allV.min(0)-.5;hi=allV.max(0)+.5
    f,axs=plt.subplots(4,3,figsize=(15,17));audit=[]
    for i,(axis,off) in enumerate([(0,0.),(1,0.),(2,-2.),(2,-6.)]):
        coord=[k for k in range(3) if k!=axis]
        for j,method in enumerate(methods):
            ax=axs[i,j];body=final if method=='RAY_UPDATED' else initial
            for name,m,c,style in [('Body',body,'gray','dashed'),('Ring',ring,'black','solid')]+[(v['id'],m,'red' if v['video']=='004' else 'blue','solid') for v,m in zip(data,allmeshes[method])]:
                seg=mesh_sections(m['V'],m['F'],axis,off)
                if len(seg):ax.add_collection(LineCollection(plane_coordinates(seg,axis),colors=c,linewidths=.7,linestyles=style))
                audit.append(dict(case=case,method=method,view=name,axis=axis,offset_mm=off,actual_triangle_intersection_N=len(seg)))
            ax.set(xlim=(lo[coord[0]],hi[coord[0]]),ylim=(lo[coord[1]],hi[coord[1]]),xlabel='XYZ'[coord[0]]+' mm',ylabel='XYZ'[coord[1]]+' mm',title=method+' '+'XYZ'[axis]+'='+str(off)+'mm');ax.set_aspect('equal');ax.grid(alpha=.15)
    f.suptitle(case+' all native HERO triangle-plane cuts: original / original Body rays / updated Body rays');f.tight_layout();f.savefig(fig/(case+'_HERO_SECTIONS.png'),dpi=150);plt.close(f);save_json(fig/(case+'_HERO_SECTION_AUDIT.json'),audit)


def visualize(task,attempt,real=False):
    root=attempt.parents[1];fig=attempt/'figures';fig.mkdir();models=attempt/'meshes';models.mkdir();metric=json.loads(fetch(root,'G2_C0_evaluate','C0_METRICS.json').read_text())
    initial,views,ring,_,_=simulation_data(task);gt=dict(np.load(fetch(root,'G2_C0_evaluate','GT.npz')))
    deform=dict(np.load(fetch(root,'G1_C0_update','C0/DEFORM_ONLY/FINAL.npz')));final=dict(np.load(fetch(root,'G1_C0_update','C0/DEFORM_GROW/FINAL.npz')))
    body_figures('C0',views,ring,initial,deform,final,gt,fetch(root,'G1_C0_update','C0/DEFORM_GROW/UPDATES.json').parent,fig,models)
    for name,stage in [('C0_METRICS.json','G2_C0_evaluate'),('INITIALIZATION_AUDIT.json','G0_initialization')]:shutil.copyfile(fetch(root,stage,name),attempt/name)
    for arm in task['structural']['Body_arms']:
        base=fetch(root,'G1_C0_update','C0/'+arm+'/UPDATES.json').parent;shutil.copyfile(base/'UPDATES.json',attempt/(arm+'_UPDATES.json'))
        # Curated complete intermediate arrays. Every stage remains in immutable run.
        dest=attempt/'evidence'/arm;dest.mkdir(parents=True)
        for p in ('STEP_000','STEP_012','STEP_024','STEP_035','FINAL_CORRESPONDENCES'):
            if (base/p).exists():shutil.copytree(base/p,dest/p)
        for n in ('INITIAL.npz','FINAL.npz'):shutil.copyfile(base/n,dest/n)
    failures=[]
    for key,ok in metric['scientific_checks'].items():
        if not ok:failures.append(dict(id='SU-C0-'+key,category='scientific_negative',symptom=key+' not satisfied',cause_status='observed_not_isolated',cause='See measured C0 arms, actual update and growth rejection logs; no GT tuning',repair=None,regression=['C0 scientific gate'],evidence=['C0_METRICS.json','DEFORM_GROW_UPDATES.json'],rule_status='candidate',review=dict(status='unreviewed')))
    realstatus='NOT_RUN_C0_GATE_FAILED' if not metric['scientific_pass'] else 'AUTHORIZED_AFTER_C0'
    if real:
        for n in ('REAL_BODY_METRICS.json','REAL_HERO_METRICS.json'):shutil.copyfile(fetch(root,'G7_real_evaluate',n),attempt/n)
        # Actual world and independently aligned Mesh exports, never aligned HERO input.
        pred=json.loads(fetch(root,'G5_real_update','BODY_PREDICTIONS_FROZEN.json').read_text())
        for case in task['structural']['real_cases']:
            ini,vw,rg,_,_=real_data(task,case);source=next(r for r in __import__('data_adapter').sources(task)['cases'] if r['case']==case);g=dict(np.load(source['GT']['path']))
            aa={r['arm']:r for r in pred['records'] if r['case']==case and r.get('status')=='NUMERIC'}
            if set(task['structural']['Body_arms'])<=set(aa):
                d=dict(np.load(fetch(root,'G5_real_update',aa['DEFORM_ONLY']['mesh_relative'])));f=dict(np.load(fetch(root,'G5_real_update',aa['DEFORM_GROW']['mesh_relative'])))
                # These panels are intentionally world coordinates; aligned GT copies separate.
                body_figures(case,vw,rg,ini,d,f,None,fetch(root,'G5_real_update',aa['DEFORM_GROW']['update_record_relative']).parent,fig,models)
                real_gt_panels(root,case,g,fig,models)
                source_hero=next(x for x in __import__('data_adapter').sources(task)['real_groups'] if x['group']==case)
                if len([x for x in source_hero['views'] if x['role']=='FIT'])>=2:hero_figures(root,case,source_hero,ini,f,rg,fig,models)
        realstatus='EXECUTED_SEE_REAL_METRICS'
    save_json(attempt/'FAILURE_REGISTRY.json',dict(policy='Scientific observations, never auto-promoted rules',failures=failures))
    lines=['# '+task['task_id'],'','![Shared 3D deformation and generated structure](visualization/figures/C0_DEFORMATION_GROWTH.png)','',
           'Scientific status: '+('C0_PASS' if metric['scientific_pass'] else '**C0_CORE_VALIDATION_FAILED — real/HERO execution stopped**'),'',
           'One exact historical013 Init-A loader and one shared FIT-only updater are used for both domains. Cameras/K, Ring CAD, images and splits are fixed. No HERO depth, GT shape, E1/E2 or image warp enters Body training.',
           '', '## Measured ideal C0','', '| Arm | FIT IoU | HOLDOUT IoU | Chamfer MAE mm | P95 mm | Accepted growth |','| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in metric['rows']:lines.append(f"| {r['arm']} | {r['split_means']['FIT']['IoU']:.6f} | {r['split_means']['HOLDOUT']['IoU']:.6f} | {r['Chamfer_mm']['MAE']:.6f} | {r['Chamfer_mm']['p95']:.6f} | {r.get('updates',{}).get('accepted_growth',0)} |")
    lines+=['','C0 uses the existing frozen G01-like physical Ring scene, with exact cameras/Mask and zero injected pose noise. GT comparison uses the unchanged canonical metric frame; no GT best alignment hides placement error. Real shape evaluation, if authorized by this gate, uses historical scale1 best_rigid015 copies only.',
            '', '## Method','',
            'For each FIT view: R+=M\\P, R-=P\\M with Ring-uncertain pixels excluded from optimization and retained in evidence. Visible triangles and barycentric coordinates come from the existing metric ray/triangle renderer. R- pixels map to their own visible faces; R+ contour targets map to the nearest currently visible projected boundary. No new 3D depth is invented for missing pixels.',
            '', 'L(V)=sum_i w_i Huber((pi_i(sum_j bary_j V_face_j)-q_i)/20) + lambda_lap ||L0(V−Vref)||² + lambda_edge ||edge(V)−edge(Vref)||² + lambda_prior ||V−Vref||². Historical video/direction weights are retained. Laplacian is the mature PyTorch3D sparse implementation. Ring/base rules remain hard acceptance constraints through the exact historical GeometryGuard. No claim of ARAP implementation; edge/Laplacian displacement regularization is used.',
            '', 'At every accepted or rejected outer iteration all FIT correspondences are rebuilt. Adam proposes a bounded metric vertex step, historical 8-level retraction and complete fixed-assignment FIT loss/geometry checks accept or reject it. Records contain each view gradient and gradient·actual_shared_displacement, which is directional work rather than a unique causal displacement decomposition.',
            '', 'Growth is a declared minimal local patch-extrusion baseline. Missing-region support must span >=3 views and both videos, with a conditioned stack of calibrated projection Jacobians. A least-squares common3D displacement must explain the2D residuals consistently and point outward. A connected patch is replaced by an extruded cap and continuous sidewalls. Only candidates passing nonintersection, winding, manifold connectivity, base and Ring checks and balanced FIT IoU gain are accepted. New vertex/face IDs and parent IDs are saved. New topology enters the same shared differentiable optimizer; rest geometry is frozen per accepted topology stage. This is not a type-specific stalk/sweep model.',
            '', '## Gate and downstream status','',json.dumps(metric['scientific_checks'],ensure_ascii=False),'',
            'G01/G03/G05 and HERO: '+realstatus+'. A failed C0 is retained as a scientific negative and stops downstream experiments; it is not repaired by GT-driven tuning or by silently using E1/E2. Numerical deformation output alone does not validate missing-structure recovery.',
            '', 'HERO adapter (executed only after C0 pass): exact source UV -> current Body visible Face/bary -> low-DOF axial model z_new=(1+s_frame)z+b_video+b_frame+gx*u_normalized+gy*v_normalized, robust0.5mm Body tolerance and frozen priors/bounds. Camera/pixels/Body remain fixed; every source vertex/triangle is retained, and edge distortions are evaluated. M0/RAY_INITIAL/RAY_UPDATED use identical data. No global fusion or watertight closure. Real surface concentration is not independent absolute3D accuracy.',
            '', '## Fixed audit','',
            '| 审计项目 | 必须汇报 |','| --- | --- |',
            '| 目标组数 | 虚拟 C0 1组；真实 G01/G03/G05 3组，受C0门禁约束 |',
            '| 本算法独立成功 | C0 两个实验臂产生数值Mesh；科学通过见门禁，不能等同准确 |',
            '| 本算法失败 | C0未通过项逐项保留；若门禁失败，真实3组及HERO为NOT_RUN/NaN而非算法成功 |',
            '| 历史测量值回退 | 0；仅用户指定013初始资产和冻结底层图像/相机复用 |',
            '| 失败组及具体原因 | FAILURE_REGISTRY.json；逐次几何/生长拒绝见*_UPDATES.json和原始attempt |',
            '| 最终统计样本 | C0固定24视角（16FIT/8HOLDOUT）；每臂双向各12000表面样本；不筛选成功视角 |',
            '| 是否使用GT选择算法 | 否；TASK/代码/输入哈希先冻结，全部C0预测冻结后评价；门禁只决定是否继续 |',
            '', 'No diameter is estimated: median absolute relative diameter error N/A; full MAE/median/P95/max surface metrics are in C0_METRICS.json. Strict/conditional3D occupancy IoU is not a primary endpoint of this task and is not invented.',
            '', 'Original sources, protected workspaces and previous experiment results remain unchanged. New simulation uses the exact real013 mesh, not the old9-parameter E1/E2 initializer. Full source/asset/configuration SHA256 and runner freeze record accompany the task. PNGs show actual triangles and native pixels; GLBs export millimetres as metres with factor0.001. The HTML file is only a local file list.']
    report='\n'.join(lines)+'\n';(attempt/'TECHNICAL_REPORT.md').write_text(report)
    (attempt/'RESULT_CARD.md').write_text('\n'.join(lines[:12])+ '\n\nC0 gate: '+str(metric['scientific_pass'])+'; real/HERO: '+realstatus+'\n')
    links=[]
    for p in sorted(attempt.rglob('*')):
        if p.is_file() and p.suffix in {'.png','.glb','.json','.npz','.md'} and 'runtime' not in p.relative_to(attempt).parts:
            rel=p.relative_to(attempt).as_posix()
            if p.name in {'request.json','worker.json','payload.json','result.json'}:continue
            href='../'+rel if rel in {'TECHNICAL_REPORT.md','RESULT_CARD.md'} else rel
            links.append('<li><a href="'+html.escape(href,quote=True)+'">'+html.escape(rel)+'</a></li>')
    (attempt/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Actual Mesh/PNG files</title><p>Local file list; no web app. Scientific C0 pass: '+str(metric['scientific_pass'])+'</p><ul>'+''.join(links)+'</ul>')
    return outputs(attempt,dict(status='PASS',scientific_pass=metric['scientific_pass'],scientific_failures=failures,real_status=realstatus,PNG_figures=len(list(fig.glob('*.png')))))
