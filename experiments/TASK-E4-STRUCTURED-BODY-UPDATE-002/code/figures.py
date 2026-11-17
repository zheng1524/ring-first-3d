"""Measured full-triangle geometry and native-pixel evidence; offline review only."""
from pathlib import Path
import html,json,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection
from common import load_case,dump
from pipeline import read,PREVIOUS
from ring_first_3d.synthetic.io import fetch,outputs
from ring_first_3d.policy.contracts import require
from ring_first_3d.multisurface.geometry import mesh_sections as section

COLORS=['#999999','#e0923a','#2187bc','#8834b8']
def mesh(ax,b,c,alpha=.6,values=None):
    q=b['V'][b.get('F_solid',b['F'])];p=Poly3DCollection(q,alpha=alpha,linewidths=0)
    p.set_facecolor(c if values is None else plt.cm.inferno(np.clip(values,0,1)));ax.add_collection3d(p)

def bounds(ax,lo,hi,elev=20,azim=-65):
    for setter,a,b in zip([ax.set_xlim,ax.set_ylim,ax.set_zlim],lo,hi):setter(a,b)
    ax.set_box_aspect(hi-lo);ax.view_init(elev,azim);ax.set_xlabel('x mm',fontsize=7);ax.set_ylabel('y mm',fontsize=7);ax.set_zlabel('z mm',fontsize=7);ax.tick_params(labelsize=6)

