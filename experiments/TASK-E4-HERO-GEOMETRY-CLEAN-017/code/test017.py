from analyze017 import *
def main():
    t=load(R/'config/PROTOCOL.json')['thresholds'];tests=[]
    # Scalar logic controls isolate correlated metrics: single warnings never delete.
    base=dict(perspective_stretch=1.,tangent_stretch=1.,tangent_reliable=True,native_depth_jump_mm=0.,triangle_quality=.8,normal_coherence=1.,normal_angle_deg=0.,boundary_distance_native_px=10.,CAD_inside_samples=0,native_mask_supported=True,incidence_min=.9,CAD_occluded=False,density_normalized=1.,nearest_competition=False,boundary_face=False,minor_component=False,nonmanifold=False)
    cases=[('ordinary',{},0),('long_edge_only',dict(perspective_stretch=30),1),('low_density_only',dict(density_normalized=.01),1),('sharp_normal_only',dict(normal_angle_deg=89),1),('boundary_only',dict(boundary_face=True,boundary_distance_native_px=1),1),('Ring_proximity_not_input',{},0),('Ring_inside_alone',dict(CAD_inside_samples=3),1),('hidden_behind_CAD',dict(CAD_occluded=True),3),('unknown_native_ID',dict(native_mask_supported=False),3),('grazing_extreme',dict(perspective_stretch=30,tangent_stretch=20,native_depth_jump_mm=5,triangle_quality=.01,boundary_distance_native_px=1,incidence_min=.01),3),('joint_edge_tear',dict(perspective_stretch=30,tangent_stretch=10,native_depth_jump_mm=2,triangle_quality=.03,boundary_distance_native_px=1),2),('interior_uncertain',dict(perspective_stretch=30,tangent_stretch=10,native_depth_jump_mm=2,triangle_quality=.03),1),('CAD_joint_penetration',dict(CAD_inside_samples=3,CAD_occluded=True,native_depth_jump_mm=2,triangle_quality=.03),2)]
    for name,delta,expected in cases:
        f={k:np.array([v])for k,v in dict(base,**delta).items()};state,_=classify(f,t);assert int(state[0])==expected,(name,state,expected);tests.append(dict(name=name,state=STATE_NAMES[state[0]],passed=True))
    # Physical controls use exact perspective planes, not guessed point spacing.
    K=np.array([[150.,0,23.5],[0,150.,23.5],[0,0,1.]]);T=np.eye(4);yy,xx=np.mgrid[:48,:48];r=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)]@np.linalg.inv(K).T
    labels=np.ones((48,48),np.uint8);labels[[0,-1]]=0;labels[:,[0,-1]]=0
    rm=trimesh.creation.box(extents=[1,1,1]);rm.apply_translation([100,100,100]);ring=scene(rm.vertices,rm.faces)
    for angle in [0.,65.,80.]:
        n=np.array([np.sin(np.radians(angle)),0,np.cos(np.radians(angle))]);z=(20*n[2]/(r@n)).reshape(48,48);P,F,uv,fid=native_grid(z,labels,K,T);s=dict(P=P,F=F,uv=uv,pack=dict(labels=labels,depth_mm=z,K=K,pose=T),T=T,K=K,Kn=K,nativez=z[uv[:,1],uv[:,0]],mask_ok=np.ones(len(uv),bool),boundary_distance_native=distance_transform_edt(labels==1)[uv[:,1],uv[:,0]])
        f,state,reason,top=analyze(s,ring,t);assert (state!=2).all(),angle;tests.append(dict(name='exact_perspective_plane_'+str(angle),rejected=int((state==2).sum()),max_tangent_stretch=stats(f['tangent_stretch']),max_perspective_stretch=stats(f['perspective_stretch']),passed=True))
    # Native IDs and half-pixel contract roundtrip; EDT convention is explicit.
    full=np.array([[490.,0,319.5],[0,490,179.5],[0,0,1.]]);S=np.diag([1.,352/360,1.]);S[1,2]=.5*352/360-.5;Kn=S@full
    uv=np.array([[0.,0],[639,351],[319,175]]);back=(np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@full.T)@np.linalg.inv(full).T@Kn.T;assert np.max(abs(back[:,:2]/back[:,2:]-uv))<1e-10
    m=np.zeros((7,7),bool);m[1:6,1:6]=True;d=distance_transform_edt(m);assert d[1,3]==1 and d[3,3]==3
    tests.append(dict(name='half_pixel_roundtrip_and_sample_centre_EDT',passed=True));save('metrics/CONTROL_TESTS.json',dict(passed=all(x['passed']for x in tests),tests=tests,GT_used=False))
    print('CONTROL_TESTS_PASS',len(tests),flush=True)
if __name__=='__main__':main()
