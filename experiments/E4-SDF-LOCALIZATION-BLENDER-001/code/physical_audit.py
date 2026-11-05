from common import *
import subprocess
sys.path.insert(0,'/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1/runtime/packages')
import fcl
def obj(V,F):
    b=fcl.BVHModel();b.beginModel(len(V),len(F));b.addSubModel(np.asarray(V,float),np.asarray(F,np.int32));b.endModel();return fcl.CollisionObject(b)
def main():
    assert load(R/'metrics/FIT_FINISHED.json')['finished'];cad=np.load(R/'inputs/RING_CAD.npz');c=obj(cad['V'],cad['F']);rows=[]
    for name,path in [('INITIAL',R/'local_results/INITIAL/MODEL.npz'),('FINAL',R/'local_results/FINAL/MODEL.npz'),('TARGET_GT_AUDIT',R/'audit_only/TARGET_GT.npz')]:
        a=np.load(path);o=obj(a['V'],a['F']);res=fcl.CollisionResult();n=fcl.collide(o,c,fcl.CollisionRequest(),res);dist=fcl.distance(o,c,fcl.DistanceRequest(),fcl.DistanceResult());npz=R/'audit_only'/(name+'_BLENDER_CHECK.npz');out=R/'metrics'/(name+'_BLENDER.json');np.savez_compressed(npz,V=a['V'],F=a['F'],CAD_V=cad['V'],CAD_F=cad['F']);proc=subprocess.run([BLENDER,'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(PREV/'code/blender_check.py'),'--',str(npz),str(out)],capture_output=True,text=True,timeout=120);(R/'runtime'/(name+'_BLENDER.log')).write_text(proc.stdout+proc.stderr);assert proc.returncode==0
        b=load(out);rows.append(dict(stage=name,triangle_collision=bool(n),full_triangle_Ring_gap_mm=float(dist),Blender=b,passed=not n and b['EXACT_intersection_volume_mm3']<=1e-8))
    save('metrics/PHYSICAL_AUDIT.json',dict(passed=all(x['passed']for x in rows),rows=rows,no_source_scene_modification=True));print('PHYSICAL_AUDIT',all(x['passed']for x in rows),flush=True)
    # Reuse the audited broad and narrow triangle tests, without importing any
    # old IO guard or updating its files. Original helpers are SHA-indexed.
    for fn in ['mesh_checks.py','copanalysis.py']:
        src=PREV/'code'/fn;nodes=[n for n in ast.parse(src.read_text()).body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'),globals())
    broad=[];narrow=[]
    for name,path in [('BASE_SOURCE',R/'inputs/BASE_SOURCE_MESH.npz'),('TARGET_GT',R/'audit_only/TARGET_GT.npz'),('DMTET_INITIAL',R/'local_results/INITIAL/MODEL.npz'),('DMTET_FINAL',R/'local_results/FINAL/MODEL.npz')]:
        a=np.load(path);b=self_intersections(a['V'],a['F']);broad.append(dict(state=name,**b));rr=inspect_coplanar(a['V'],a['F']);positive=[x for x in rr if x['projected_intersection_area_mm2']>0];narrow.append(dict(state=name,coplanar_broad_N=len(rr),positive_area_N=len(positive),max_area_mm2=max([x['projected_intersection_area_mm2']for x in rr],default=0),positive_examples=positive[:8]))
    save('metrics/SELF_INTERSECTION_DIAGNOSTIC.json',broad);save('metrics/COPLANAR_NARROW_PHASE.json',narrow);save('assets_index/GEOMETRY_QA_HELPERS.json',[asset(PREV/'code'/n)for n in ['blender_check.py','mesh_checks.py','copanalysis.py']])
    reference=list(csv.DictReader(Path('/home/liu/new-polyp-dxy/docs/theory/data/scenes.csv').open()));checks=[]
    for a in reference:
        if a['model']=='IIa6.5':
            p=OLD/'scenes'/a['scene_id'];checks.append(dict(id=a['scene_id'],RGB_matches_theory=sha(p/'rgb.png')==a['image_sha256'],oracle_matches_theory=sha(p/'oracle_mask.png')==a['mask_sha256']))
    original=[]
    for a in load(R/'assets_index/SOURCE_AUDIT.json')['models']:
        s=a['source'];original.append(dict(model=a['model'],path=s['path'],sha256_unchanged=sha(s['path'])==s['sha256']))
    save('metrics/DXY_THEORY_IDENTITY_VERIFICATION.json',dict(public_oracle_checks=checks,original_source_mesh_checks=original,all_unchanged=all(x['sha256_unchanged']for x in original),no_DXY_algorithm_execution=True,no_prediction_fallback=True))
if __name__=='__main__':main()
