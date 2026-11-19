"""Static data-driven failure evidence; no GT shape or training data fallback."""
from pathlib import Path
import csv
import json
import sys
import platform
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import cKDTree
import pipeline as p
from ring_first_3d.mainline.native.camera import observe,torus_contours
from ring_first_3d.mainline.native.io import save_json,sha256

T=p.TASK;R=p.ROOT
plt.rcParams.update({'font.size':9,'figure.dpi':110,'savefig.dpi':130})

def load_records():
    rows=[]
    for v in p.read(T/'audit/SELECTED_VIEWS.json'):
        m=v['meta'];d=T/'runs'/m['case']/m['video']/'camera'/m['id']
        a=p.read(d/'ADMISSION.json');r=p.read(d/'CAMERA_RESULT.json') if (d/'CAMERA_RESULT.json').exists() else {}
        rows.append(dict(group=m['case'],video=m['video'],id=m['id'],role='FIT' if m['role']=='FIT' else 'HOLDOUT',candidate_source=r.get('candidate_source','EXECUTION_ERROR'),source_gate='PASS' if r.get('candidate_source')=='originalRF5DoF_RGB_yaw' else 'FAIL',admission=a['status'],ring_MAE_px=r.get('ring_boundary_MAE_px'),ring_p95_px=r.get('ring_boundary_p95_px'),seconds=a['seconds'],result=str(d/'CAMERA_RESULT.json'),admission_path=str(d/'ADMISSION.json'),view=v,data=r))
    return rows

def camera_panels(row,axes):
    a=p.check_input(row['view']);r=row['data'];rgb=a['RGB'];lab=a['labels'];ob=observe(lab)
    curves=torus_contours(np.asarray(r['c2w_mm']),a['K'])
    axes[0].imshow(rgb);axes[0].contour(lab==2,levels=[.5],colors=['cyan'],linewidths=.7)
    for q in curves:axes[0].plot(q[:,0],q[:,1],color='yellow',linewidth=.8)
    axes[0].set_title(f"{row['id']} ({row['role']})\nCyan: observed Ring; yellow: diagnostic CAD")
    axes[1].imshow(rgb,alpha=.4)
    q=ob['q_train'];d=cKDTree(curves.reshape(-1,2)).query(q)[0]
    s=axes[1].scatter(q[:,0],q[:,1],c=d,s=9,cmap='magma',vmin=0,vmax=6)
    u=ob['unknown_boundary']
    if len(u):axes[1].scatter(u[:,0],u[:,1],s=3,c='magenta',label='Ring/Polyp unknown')
    axes[1].set_title(f"Boundary MAE {row['ring_MAE_px']:.3f}px; P95 {row['ring_p95_px']:.3f}px\nMagenta: excluded contact boundary")
    for ax in axes:
        ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_xlabel('u [px]');ax.set_ylabel('v [px]')
    return s

def body_plot(ax,V,F,title,limits):
    ax.add_collection3d(Poly3DCollection(V[F],facecolor='#8855aa',edgecolor='none',alpha=.8,rasterized=True))
    for name,lim in zip(['x','y','z'],limits):getattr(ax,'set_'+name+'lim')(lim);getattr(ax,'set_'+name+'label')(name+' [mm]')
    ax.set_box_aspect([b-a for a,b in limits]);ax.view_init(20,-65);ax.set_title(title)

