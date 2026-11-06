"""Reuse all inherited evaluation operators; replace only the list of states."""
from components import *
import evaluate as ev
import ast

def main():
    fr=load(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_EVALUATION.json')
    for a in fr['files']:assert sha(a['path'])==a['sha256'],a['path']
    cfg=load(R/'config/PROTOCOL.json');A=Path(cfg['A_frozen_root']);states={};statuses={}
    for name in['virtual','real']:
        st=[('P0',0,R/'inputs'/name/'INITIAL.npz')]+[('A',n,A/'local_results'/name/'RingAware'/('STEP_%04d.npz'%n))for n in[100,200,300]]
        for arm in['B','C','D']:
            run=load(R/'metrics'/(name+'_'+arm+'_RUN.json'));statuses[(name,arm)]=run
            st += [(arm,n,R/'local_results'/name/arm/('STEP_%04d.npz'%n))for n in cfg['checkpoints']if n>0 and n<=run['accepted_steps']and (R/'local_results'/name/arm/('STEP_%04d.npz'%n)).exists()]
            if run['status']=='STOPPED':
                p=R/'local_results'/name/arm/'LAST_SAFE.npz'
                if p.exists():st.append((arm+'_STOPPED_DIAGNOSTIC',run['accepted_steps'],p))
        states[name]=st
    ev.RUN_STATES=states
    t=ast.parse((R/'code/evaluate.py').read_text());fun=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='evaluate_case')
    for node in fun.body:
        if isinstance(node,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='states'for x in node.targets):node.value=ast.Subscript(value=ast.Name(id='RUN_STATES',ctx=ast.Load()),slice=ast.Name(id='name',ctx=ast.Load()),ctx=ast.Load())
    ast.fix_missing_locations(fun);exec(compile(ast.Module(body=[fun],type_ignores=[]),'inherited_evaluate_case_with_state_list','exec'),ev.__dict__)
    gt=dict(np.load(OLD/'audit_only/NATIVE_CAD_GT.npz'));save('assets_index/POSTERIOR_GT.json',dict(source=asset(OLD/'audit_only/NATIVE_CAD_GT.npz'),frozen_predictions=asset(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_EVALUATION.json'),time=time.time(),GT_used_for_selection=False))
    allg=[];allp=[];deprows=[];hiddenrows=[]
    for name in['virtual','real']:
        geoms,proj=ev.evaluate_case(name,gt if name=='virtual'else None);allg+=geoms;allp+=proj;c=Case(name);dep=Depth(c)
        # Fixed P0 material vertices that were the first surface behind observed Ring.
        v0=c.V;m0=trimesh.Trimesh(c.V,c.F,process=False);body=scene(c.V,c.F);ring=scene(c.ringV,c.ringF);hidden=np.zeros(len(v0),bool)
        for cid in c.fit:
            d=c.views[cid];uv,z,rz=pointcast(ring,v0,d['K'],d['T']);_,_,sz=pointcast(body,v0,d['K'],d['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);inside=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)
            hidden|=inside&(d['labels'][px[:,1],px[:,0]]==2)&(rz<z-.05)&(abs(sz-z)<.05)
        for arm,step,path in states[name]:
            a=np.load(path);m=mesh((a['V']-c.center)/c.scale,a['F']);dep.begin(m)
            for cid in c.views:
                with torch.no_grad():ll,info=dep.loss(m,cid)
                deprows.append(dict(case=name,arm=arm,step=step,role=c.views[cid]['meta']['role'],depth_kind='IDEAL_GT_DEPTH_UPPER_BOUND'if name=='virtual'else'NATIVE_HERO',**info))
            disp=np.einsum('ij,ij->i',a['V']-v0,m0.vertex_normals)
            hiddenrows.append(dict(case=name,arm=arm,step=step,P0_hidden_N=int(hidden.sum()),hidden_material_mean_outward_mm=float(disp[hidden].mean())if hidden.any()else None,hidden_material_absolute_mm=stats(disp[hidden])if hidden.any()else'NOT_EVALUABLE_NO_P0_OCCLUSION',all_material_mean_outward_mm=float(disp.mean()),operator='Same P0 vertex IDs and initial area-weighted normals, not a GT displacement or nearest-surface distance'))
    summary=[]
    for g in allg:
        pp=[p for p in allp if p['case']==g['case']and p['arm']==g['arm']and p['step']==g['step']];dd=[d for d in deprows if d['case']==g['case']and d['arm']==g['arm']and d['step']==g['step']];hh=next(h for h in hiddenrows if h['case']==g['case']and h['arm']==g['arm']and h['step']==g['step'])
        row=dict(case=g['case'],arm=g['arm'],step=g['step'],status='FROZEN_CONTROL'if g['arm']in['A','P0']else statuses.get((g['case'],g['arm']),{}).get('status','STOPPED_DIAGNOSTIC'),fit_IoU=float(np.mean([p['full_Mask_IoU']for p in pp if p['role']=='FIT'])),holdout_IoU=float(np.mean([p['full_Mask_IoU']for p in pp if p['role']!='FIT'])),fit_coverage=float(np.mean([p['coverage']for p in pp if p['role']=='FIT'])),holdout_coverage=float(np.mean([p['coverage']for p in pp if p['role']!='FIT'])),Chamfer_MAE_mm=g.get('Chamfer_mm',{}).get('MAE'),Chamfer_p95_mm=g.get('Chamfer_mm',{}).get('p95'),Chamfer_median_mm=g.get('Chamfer_mm',{}).get('median'),Chamfer_max_mm=g.get('Chamfer_mm',{}).get('maximum'),symmetric_difference_mm3=g.get('symmetric_difference_mm3'),volume_mm3=g['volume_mm3'],volume_ratio_P0=g['volume_ratio_P0'],roughness_p95_deg=g['roughness_normal_angle_deg']['p95'],Ring_collision=g['Ring_collision'],components=g['components'],watertight=g['watertight'],P0_hidden_N=hh['P0_hidden_N'],hidden_material_outward_mm=hh['hidden_material_mean_outward_mm'])
        for role in ['fit','holdout']:
            subset=[d for d in dd if(d['role']=='FIT')==(role=='fit')];N=sum(d['fixed_N']for d in subset);hits=sum(d['mesh_first_hit_N']for d in subset)
            row[role+'_depth_fixed_N']=N;row[role+'_depth_hit_rate']=hits/max(1,N);row[role+'_depth_fixed_loss']=sum(d['depth_loss']*d['fixed_N']for d in subset)/max(1,N);active=sum(d['active_N']for d in subset);row[role+'_depth_conditional_MAE_mm']=sum((d['active_depth_MAE_mm']or 0)*d['active_N']for d in subset)/max(1,active)
        summary.append(row)
    table('metrics/ALL_GEOMETRY.csv',allg);table('metrics/PER_VIEW_METRICS.csv',allp);table('metrics/DEPTH_EVALUATION.csv',deprows);table('metrics/HIDDEN_MATERIAL_DIAGNOSTICS.csv',hiddenrows);save('metrics/SUMMARY.json',summary);table('metrics/SUMMARY.csv',summary)
    endpoints=[r for r in summary if(r['arm']=='P0'or r['step']==300)]
    for(name,arm),run in statuses.items():
        if run['status']!='COMPLETED':endpoints.append(dict(case=name,arm=arm,step=run['accepted_steps'],status='STOPPED_FINAL_NOT_EVALUABLE',fit_IoU=None,holdout_IoU=None,Chamfer_MAE_mm=None,symmetric_difference_mm3=None,volume_mm3=None))
    save('metrics/ENDPOINTS.json',endpoints);table('metrics/ENDPOINTS.csv',endpoints)
    print('All common geometry/depth operators evaluated after freeze',flush=True)
if __name__=='__main__':main()
