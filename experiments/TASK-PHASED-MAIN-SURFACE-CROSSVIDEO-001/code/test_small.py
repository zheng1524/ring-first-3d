"""Analytic coordinate and source-color checks; no clinical GT or upstream run."""
from registration import *
from source_rgb_projection import raster
class T:
    def __init__(self,a):self.a=a
    def numpy(self):return self.a
class NoCAD:
    def cast(self,uv):return{'t_hit':T(np.full(len(uv),np.inf))}
def main():
    rows=[]
    def check(name,ok):assert bool(ok),name;rows.append(dict(check=name,passed=True))
    H=np.eye(4);H[:3,:3]=Rotation.from_euler('z',31,degrees=True).as_matrix();H[:3,3]=[.1,-.2,.05];P=np.array([[1.,2,3],[2,-1,0]]);check('SE3_direction_roundtrip',np.allclose(transform(transform(P,H),np.linalg.inv(H)),P,atol=1e-12));check('SE3_scale_fixed',ring_geometry(H)['SE3']);bad=H.copy();bad[:3,:3]*=1.01;check('scale_change_rejected',not ring_geometry(bad)['SE3'])
    points=np.array([[1.,1,1],[2.,2,2]]);col=np.array([[1.,0,0],[0,1,0]]);pred=raster(points,col,np.ones(2,int),np.arange(2),np.eye(3),np.eye(4),(4,4),NoCAD());check('nearest_original_point_RGB_no_target_color',pred['source_original_id'][1,1]==0 and np.array_equal(pred['RGBA'][1,1,:3],[255,0,0])and np.count_nonzero(pred['RGBA'][:,:,3])==1)
    for c in cases():
        s=source(c['id']);uv,z=vis.project_camera(s['P'],s['p']['K'],s['p']['pose']);check(c['id']+'_original_pixels_and_camera',np.max(abs(uv-np.c_[s['a']['source_u'],s['a']['source_v']]))<1e-8);check(c['id']+'_original_faces_indices',s['m'].faces.min()>=0 and s['m'].faces.max()<len(s['P']))
    save('metrics/small_tests.json',dict(status='PASS',checks=rows,not_geometry_accuracy=True));print('SMALL_TESTS_PASS',len(rows))
if __name__=='__main__':main()
