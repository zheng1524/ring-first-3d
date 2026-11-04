"""Fixed-denominator read-only evaluation after every registered arm stops."""
from inputs import *
from physical import volume
from data import Data
from scipy.spatial import cKDTree
from legacy_mesh import laplace

def absolute_stats(x):
    s=stats(x);s['median_absolute']=float(np.median(abs(x)))if len(x)else None;return s

def stage_status(row):
    status=row['status'];x=row.get('extra')or{}
    if status=='BUDGET_COMPLETED'and x.get('attempted_iterations',0)<x.get('budget_iterations',0):return 'TRUST_REGION_NUMERICAL_LIMIT_PARTIAL_ACCEPTANCE'
    return status

def observe_support(V,F,scene):
    rt=mesh_scene(V,F);supported=[];blocks=[]
    for cid in protocol()['scenes'][scene]['P2']:
        s=source(cid);uv,z=vis.project_camera(V,s['K'],s['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);hit=cast(rt,uv,s['K'],s['T'])[0];cad=cast(ringscene(scene),uv,s['K'],s['T'])[0];good=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)&(s['labels'][px[:,1],px[:,0]]==1)&~(np.isfinite(hit)&(hit<z-.05))&(z<=cad+.05)&(cKDTree(obs(cid)['X']).query(V)[0]<=.75);supported.append(good);blocks.append(GATE[cid]['block'])
    a=np.array(supported);pc=sum(np.any(a[np.array(blocks)==b],axis=0)for b in sorted(set(blocks)));face=np.any(a,axis=0)[F].sum(1)>=2;multi=(pc[F]>=2).sum(1)>=2;return dict(vertex_source_support=a,vertex_partition_count=pc,face_observed_proxy=face,face_multiview_proxy=multi,face_inferred=~face)

def main():
    assert load(R/'metrics/RUN_FINISHED.json')['finished'];results=load(R/'metrics/RESULTS.json');allrows=[];summary=[];common=[];classes=[]
    for case in results:
        scene=case['case']
        if case['status']=='NOT_EXECUTABLE':summary.append(dict(case=scene,arm='ALL',status='NOT_EXECUTABLE',reason=case['reason']));continue
        data=Data(scene);items=[];p0arr=dict(np.load(R/'local_results'/scene/'C2/P0.npz'))
        for arm in ['C0','C1','C2','C3']:
            names=['P0','P1_PARTIAL']if arm=='C0'else['P0','P1','P2','P3']
            for st in names:
                path=R/'local_results'/scene/arm/(st+'.npz')
                if not path.exists():continue
                cp=dict(np.load(path));items.append((arm,st,cp,path));rt=mesh_scene(cp['V'],cp['F']);sup=observe_support(cp['V'],cp['F'],scene);np.savez_compressed(R/'local_results'/scene/arm/(st+'_EVIDENCE.npz'),**sup);area=trimesh.Trimesh(cp['V'],cp['F'],process=False).area_faces
                stages_file=R/'metrics'/(scene+'_'+arm+'_'+st+'.json');raw=load(stages_file)if stages_file.exists()else None
                classes.append(dict(case=scene,arm=arm,stage=st,support_area_mm2=float(area[sup['face_observed_proxy']].sum()),multiview_support_area_mm2=float(area[sup['face_multiview_proxy']].sum()),inferred_area_mm2=float(area[sup['face_inferred']].sum()),total_area_mm2=float(area.sum()),definition='>=2 face vertices pass fixed .75mm same-source HERO proximity and camera/Mask/CAD visibility; proxy, not truth'))
                metrics=[];native=[]
                u,v=np.meshgrid(np.arange(640),np.arange(360));uv=np.c_[u.ravel(),v.ravel()]
                for cid in data.ids:
                    s=source(cid);d=data.views[cid];o=obs(cid);z=cast(rt,uv,s['K'],s['T'])[0];cz=cast(ringscene(scene),uv,s['K'],s['T'])[0];pred=(np.isfinite(z)&(z>0)&(z<=cz)).reshape(360,640);full=s['labels']==1;bg=s['labels']!=2;unknown=np.repeat(np.repeat(d['unknown'],2,axis=0),2,axis=1);kn=~unknown
                    pa=contour(pred);pb=contour(full);pa=pa[kn[pa[:,1].astype(int),pa[:,0].astype(int)]];pb=pb[kn[pb[:,1].astype(int),pb[:,0].astype(int)]];dist=np.r_[cKDTree(pb).query(pa)[0],cKDTree(pa).query(pb)[0]]if len(pa)and len(pb)else np.array([])
                    z=cast(rt,o['uv'],o['Kn'],s['T'])[0];hit=np.isfinite(z)&(z>0)&(z<=o['cad']+.05);ph=hit[o['pairs']].all(1);err=z[hit]-o['z'][hit];closest=rt.compute_distance(o3d.core.Tensor(o['X'].astype(np.float32))).numpy();meta=next((x for x in raw['per_view']if x['source']==cid),None)if raw else None
                    row=dict(case=scene,arm=arm,stage=st,status=stage_status(raw)if raw else'HISTORICAL_PARTIAL_NO_MATCHED_BUDGET',source=cid,qualification=GATE[cid]['qualification'],role='TRAINING_NO_HOLDOUT',full_original_Mask_N=int(full.sum()),full_original_hit_N=int((pred&full).sum()),full_original_miss_N=int((full&~pred).sum()),outside_original_N=int((pred&~full&bg).sum()),full_original_IoU=float((pred&full).sum()/max(1,(full|(pred&bg)).sum())),fixed_known_original_N=int(kn.sum()),symmetric_known_contour_px=absolute_stats(dist),native_fixed_N=512,native_hit_N=int(hit.sum()),native_miss_N=int((~hit).sum()),first_depth_error_mm=absolute_stats(err),relative_fixed_pair_N=256,relative_hit_pair_N=int(ph.sum()),HERO_point_distance_mm=absolute_stats(closest),observed_HERO_behind_CAD_N=int((o['z']>o['cad']+.05).sum()),GT='NOT_EVALUABLE',fixed_training_metrics=meta)
                    allrows.append(row);metrics.append(row);native.append(dict(source=cid,z=z,pair_hit=ph))
                    np.savez_compressed(R/'local_results'/scene/arm/(st+'__'+cid+'_NATIVE_EVAL.npz'),z=z,hit=hit,pair_hit=ph)
                L,mass,_=laplace(cp['V'],cp['F']);curvature=np.linalg.norm(L@cp['V'],axis=1)/(2*mass);mesh=trimesh.Trimesh(cp['V'],cp['F'],process=False);angles=np.degrees(np.arccos(np.clip(np.sum(mesh.face_normals[mesh.face_adjacency[:,0]]*mesh.face_normals[mesh.face_adjacency[:,1]],axis=1),-1,1)))
                displacement=np.linalg.norm(cp['V']-p0arr['V'],axis=1);summary.append(dict(case=scene,arm=arm,stage=st,status=stage_status(raw)if raw else'HISTORICAL_PARTIAL',mean_full_Mask_IoU=float(np.mean([x['full_original_IoU']for x in metrics])),fixed_Mask_N=sum(x['full_original_Mask_N']for x in metrics),Mask_hit_N=sum(x['full_original_hit_N']for x in metrics),native_fixed_N=len(metrics)*512,native_hit_N=sum(x['native_hit_N']for x in metrics),native_miss_N=sum(x['native_miss_N']for x in metrics),relative_fixed_pair_N=len(metrics)*256,relative_hit_pair_N=sum(x['relative_hit_pair_N']for x in metrics),volume_mm3=volume(cp['V'],cp['F']),volume_ratio=volume(cp['V'],cp['F'])/volume(p0arr['V'],p0arr['F']),max_P0_move_mm=float(displacement.max()),median_P0_move_mm=float(np.median(displacement)),curvature_proxy_per_mm=absolute_stats(curvature),adjacent_normal_angle_deg=absolute_stats(angles),common_objective=raw['fixed_common_objective']if raw else None,Ring_gap_mm=raw['collision']['distance_mm']if raw else None,Blender_intersection_mm3=raw['Blender']['EXACT_intersection_volume_mm3']if raw else None))
        pooled={}
        for cid in data.ids:
            o=obs(cid);arrays={(arm,st):dict(np.load(R/'local_results'/scene/arm/(st+'__'+cid+'_NATIVE_EVAL.npz')))for arm,st,cp,path in items};joint=np.logical_and.reduce([x['pair_hit']for x in arrays.values()]);p=o['pairs'][joint]
            for(arm,st),ar in arrays.items():
                e=ar['z'][p[:,0]]-ar['z'][p[:,1]]-o['delta'][joint];common.append(dict(case=scene,arm=arm,stage=st,source=cid,fixed_pair_N=256,joint_common_N=int(joint.sum()),**absolute_stats(e)));pooled.setdefault((arm,st),[]).append(e)
        for(arm,st),e in pooled.items():
            ee=np.concatenate(e);common.append(dict(case=scene,arm=arm,stage=st,source='ALL',fixed_pair_N=256*len(data.ids),joint_common_N=len(ee),**absolute_stats(ee)))
    table('metrics/FIXED_DENOMINATOR_METRICS.csv',allrows);table('metrics/STAGE_COMPARISON.csv',summary);table('metrics/COMMON_PAIR_COMPARISON.csv',common);table('metrics/OBSERVED_INFERRED_AREAS.csv',classes);save('metrics/EVALUATION.json',dict(per_source=allrows,summary=summary,common_pairs=common,evidence_areas=classes,GT='NOT_EVALUABLE',no_holdout=True,no_source_removed=True));print('EVALUATED',len(summary),'real saved stages',flush=True)

if __name__=='__main__':main()
