from geometry import *
def main():
    tests=[]
    def check(name,ok):assert bool(ok),name;tests.append(dict(test=name,passed=True))
    views=load(R/'metrics/view_distribution.json');lookup={v['id']:v for v in views};roles={v['id']:v.get('role')for v in views};check('62 real camera rows /3 POSE_UNKNOWN photos',len(views)==65 and sum(not v['pose_known']for v in views)==3)
    for q in load(R/'metrics/new_reference_plan.json'):
        v=lookup[q['reference_view']];check(v['id']+' is actual new reference, not renamed P0',not v['existing_refs']);check(v['id']+' not holdout',roles[v['id']]!='HOLDOUT');check(v['id']+' source role frozen',len(q['source_views'])==3 and all(roles[x]!='HOLDOUT'for x in q['source_views']));check(v['id']+' no cross video source',all(lookup[x]['source_id']==v['source_id']for x in q['source_views']))
    for c in cases():
        s=source(c['id']);a=np.load(R/f'local_results/cleaned/{c["id"]}.npz');check(c['id']+' exact XYZ',np.array_equal(a['XYZ_mm'],s['P']));check(c['id']+' exact T2 predicate',np.array_equal(a['historical_T2_deleted'],a['rho_radius']<a['threshold']));check(c['id']+' protected stalk not removed',not np.any(a['clean_removed']&a['protected_possible_stalk']))
    p=np.array([[0,0,1.],[1,0,1.]]);K=np.eye(3);uv,z=vis.project_camera(p,K,np.eye(4));check('axial millimeter pinhole roundtrip',np.allclose(vis.camera_rays(uv,K,np.eye(4))[:,3:]*z[:,None],p));both('small_tests',tests);print('TESTS',len(tests),'pass')
if __name__=='__main__':main()