def figures(rows):
    for row in rows:
        f,axes=plt.subplots(1,2,figsize=(12,4));s=camera_panels(row,axes);f.colorbar(s,ax=axes.ravel().tolist(),label='Observed Ring -> CAD [px]',shrink=.7)
        f.suptitle(f"DIAGNOSTIC ONLY | selected {row['candidate_source']} | admission {row['admission']}\nInput {row['view']['cache']['sha256'][:16]} | no camera fallback",fontsize=10)
        out=T/'figures'/row['group']/row['video'];out.mkdir(parents=True,exist_ok=True)
        f.savefig(out/(row['id']+'_RingFirst.png'),bbox_inches='tight');plt.close(f)
    for c in p.cases():
        group=c['case'];sub=[r for r in rows if r['group']==group]
        fig,axes=plt.subplots(2,2,figsize=(13,8))
        for i,video in enumerate(['004','005']):
            selected=[r for r in sub if r['video']==video and r['role']=='FIT'][4]
            camera_panels(selected,axes[i])
        fig.suptitle(group+': frozen FIT index 4, both videos; all displayed cameras inadmissible')
        d=T/'figures'/group;fig.tight_layout();fig.savefig(d/'Figure1_RingFirst.png');plt.close(fig)
        fig=plt.figure(figsize=(12,5));ax=fig.add_subplot(121,projection='3d');th=np.linspace(0,2*np.pi,129)
        ax.plot(5.6*np.cos(th),5.6*np.sin(th),np.zeros_like(th),color='black',label='R10 centreline')
        positions=[]
        for video,color in [('004','red'),('005','blue')]:
            ss=[r for r in sub if r['video']==video];C=np.array([r['data']['c2w_mm'] for r in ss]);positions.extend(C[:,:3,3])
            ax.scatter(*C[:,:3,3].T,c=color,label=video+' diagnostic')
            for cam in C:
                z=cam[:3,3];end=z+3*cam[:3,2];ax.plot(*np.c_[z,end],color=color,linewidth=.5)
        xyz=np.r_[np.asarray(positions),[[0,0,0]]];ctr=(xyz.min(0)+xyz.max(0))/2;extent=max(np.ptp(xyz,axis=0).max()/2,8)*1.05
        for k,v in enumerate('xyz'):getattr(ax,'set_'+v+'lim')((ctr[k]-extent,ctr[k]+extent));getattr(ax,'set_'+v+'label')(v+' [mm]')
        ax.set_box_aspect((1,1,1));ax.view_init(20,-60);ax.legend();ax.set_title(group+' actual diagnostic camera distribution\nRGB-map-conditioned; not certified metric pose truth')
        ax=fig.add_subplot(122);source=['originalRF5DoF_RGB_yaw','REAL_RGB_PNP_LM','RING_ONLY_YAW_UNRESOLVED']
        for i,role in enumerate(['FIT','HOLDOUT']):
            ax.bar(np.arange(3)+i*.35,[sum(r['role']==role and r['candidate_source']==s for r in sub) for s in source],width=.35,label=role)
        ax.set_xticks(np.arange(3)+.175,['Ring5DoF+RGB yaw','PnP winner (forbidden)','Unresolved yaw'],rotation=15);ax.set_ylabel('Fixed views');ax.legend();ax.set_title('Original winner kept; no second-best reselection')
        fig.tight_layout();fig.savefig(d/'Figure1_CameraDistribution.png');plt.close(fig)
        initial=dict(np.load(c['initial']['path']));V=initial['V'];F=initial['F_solid'];xyz=V;centre=(xyz.max(0)+xyz.min(0))/2;extent=np.ptp(xyz,axis=0).max()*.65;lims=[(x-extent,x+extent) for x in centre]
        fig=plt.figure(figsize=(15,5));ax=fig.add_subplot(131,projection='3d');body_plot(ax,V,F,'B0: actual EXACT013 Initial',lims)
        for j,name in [(2,'B1 contour-only'),(3,'B2 contour+depth')]:
            ax=fig.add_subplot(1,3,j);ax.axis('off');ax.text(.5,.6,name+'\nNOT_RUN',ha='center',va='center',fontsize=18,color='firebrick');ax.text(.5,.35,'0/16 FIT camera winners admitted by source gate\nNo trained Mesh or GT benefit is claimed',ha='center',va='center')
        fig.suptitle(group+' | B0 SHA '+c['initial']['sha256'][:16]+' | no GT geometry read');fig.tight_layout();fig.savefig(d/'Figure3_BodyAbalation_NOT_RUN.png');plt.close(fig)
        import trimesh
        model=T/'runs'/group/'B0';model.mkdir(exist_ok=True)
        trimesh.Trimesh(V,F,process=False).export(model/'INITIAL.ply')
        save_json(model/'IDENTITY.json',dict(source=c['initial'],mesh=str(model/'INITIAL.ply'),export_sha256=sha256(model/'INITIAL.ply'),unit='mm',vertex_max_abs_delta_mm=0,optimized=False,GT_geometry_read=False))
        for num,label in [(2,'HERO'),(4,'FIT_HOLDOUT_Projection'),(5,'3D_Comparison'),(6,'Local_Structure')]:
            fig,ax=plt.subplots(figsize=(10,3));ax.axis('off');ax.text(.5,.7,f'{group} Figure {num}: {label} — NOT_RUN',ha='center',fontsize=17,color='firebrick');ax.text(.5,.4,'Upstream blocker: no legal FIT Ring-First winner.\nHistorical HERO/PnP cameras and B0 copies cannot substitute for new results.\nSee Figure 1, per-frame diagnostic PNGs, and PIPELINE_COMPLETENESS.csv.',ha='center',fontsize=11)
            fig.savefig(d/f'Figure{num}_{label}_NOT_RUN.png',bbox_inches='tight');plt.close(fig)

