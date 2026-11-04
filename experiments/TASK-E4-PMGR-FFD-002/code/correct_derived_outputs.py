"""Post-stop output-only repairs; preserve originals, all geometry and logs."""
from inputs import *
from shape import Body
import datetime
import copy

def main():
    if (R/'metrics/DERIVED_OUTPUT_ORIGINALS.json').exists():
        print('ALREADY_CORRECTED; originals never overwritten');return
    assert load(R/'metrics/RUN_FINISHED.json')['finished'];old={};changes=[]
    for scene in protocol()['scene_order']:
        initial=R/'local_results'/scene/'C2/P0.npz'
        if not initial.exists():continue
        p=np.load(initial)['q'][:9];row=p0(scene,protocol()['scenes'][scene]['initial'])
        for arm in ['C1','C2','C3']:
            basis=np.load(R/'inputs'/(scene+('_spectral'if arm=='C1'else'_ffd')+'_BASIS.npz'))['fields'];body=Body(row,p,basis)
            for name in ['P0','P1','P2','P3','BEST','LAST_SAFE']:
                file=R/'metrics'/(scene+'_'+arm+'_'+name+'.json');path=R/'local_results'/scene/arm/(name+'.npz')
                if not file.exists()or not path.exists():continue
                j=load(file);old[file.name]=copy.deepcopy(j);cp=dict(np.load(path));q=cp['q'];assert abs(cp['V']-body.vertices(q)).max()<1e-10
                delta=np.linalg.norm(cp['V']-body.vertices(np.r_[q[:9],np.zeros(len(q)-9)]),axis=1);prev=j['maximum_nonellipsoid_displacement_mm'];j['maximum_nonellipsoid_displacement_mm']=float(delta.max());j['median_nonellipsoid_displacement_mm']=float(np.median(delta));x=j.get('extra')or{}
                if j['status']=='BUDGET_COMPLETED'and x.get('attempted_iterations',0)<x.get('budget_iterations',0):j['status']='TRUST_REGION_NUMERICAL_LIMIT_PARTIAL_ACCEPTANCE';x['status']=j['status'];x['termination']='finite damping limit1e8, not all scheduled iterations consumed';j['extra']=x
                j['post_stop_output_correction']='Derived nonellipsoid displacement now uses CURRENT nine-parameter ellipsoid; early-stage status distinguishes numerical trust limit. Original JSON preserved; no geometry/update replay.'
                changes.append(dict(file=file.name,old_max_nonellipsoid_mm=prev,corrected_max_nonellipsoid_mm=float(delta.max()),original_status=old[file.name]['status'],corrected_status=j['status'],geometry_SHA_unchanged=asset(path)));save('metrics/'+file.name,j)
    # Preserve original embedded outputs as well; refresh them from stage files.
    result=load(R/'metrics/RESULTS.json');old['RESULTS.json']=copy.deepcopy(result)
    for case in result:
        if 'arms'not in case:continue
        for arm in case['arms']:
            arm['stages']=[load(R/'metrics'/(case['case']+'_'+arm['arm']+'_'+s['stage']+'.json'))for s in arm.get('stages',[])]
            if 'last_safe'in arm:arm['last_safe']=load(R/'metrics'/(case['case']+'_'+arm['arm']+'_LAST_SAFE.json'))
        save('metrics/'+case['case']+'_RESULTS.json',case)
    save('metrics/DERIVED_OUTPUT_ORIGINALS.json',old);save('metrics/RESULTS.json',result);save('metrics/DERIVED_OUTPUT_CORRECTION.json',dict(changes=changes,no_geometry_changed=True,no_optimization_repeated=True,executed_commit='24232c8',correction_scope='two reporting calculations only',timestamp=datetime.datetime.now().astimezone().isoformat()));print('DERIVED_OUTPUT_REPAIRS',len(changes),flush=True)

if __name__=='__main__':main()