def save(fig,path):fig.savefig(path,dpi=125,bbox_inches='tight');plt.close(fig)
def visualize(task,attempt):
    root=attempt.parents[1];ep=fetch(root,'G2_evaluate','EVALUATION.json');ev=read(ep);failure=read(fetch(root,'G2_evaluate','FAILURE_REGISTRY.json'));figdir=attempt/'figures';figdir.mkdir();shutil.copyfile(fetch(root,'G2_evaluate','FAILURE_REGISTRY.json'),attempt/'FAILURE_REGISTRY.json');summary=ev['summary'];pages=[];viewchanges=[]
    for case in task['structured']['cases']:
        initial,views,ring,base,chart,source=load_case(case);predpath=fetch(root,'G1_'+case,'BODY_PREDICTIONS_FROZEN.json');records=read(predpath)['records'];models=[initial,dict(np.load(PREVIOUS/case/'DEFORM_GROW/FINAL.npz'))];arms=['INITIAL','PREVIOUS_DEFORM_GROW'];locations={}
        for r in records:
            if r['status']=='NUMERIC':
                p=fetch(root,'G1_'+case,r['mesh_relative']);locations[r['arm']]=p.parent;models.append(dict(np.load(p)));arms.append(r['arm'])
        VV=np.concatenate([m['V']for m in models]+[ring['V']]);lo=VV.min(0)-.5;hi=VV.max(0)+.5
        fig=plt.figure(figsize=(15,7))
        for row,(elev,azi)in enumerate([(20,-65),(10,25)]):
            for j,(arm,b)in enumerate(zip(arms,models)):
                ax=fig.add_subplot(2,4,row*4+j+1,projection='3d');mesh(ax,b,COLORS[j]);mesh(ax,ring,'black',.35);bounds(ax,lo,hi,elev,azi);r=next(x for x in summary if x['case']==case and x['arm']==arm);ax.set_title(f'{arm}\nFIT {r["FIT_IoU"]:.3f} / HOLDOUT {r["HOLDOUT_IoU"]:.3f}',fontsize=8)
        fig.suptitle(f'{case} | actual full triangles | fixed metric camera and mm limits | no HERO');save(fig,figdir/(case+'_BODY.png'))
        fig=plt.figure(figsize=(14,4))
        for j,(arm,b)in enumerate(zip(arms,models)):
            ax=fig.add_subplot(1,4,j+1,projection='3d');aligned=dict(np.load(ep.parent/case/(arm+'_GT_ALIGNED.npz')));gt=dict(np.load(ep.parent/case/'GT.npz'));mesh(ax,gt,'gray',.18);mesh(ax,aligned,COLORS[j],.75);allv=np.r_[gt['V'],*[dict(np.load(ep.parent/case/(a+'_GT_ALIGNED.npz')))['V']for a in arms]];bounds(ax,allv.min(0)-.3,allv.max(0)+.3);r=next(x for x in summary if x['case']==case and x['arm']==arm);ax.set_title(f'{arm}\nMAE {r["GT_MAE_mm"]:.3f} p95 {r["GT_p95_mm"]:.3f} mm',fontsize=8)
        fig.suptitle(case+' | scale-fixed true SE(3) GT registration; evaluation copies only');save(fig,figdir/(case+'_GT.png'))
        # Every retained FIT view, actual pixels and accepted/rejected Face-linked evidence.
        case_rows=[r for r in ev['rows']if r['case']==case];initialrow=next(r for r in case_rows if r['arm']=='INITIAL');index={r['id']:r for r in initialrow['projection']}
        for arm,folder in locations.items():
            fig=plt.figure(figsize=(11,4));g=np.load(folder/'STEP_035/GRAPH.npz');R=g['rotation'];t=g['translation'];nodes=g['nodes'];edge=g['edges'];ax=fig.add_subplot(121,projection='3d');mesh(ax,initial,'gray',.2);ax.add_collection3d(Line3DCollection(nodes[edge],colors='gray',linewidths=.7));ax.scatter(*nodes.T,c=np.linalg.norm(t,axis=1),cmap='viridis',s=18);ax.quiver(*nodes.T,*t.T,color='red',normalize=False);bounds(ax,lo,hi);ax.set_title('32 geodesic nodes; actual translations (mm)',fontsize=9);ax=fig.add_subplot(122);ax.plot(np.linalg.norm(t,axis=1),label='translation mm');ax.plot(np.rad2deg(np.linalg.norm(R,axis=1)),label='rotation deg');ax.legend();ax.set_xlabel('control node ID');save(fig,figdir/(case+'_'+arm+'_GRAPH.png'))
            for v in [v for v in views if v['role']=='FIT']:
                old=np.load(folder/'INITIAL_PAIRS'/(v['id']+'.npz'));new=np.load(folder/'FINAL_PAIRS'/(v['id']+'.npz'));fig,axes=plt.subplots(1,4,figsize=(13,3));axes[0].imshow(v['RGB']);axes[0].contour(v['labels']==1,levels=[.5],colors=['lime'],linewidths=.7);axes[0].contour(v['labels']==2,levels=[.5],colors=['black'],linewidths=.7);axes[0].set_title('RGB / real Polyp + Ring Mask',fontsize=7)
                for ax,data,title in zip(axes[1:3],[old,new],['INITIAL: R+ red / R- blue',arm+': fresh correspondences']):
                    rgb=np.zeros((*v['labels'].shape,3));rgb[data['R_plus']]=[1,.2,.1];rgb[data['R_minus']]=[.1,.4,1];rgb[data['unknown']]=[.35,.35,.35];ax.imshow(rgb);ax.contour(data['predicted'],levels=[.5],colors=['white'],linewidths=.4);ax.set_title(title,fontsize=7)
                accepted=new['accepted'];uv=new['source_uv'];q=new['target_uv'];pick=np.flatnonzero(accepted)[::max(1,int(accepted.sum()/25))];axes[2].add_collection(LineCollection(np.stack([uv[pick],q[pick]],1),colors='lime',linewidths=.6));bad=np.flatnonzero(~accepted)[::max(1,int((~accepted).sum()/100))];axes[2].scatter(*uv[bad].T,s=1,c='yellow');axes[3].imshow(new['visible_face'],cmap='tab20');axes[3].set_title('Actual visible Face ID / bary saved',fontsize=7)
                for ax in axes:ax.set_axis_off()
                fig.suptitle(f'{case} {v["id"]} {v["video"]} | white projected boundary; gray unknown; green accepted, yellow rejected',fontsize=9);save(fig,figdir/(case+'_'+arm+'_'+v['id']+'_CONTOUR.png'))
            # Fixed probe heat maps and measured non-regression.
            c=np.load(folder/'RING_FINAL.npz');b=next(m for a,m in zip(arms,models)if a==arm);fig=plt.figure(figsize=(11,4));mx=max(float(c['body_penetration'].max()),.001);ax=fig.add_subplot(121,projection='3d');mesh(ax,b,'gray',.8,values=c['body_penetration'].max(1)/mx);mesh(ax,ring,'black',.3);bounds(ax,lo,hi);ax.set_title(f'Body -> Ring penetration; common scale 0..{mx:.4f} mm',fontsize=8);ax=fig.add_subplot(122);oldc=np.load(folder/'RING_INITIAL.npz');ax.plot(oldc['ring_penetration'].max(1),label='initial');ax.plot(c['ring_penetration'].max(1),label='final');ax.set_ylabel('Ring -> Body penetration mm');ax.set_xlabel('fixed CAD material face');ax.legend();save(fig,figdir/(case+'_'+arm+'_RING.png'))
            row=next(r for r in case_rows if r['arm']==arm);delta=[];boundary=[];labels=[]
            for p in row['projection']:
                if p['role']!='FIT':continue
                a=index[p['id']];delta.append(p['IoU']-a['IoU']);boundary.append(p['Boundary_MAE_px']-a['Boundary_MAE_px']);labels.append(p['id']);viewchanges.append(dict(case=case,arm=arm,id=p['id'],video=p['video'],protected=a['IoU']>=.8,IoU_delta=delta[-1],Boundary_delta_px=boundary[-1]))
            fig,axes=plt.subplots(2,1,figsize=(13,5),sharex=True);axes[0].bar(range(len(delta)),delta,color=['green'if z>=0 else'red'for z in delta]);axes[0].axhline(-.01,color='black',linestyle='--');axes[0].set_ylabel('IoU change');axes[1].bar(range(len(delta)),boundary);axes[1].axhline(1,color='black',linestyle='--');axes[1].set_ylabel('Boundary MAE change px');axes[1].set_xticks(range(len(labels)),labels,rotation=65,fontsize=5);fig.suptitle(case+' '+arm+' | every original FIT retained');save(fig,figdir/(case+'_'+arm+'_PER_VIEW.png'))
            updates=read(folder/'UPDATES.json');proposals=sorted(folder.glob('GROWTH_PROPOSAL_*/SWEEP.npz'));accepted_sweep=folder/'STEP_035/SWEEP.npz'
            sweepfile=accepted_sweep if accepted_sweep.exists()else(proposals[0]if proposals else None)
            fig=plt.figure(figsize=(12,4))
            if sweepfile is not None:
                sw=np.load(sweepfile);candidate=dict(np.load(sweepfile.with_name('BODY.npz')));C=sw['centerline'];aa=sw['axes'];length=np.linalg.norm(np.diff(C,axis=0),axis=1).sum();ax=fig.add_subplot(131,projection='3d');mesh(ax,candidate,'purple',.3);ax.plot(*C.T,c='black',marker='.',ms=2);bounds(ax,lo,hi);ax.set_title(f'Actual sweep; length {length:.3f}mm\n'+('ACCEPTED'if accepted_sweep.exists()else'REJECTED proposal'),fontsize=8);ax=fig.add_subplot(132);ax.plot(2*aa[:,0],label='major diameter mm');ax.plot(2*aa[:,1],label='minor diameter mm');ax.legend(fontsize=7);ax.set_xlabel('spline station');ax=fig.add_subplot(133,projection='3d');mesh(ax,candidate,'purple',.3);rim=candidate['V'][sw['root_loop']];ax.plot(*np.r_[rim,rim[:1]].T,color='orange',marker='.',ms=3);bounds(ax,np.r_[rim,C[:4]].min(0)-.3,np.r_[rim,C[:4]].max(0)+.3);ax.set_title('Shared original rim IDs / transition',fontsize=8)
            else:
                ax=fig.add_subplot(111);ax.axis('off');diagnostics=[dict(iteration=e['iteration'],status=e['status'],support_rows=e['support_rows'],eligible_patches=e['eligible_patches'],rejection_reasons=sorted({x for d in e['seed_diagnostics']for x in d['rejections']}))for e in updates['growth']];ax.text(.02,.95,'NO ACCEPTED OR FEASIBLE SWEEP\n'+json.dumps(diagnostics,indent=2),va='top',family='monospace',fontsize=8)
            fig.suptitle(case+' '+arm+' | multiview evidence-driven growth; no forced structure');save(fig,figdir/(case+'_'+arm+'_SWEEP.png'))
        # Actual triangle sections show shape changes, never sampled average contours.
        fig,axes=plt.subplots(1,4,figsize=(14,4));center=initial['V'].mean(0)
        for j,(axis,offset)in enumerate([(0,-.5),(0,.5),(2,-.5),(2,.5)]):
            value=center[axis]+offset;keep=[x for x in range(3)if x!=axis]
            for arm,b,c in zip(arms,models,COLORS):
                from ring_first_3d.multisurface.geometry import mesh_sections as section as cut
                seg=cut(b['V'],b['F_solid'],axis,value)
                if len(seg):axes[j].add_collection(LineCollection(seg[:,:,keep],colors=c,linewidths=.8,label=arm))
            axes[j].set_xlim(lo[keep[0]],hi[keep[0]]);axes[j].set_ylim(lo[keep[1]],hi[keep[1]]);axes[j].set_aspect('equal');axes[j].set_title(f'{"xyz"[axis]}={value:.2f}mm');axes[j].set_xlabel('mm');axes[j].set_ylabel('mm')
        axes[0].legend(fontsize=6);fig.suptitle(case+' | all full-triangle plane intersections, common metric extents');save(fig,figdir/(case+'_SECTIONS.png'));pages.append(case)
    dump(attempt/'SUMMARY.json',dict(body_metrics=summary,per_view_changes=viewchanges,failures=failure['records'],scientific_pass_not_assumed=True));write_reports(task,attempt,summary,viewchanges,failure)
    images=sorted(figdir.glob('*.png'));lines=['<!doctype html><meta charset="utf-8"><title>Structured Body Update 002</title><style>body{font-family:sans-serif;max-width:1500px;margin:auto}img{max-width:100%}details{margin:1em}a{padding:.4em}</style><h1>Structured Body Update 002</h1><p><a href="../RESULT_CARD.md">Result card</a> <a href="../TECHNICAL_REPORT.md">Technical report</a></p><p>Actual real G01/G03/G05 Mesh and native observations. No HERO. Gray unknown regions are excluded; rejected candidates remain visible. All GT fits affect evaluation copies only.</p>']
    for case in pages:
        lines+=['<h2>'+case+'</h2>',f'<img src="figures/{case}_BODY.png">',f'<img src="figures/{case}_GT.png">']
        for p in images:
            if p.name.startswith(case)and not p.name.endswith(('_BODY.png','_GT.png')):lines.append(f'<details><summary>{html.escape(p.stem)}</summary><img loading="lazy" src="figures/{p.name}"></details>')
    (attempt/'index.html').write_text('\n'.join(lines));return outputs(attempt,dict(status='PASS',scientific_failures=failure['records'],cases=3,figures=len(images),GT_used_for_evaluation_only=True))

