"""Geometry, CAD visibility and source-color invariants for the scene adapter."""
from scene_renderer import *
import inspect
def main():
    tests=[]
    def check(n,x):assert x,n;tests.append(n)
    d=scene_data('G01_004_ref03');h=np.load(HIST/'local_scenes/G01_004_same_camera_ref03/Background_FULL_DISPLAY_ONLY.npz');cache=np.load(INC/'local_results/background/G01_004_ref03.npz');check('recovered historical background XYZ/RGB exactly',np.array_equal(h['XYZ_mm'],cache['XYZ_mm'])and np.array_equal(h['rgb'],cache['RGB']))
    check('all original Polyp points retained',np.array_equal(d['P'],source(d['c']['id'])[1]));projected,z=vis.project_camera(d['P'],d['p']['K'],d['p']['pose']);check('P0 identity round trip',np.max(abs(projected-d['uv']))<1e-4)
    row=next(x for x in load(R/'provenance/PAIRS_FROZEN.json')['pairs']if'video005_v005'in x['pair_id']);H=np.array(row['H_A_to_B_world']);pose=np.array(row['B_target']['c2w']);a,_=vis.project_camera(d['P'],d['p']['K'],np.linalg.inv(H)@pose);b,_=vis.project_camera(d['P']@H[:3,:3].T+H[:3,3],d['p']['K'],pose);check('frozen H changes camera coordinates only, projection equivalent',np.allclose(a,b,atol=1e-9))
    sc=camera_scene(d,d['p']['K'],d['p']['pose']);ri=sc.ring_image();check('Ring is CAD raycast, opaque at hits and black shaded',set(np.unique(ri[:,:,3]))=={0,1}and 0<ri[:,:,:3].max()<.1)
    v,u=np.nonzero(ri[:,:,3]>0);ij=np.array([[u[len(u)//2],v[len(v)//2]]]);ray=vis.camera_rays(ij,d['p']['K'],d['p']['pose'])[0];depth=sc.cast(ij)['t_hit'].numpy()[0]
    dd={**d,'P':(ray[:3]+ray[3:]*(depth+1))[None],'C':np.array([[1.,0,0]]),'uv':ij,'B':np.empty((0,3)),'BC':np.empty((0,3)),'BU':np.empty((0,2),int),'B_ids':np.array([],int)};r=point_projection(dd,d['p']['K'],d['p']['pose']);check('actual CAD occludes point behind it',r['layer'][ij[0,1],ij[0,0]]==2)
    dd['P']=(ray[:3]+ray[3:]*(depth-1))[None];r=point_projection(dd,d['p']['K'],d['p']['pose']);check('point in front can occlude CAD',r['layer'][ij[0,1],ij[0,0]]==1 and np.array_equal(r['RGBA'][ij[0,1],ij[0,0],:3],[255,0,0]))
    check('prediction APIs have no target color/mask/depth inputs',list(inspect.signature(point_projection).parameters)==['d','K','pose'])
    save('metrics/small_tests.json',dict(passed=len(tests),tests=tests));print('SMALL_TESTS_PASS',len(tests))
if __name__=='__main__':main()
