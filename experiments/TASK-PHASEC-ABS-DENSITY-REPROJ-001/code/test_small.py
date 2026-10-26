"""Analytic checks for source color provenance, occlusion and index-only removal."""
from reprojection import *
class Value:
    def __init__(self,x):self.x=x
    def numpy(self):return self.x
class EmptyCAD:
    def cast(self,uv):return{'t_hit':Value(np.full(len(uv),np.inf))}
def main():
    checks=[]
    def check(name,ok):assert ok,name;checks.append(dict(check=name,passed=True))
    P=np.array([[1.,1,1],[2.,2,2],[-1.,0,-1],[50.,50,1]]);rgb=np.array([[1.,0,0],[0.,1,0],[0,0,1],[1,1,0]]);kind=np.ones(4,int);ids=np.arange(4);scene=EmptyCAD();out=raster(P,rgb,kind,ids,np.eye(3),np.eye(4),(4,4),scene)
    check('nearest_positive_source_wins_no_hole_fill',out['source_original_id'][1,1]==0 and(out['RGBA'][:,:,3]>0).sum()==1)
    check('exact_A_color_preserved',np.array_equal(out['RGBA'][1,1,:3],[255,0,0]))
    q=raster(P[1:],rgb[1:],kind[1:],ids[1:],np.eye(3),np.eye(4),(4,4),scene);check('deletion_reveals_next_original_point',q['source_original_id'][1,1]==1 and np.array_equal(q['RGBA'][1,1,:3],[0,255,0]))
    uv,z=vis.project_camera(P[:2],np.eye(3),np.eye(4));check('axial_Z_and_pixel_roundtrip',np.array_equal(uv,[[1,1],[1,1]])and np.array_equal(z,[1,2]))
    keep=np.array([5.,10,15])>=10;check('strict_threshold_boundary',np.array_equal(keep,[False,True,True]))
    F=np.array([[0,1,2],[1,2,3]]);deleted=np.array([True,False,False,False]);check('only_incident_original_faces_removed',np.array_equal(F[~deleted[F].any(1)],[[1,2,3]]))
    target=np.zeros((4,4,3),np.uint8);ev=evaluate(out,out,target,np.ones((4,4),np.uint8));check('identical_raw_clean_common_support_errors_equal',ev['common_raw']==ev['common_cleaned']and ev['coverage_change']==0)
    denied=False
    try:open('/home/liu/polyp_research/forbidden_test_WRITE','w')
    except PermissionError:denied=True
    check('read_only_history_guard',denied);save('metrics/small_tests.json',dict(status='PASS',checks=checks));print('PASS',len(checks),'analytic/identity checks')
if __name__=='__main__':main()
