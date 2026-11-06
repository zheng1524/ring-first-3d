from parametric import *

def main():
 rows=[];Q=np.eye(3);plane=dict(family='cap',base_Q=Q,anchor=[0.,0.,0.],stage='C0');p=np.r_[0.,0.,np.log([2.,3.,1.]),0.];V,F,full,flag=body(p,plane);m=trimesh.Trimesh(V,full,process=False);rows.append(dict(test='cap_closed_computational_solid',passed=bool(m.is_watertight and m.is_winding_consistent),open_render_surface_has_no_inferred_bottom=len(F)<len(full),inferred_base_faces=int(flag.sum())))
 for index,step,expected in[(0,.05,[.05,0,0]),(1,.05,[0,.05,0])]:
  q=p.copy();q[index]+=step;W,_,_,_=body(q,plane);error=float(abs((W-V)-expected).max());rows.append(dict(test='footprint_translation_'+str(index),error=error,passed=error<1e-10))
 q=p.copy();q[4]+=np.log(1.1);W,_,_,_=body(q,plane);rows.append(dict(test='retained_height_expansion',passed=bool(np.all(W[:,2]>=V[:,2]-1e-12)and abs(W[:,2].max()-1.1)<1e-10),same_boundary_zero=True));pm=np.r_[p,2.,0.,0.];heightmeta=dict(plane,stage='C2');W,upper,_,_=body(pm,heightmeta);W=W[np.unique(upper)];P=(W-np.array(heightmeta['anchor']))@np.array(heightmeta['base_Q']);analytic=np.maximum(0,1-(P[:,0]/2)**2-(P[:,1]/3)**2)**2;rows.append(dict(test='old_A1_height_family_gamma2_equivalence',max_error=float(abs(P[:,2]-analytic).max()),passed=float(abs(P[:,2]-analytic).max())<1e-9))
 for name in load(R/'config/PROTOCOL.json')['cases']:
  a=np.load(R/'inputs'/name/'INITIAL.npz');p,Q=initial_parameters(a['V']);c,Q,axes=decode_ellipsoid(p,Q);error=float(abs(np.linalg.norm((a['V']-c)@Q/axes,axis=1)-1).max());rows.append(dict(test='P0_ellipsoid_parameter_adapter',case=name,max_implicit_error=error,passed=error<1e-5))
 save('metrics/PARAMETRIC_PREFLIGHT.json',dict(passed=all(x['passed']for x in rows),rows=rows,real_GT_read=False,hyperparameter_choice_from_control=False));print(rows)
if __name__=='__main__':main()