def write_reports(task,attempt,rows,changes,failure):
    tab=['|case|arm|FIT IoU|HOLDOUT IoU|GT Chamfer MAE mm|GT p95 mm|coverage@0.5|growth length mm|','|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['status']=='NUMERIC':tab.append(f'|{r["case"]}|{r["arm"]}|{r["FIT_IoU"]:.5f}|{r["HOLDOUT_IoU"]:.5f}|{r["GT_MAE_mm"]:.5f}|{r["GT_p95_mm"]:.5f}|{r["GT_coverage_0p5mm"]:.5f}|{r["growth_length_mm"]:.4f}|')
        else:tab.append(f'|{r["case"]}|{r["arm"]}|NaN|NaN|NaN|NaN|NaN|NaN|')
    by={(r['case'],r['arm']):r for r in rows};conclusions=[]
    for c in task['structured']['cases']:
        old=by[c,'INITIAL'];prev=by[c,'PREVIOUS_DEFORM_GROW']
        for a in task['structured']['arms']:
            r=by[c,a]
            if r['status']!='NUMERIC':continue
            cc=[v for v in changes if v['case']==c and v['arm']==a];degraded=[v['id']for v in cc if v['IoU_delta']<0];bad=[v for v in cc if v['protected']and(v['IoU_delta']<-.01000001 or v['Boundary_delta_px']>1.00000001)]
            conclusions.append(f'{c} {a}: accepted {r["accepted_updates"]}/36; FIT ΔIoU={r["FIT_IoU"]-old["FIT_IoU"]:+.6f}; HOLDOUT ΔIoU={r["HOLDOUT_IoU"]-old["HOLDOUT_IoU"]:+.6f}; GT ΔMAE={r["GT_MAE_mm"]-old["GT_MAE_mm"]:+.6f}mm vs INITIAL, {r["GT_MAE_mm"]-prev["GT_MAE_mm"]:+.6f}mm vs previous; {r["growth_status"]}. Protected violations {len(bad)}. Degraded FIT IDs: {", ".join(degraded)or"none"}.')
    audit='''|审计项目|必须汇报|
|---|---|
|目标组数|3 physical groups; 6 independent predictions, 2 arms each|
|本算法独立成功|Numeric output counts below; numeric output is not scientific success|
|本算法失败|All failed arms NaN; scientific no-gain cases retained in Failure Registry|
|历史测量值回退|0; previous Mesh only independent evaluation control|
|失败组及具体原因|FAILURE_REGISTRY.json and full UPDATES.json candidate gates|
|最终统计样本|All 3 groups per arm; paired comparisons use same groups; no diameter measurement|
|是否使用 GT 选择算法|No. Config/code frozen before all real predictions, GT first opened G2 after all freezes|
'''
    text='\n'.join(['# TASK-E4-STRUCTURED-BODY-UPDATE-002','', 'Real-only fixed 36-outer pilot; no HERO relocation. Predictions remain in Ring-First mm coordinates. GT unknown deployment is handled by actual fixed-scale SE(3) fits on evaluation copies. Shape changes do not establish real-world absolute position.','',*conclusions,'','## Initialization and isolation','Exact same previous initialize() function and EXACT_013_INPUT_MESH_V_F_SOLID_CAP assets. Identity Ring->same Ring deterministic adapter. No E1/E2, no GT initial shape, no HERO depth, no DXY edits. All original FIT views and exact balanced weights retained; HOLDOUT final evaluation only. Input/config/code SHA256 in inputs locks and TASK_FREEZE. Initial cap-node graph transforms preserve inherited base chart; no individual vertex optimization.','', '## Structured optimizer and mathematics','32 intrinsic geodesic FPS nodes; 4 neighboring graph nodes and 4 geodesic vertex influences. v′=Σw[R_j(v−g_j)+g_j+t_j], R=exp(skew(ω)). Core variables are node ω,t, plus optional cubic spline controls and independent softplus axis controls. Same Adam and line-search budget for both arms.','Smooth ARAP follows Oehri et al.2025 Eq1–5: cotangent L, mixed Voronoi A, ell=M^-1 LV, triangle spokes-and-rims cot(edge)/3 energies, edge-only proper SVD local rotations, E_smooth=ΣA||ell′−R ell||²; lambda=.7. Alternating local rotations frozen during PyTorch graph global steps. This is graph-parameterized SARAP, not the paper unrestricted vertex linear solver. Raw metric Voronoi areas follow paper; inspected author C++ uses mean-normalized mass, so no claim of literal C++ numerical replication. SARAP normalized by total metric area in combined loss.','https://arxiv.org/html/2501.10335v1 ; https://github.com/oehria/smooth-arap','Robust paired normal + bilinear SDF residuals use frozen ExplicitContour bidirectionality, exact mutual NN, normal compatibility, tangent<=8px, distance<=40px, visible Face/bary, 3px Ring unknown. Mask region IoU/boundary is an independent hard acceptance constraint, not a free 2D warp. Far R+ retained only as growth evidence. Every trial fresh-renders all FIT, rebuilds all correspondences, and checks regional objective, pair coverage and full FIT loss. Initial valid IoU>=.80 views allow at most -.01 IoU and +1px Boundary MAE.','Sweep uses cubic 5-control B-spline, 16x16 elliptical stations, independent softplus axes, Wang2008 Double Reflection RMF, connected actual original rim vertex IDs, interpolated polygon-to-ellipse transition, root normal loss, continuous tip fan. At least3 FIT/two videos plus Jacobian rank and consistent residual explanation required; uniform bounds: radius>=.05mm, <=fixed max; length<=6mm. No single translated patch extrusion, no floating shell. Rejected actual proposals and seed diagnostics retained. https://www.ag.jku.at/pubs/2007wjzl.pdf','RingCollisionGate is detached acceptance only; seven fixed barycentric probes per original material face and per CAD face; repeat-query/float32 ULP tolerance frozen. Both Body->Ring and Ring->Body compared against current AND initial. New root inherits attachment provenance; non-root new penetration forbidden. Existing penetration is allowed if unchanged or reduced. Discrete sampled gate does not certify continuous collision absence; exact mesh intersections checked separately. No Ring optimization gradient.','', '## Metrics (fixed 12000 material surface samples per direction)','Surface metrics evaluate actual triangles, GT rigid alignment scale1; FIT/HOLDOUT means use unchanged full view denominators. Chamfer here is symmetric unsquared point-to-triangle distance. No occupancy IoU claim; no diameter/MRE because this is a shape update task.',*tab,'','## Projection / geometry / failures','Full per-view protected outcomes, topology, self-intersections, flip checks and Ring areas/energy in metrics CSV; all accepted/rejected candidate views/gates in immutable UPDATES. Growth metrics with no accepted sweep are 0 (not a fabricated recovery). No inferred stalk length when evidence underconstrained. Scientific negative results do not automatically become permanent rules.','',audit,'Numeric independent predictions: '+str(sum(r['status']=='NUMERIC'and r['arm']in task['structured']['arms']for r in rows))+'/6.','Failure ledger: '+json.dumps(failure['records'],ensure_ascii=False),'','## Review paths','visualization/index.html and actual PNG evidence; immutable runs contain complete INITIAL/early/mid/final meshes, Face/bary/R+/R− maps, graph/Sweep parameters, and GT registration copies. Source origins frozen in input manifest. No GT checkpoint selection; final36 frozen. Scientific conclusions above must be read per group, not inferred from prettier projections.'])
    (attempt/'TECHNICAL_REPORT.md').write_text(text+'\n');(attempt/'RESULT_CARD.md').write_text('# RESULT_CARD\n\n'+'\n\n'.join(conclusions)+'\n\n'+ '\n'.join(tab)+'\n\nNumeric output is separate from scientifically improved geometry. No HERO stage executed.\n')