def summary(rows):
    p.table(T/'metrics/CAMERA_METRICS.csv',[{k:v for k,v in r.items() if k not in ['view','data']} for r in rows])
    cells=[];compact=[];failures=[];metrics=[]
    for c in p.cases():
        for video in ['004','005']:
            ss=[r for r in rows if r['group']==c['case'] and r['video']==video];fit=[r for r in ss if r['role']=='FIT'];held=[r for r in ss if r['role']=='HOLDOUT']
            counts={s:sum(r['candidate_source']==s for r in ss) for s in sorted({r['candidate_source'] for r in ss})}
            status='FAIL';reason=f"0/{len(fit)} FIT winners from permitted RF5DoF+RGB yaw; original candidates {counts}"
            compact.append(dict(Group=c['case'],Video=video,**{'Ring-First':'FAIL','HERO':'NOT_RUN','PyTorch3D':'NOT_RUN','Contour':'NOT_RUN','Contour+Depth':'NOT_RUN'},FIT=len(fit),HOLDOUT=len(held),reason=reason,evidence=str(T/'metrics/CAMERA_METRICS.csv')))
            for stage in ['Ring-First','HERO','PyTorch3D','Contour','Contour+Depth']:
                cells.append(dict(Group=c['case'],Video=video,Stage=stage,Status='FAIL' if stage=='Ring-First' else 'NOT_RUN',Inputs=str(T/'audit/INPUT_MANIFEST.csv'),Outputs=str(T/'runs'/c['case']/video/'camera') if stage=='Ring-First' else '',SourceVersion=str(T/'audit/SOURCE_LOCK.json'),Log=str(T/'logs/CAMERA_RUN.log'),Evidence=str(T/'metrics/CAMERA_METRICS.csv'),Reason=reason if stage=='Ring-First' else 'UPSTREAM_RING_FIRST_SOURCE_GATE_FAILED; no substitution allowed'))
            failures.append(dict(id=c['case']+'_'+video+'_CAMERA_SOURCE',kind='INPUT_PROVENANCE_OR_METHOD_SELECTION_FAILURE',group=c['case'],video=video,symptom=reason,confirmed_cause='Original frozen candidate comparison chooses pure PnP for mapped FIT views; other FIT views have no same-video map and unresolved yaw.',code_bug=False,scientific_depth_negative_result=False,repair='A separately authorized Ring-First-only selection protocol or a verified same-video RGB yaw calibration is needed; do not change winner silently.',regression_tests=str(T/'tests/test_contracts.py'),evidence=[r['admission_path'] for r in ss],permanent_rule_promotion='NOT_REVIEWED',historical_fallback_count=0))
            for arm in ['B0','B1','B2']:
                metrics.append(dict(group=c['case'],video=video,arm=arm,status='PASS' if arm=='B0' else 'NOT_RUN',initial_identity='EXACT_013_INPUT_MESH_V_F_SOLID_CAP',FIT_IoU='NaN',HOLDOUT_IoU='NaN',Boundary_Chamfer_px='NaN',strict_3D_IoU='NaN',strict_IoU_validity='NOT_EVALUATED',conditional_occupancy_IoU='NaN',GT_MAE_mm='NaN',GT_P95_mm='NaN',Fscore_0_5mm='NaN',HERO_MAE_mm='NaN',HERO_P95_mm='NaN',HERO_coverage='NaN',depth_views=0,vertex_displacement_MAE_mm=0 if arm=='B0' else 'NaN',vertex_displacement_P95_mm=0 if arm=='B0' else 'NaN',reason='B0 identity/export verified; no trained prediction exists and no GT comparison run' if arm=='B0' else 'UPSTREAM_RING_FIRST_SOURCE_GATE_FAILED'))
    p.table(T/'report/PIPELINE_COMPLETENESS.csv',compact);p.table(T/'report/PIPELINE_STAGE_RECORDS.csv',cells);p.table(T/'metrics/BODY_METRICS.csv',metrics)
    save_json(T/'FAILURE_REGISTRY.json',dict(schema='task_local_failure_records_v1',task_id=T.name,permanent_rules_changed=False,failures=failures))
    lines=['# 标准流程验收','', '| Group | Video | FIT/HOLDOUT | Ring-First | HERO | PyTorch3D | Contour | Contour+Depth |','|---|---|---|---|---|---|---|---|']
    for r in compact:lines.append(f"| {r['Group']} | {r['Video']} | {r['FIT']}/{r['HOLDOUT']} | FAIL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |")
    lines+=['','所有阶段的输入、源码、日志及证据见 [PIPELINE_STAGE_RECORDS.csv](PIPELINE_STAGE_RECORDS.csv)。没有科研计算阶段被标记 PASS。B0 身份核验不代表主体优化通过。']
    (T/'report/PIPELINE_COMPLETENESS.md').write_text('\n'.join(lines)+'\n')
    save_json(T/'metrics/SUMMARY.json',dict(groups=5,videos=10,views=len(rows),FIT=sum(r['role']=='FIT' for r in rows),HOLDOUT=sum(r['role']=='HOLDOUT' for r in rows),candidate_sources={s:sum(r['candidate_source']==s for r in rows) for s in sorted({r['candidate_source'] for r in rows})},FIT_allowed_source=sum(r['role']=='FIT' and r['source_gate']=='PASS' for r in rows),HOLDOUT_allowed_source=sum(r['role']=='HOLDOUT' and r['source_gate']=='PASS' for r in rows),admitted_frames=sum(r['admission']=='PASS' for r in rows),camera_execution_seconds=sum(r['seconds'] for r in rows),HERO_inferences=0,trained_B1=0,trained_B2=0,GT_shapes_read=0,historical_fallback=0))

if __name__=='__main__':
    p.verify_freeze();rows=load_records();assert len(rows)==105
    assert not any(r['role']=='FIT' and r['source_gate']=='PASS' for r in rows),'New admissible FIT input needs scientific continuation, not a failure report'
    summary(rows);figures(rows);print('SUMMARY_AND_STATIC_FIGURES_COMPLETE',len(rows),flush=True)
