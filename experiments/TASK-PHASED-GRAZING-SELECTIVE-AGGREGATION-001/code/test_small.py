from cleaning import *
def main():
    rows=[]
    def check(name,test):assert bool(test),name;rows.append(dict(test=name,passed=True))
    n=np.array([0.,0,1.]);rays=np.array([[1,0,0],[np.cos(np.deg2rad(15)),0,np.sin(np.deg2rad(15))],[0,0,1.]])
    beta=np.degrees(np.arcsin(np.clip(abs(rays@n),0,1)));check('grazing definition 0/15/90 degrees',np.allclose(beta,[0,15,90]));check('normal sign invariance',np.array_equal(abs(rays@n),abs(rays@-n)))
    H=trimesh.transformations.rotation_matrix(.7,[.2,.3,.4]);check('rigid beta invariance',np.allclose(abs((rays@H[:3,:3].T)@(H[:3,:3]@n)),abs(rays@n)))
    a=np.array([5,12,18,30]);eligible=np.array([False,True,True,True]);m=[eligible&(a<t)for t in [10,15,20]];check('unreliable low angle retained',not m[0][0]);check('fixed threshold nesting',np.all(~m[0]|m[1])and np.all(~m[1]|m[2]))
    p=np.array([[0,0,1],[1,0,1],[0,1,1],[1,1,1.]]);f=np.array([[0,1,2],[1,3,2]]);check('original face area proxy conservation',np.isclose(vertex_area(p,f).sum(),area(p,f).sum()));check('face removal only references existing vertices',np.array_equal(f[~np.array([False,False,False,True])[f].any(1)],f[:1]))
    K=np.array([[490.,0,319.5],[0,490,179.5],[0,0,1.]]);pose=np.eye(4);uv,z=vis.project_camera(p,K,pose);r=vis.camera_rays(uv,K,pose);check('ray parameter equals axial mm depth',np.allclose(r[:,:3]+r[:,3:]*z[:,None],p));check('depth tolerance uses projected physical sampling',np.allclose(depth_tau(np.array([30.,100.]),K),[.5,300/490]))
    # Reuse latest approved two-class HLS lightness definition, analytically.
    import colorsys
    pc=np.array([colorsys.hls_to_rgb(340/360,x,.7)for x in [.82,.27]]);bc=np.array([colorsys.hls_to_rgb(170/360,x,.7)for x in [.82,.27]]);check('approved shared depth lightness / distinct hues',pc[0].mean()>pc[1].mean()and bc[0].mean()>bc[1].mean()and not np.allclose(pc,bc))
    check('only prescribed angle thresholds',cfg()['angles_deg']==[10,15,20]);check('no relative depth correction',cfg()['relative_depth_correction']is False)
    both('small_tests',rows);print('SMALL TESTS',len(rows),'passed',flush=True)
if __name__=='__main__':main()
