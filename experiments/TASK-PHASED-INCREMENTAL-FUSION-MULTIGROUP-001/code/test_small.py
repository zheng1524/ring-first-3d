"""Small analytic checks for traceable subdivision and isolated projection geometry."""
from metric_geometry import *
def main():
    checks=[]
    def ck(name,ok):assert bool(ok),name;checks.append(dict(check=name,passed=True))
    P=np.array([[0.,0,0],[4,0,0],[0,3,0]]);b=np.array([[[1,0,0],[.5,.5,0],[.5,0,.5]],[[.5,.5,0],[0,1,0],[0,.5,.5]],[[.5,0,.5],[0,.5,.5],[0,0,1]],[[.5,.5,0],[0,.5,.5],[.5,0,.5]]]);tri=b@P;areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2;ck('one_level_source_triangle_subdivision_area_exact',np.allclose(areas,1.5)and np.isclose(areas.sum(),6));ck('subdivision_inside_parent_and_source_weights',np.all(b>=0)and np.allclose(b.sum(2),1))
    X=np.array([[0.,0,2],[4,0,2],[4,3,2],[0,3,2]]);f=projected_feret(X,np.array([0.,0,1.]));ck('projected_Feret_3_4_5',np.isclose(f['value_mm'],5));ck('normal_displacement_does_not_change_transverse_diameter',np.isclose(projected_feret(X+np.array([0,0,17]),np.array([0.,0,1.]))['value_mm'],5))
    for c in cases():
        s=source(c['id']);uv,z=vis.project_camera(s['P'],s['p']['K'],s['p']['pose']);ck(c['id']+'_source_pixel_camera_identity',np.max(abs(uv-np.c_[s['a']['source_u'],s['a']['source_v']]))<1e-8)
    ck('four_independent_groups_not_five_videos',len(set(c['group']for c in cases()))==4 and len(scenes())==5);save('metrics/small_tests.json',dict(status='PASS',checks=checks,not_physical_accuracy=True));print('SMALL_CHECKS',len(checks),'PASS',flush=True)
if __name__=='__main__':main()
