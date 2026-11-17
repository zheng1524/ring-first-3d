"""Investigate two measured mesh/root discrepancies, without changing outputs."""
from models import *
from scipy.optimize import brentq
def main():
    rr=load(R/'metrics/S2_PRIMARY.json');rows=[]
    for scene,arm,cid in [('G01_004','A1-3','G01_004_ref08'),('G07_004','A1-3','G07_004_ref04')]:
        m=next(m for m in rr if(m['scene'],m['arm'])==(scene,arm));p=np.array(m['p']);R0=np.array(m['R0']);c,Q,a=decode(p,R0);o=observation(cid);s=source(cid);rays=vis.camera_rays(o['depth_native_uv'],o['Kn'],s['T']);t=first_depth(p,R0,m['family'],rays)
        for factor in [1,2,4]:
            P,F=sphere_mesh(96*factor,48*factor,float(p[9]))if m['family']=='cap'else sphere_mesh(96*factor,48*factor)
            if m['family']=='star':P=P*radial_factor(P,p[9:])[:,None]
            P=(P*a)@Q.T+c;z=cast(mesh_scene(P,F),o['depth_native_uv'],o['Kn'],s['T'])[0];hit=np.isfinite(z)&np.isfinite(t)
            rows.append(dict(scene=scene,arm=arm,reference=cid,display_refinement_factor=factor,vertices=len(P),faces=len(F),hit_disagreement_N=int((np.isfinite(t)!=np.isfinite(z)).sum()),common_depth_error_mm=stats(t[hit]-z[hit]),changes_formal_output=False))
    # Only the already detected disagreeing ray: resolve the reason on its legal
    # finite interval. This diagnostic never replaces a fitted or evaluated value.
    m=next(m for m in rr if(m['scene'],m['arm'])==('G01_004','A1-3'));p=np.array(m['p']);R0=np.array(m['R0']);c,Q,a=decode(p,R0);cid='G01_004_ref08';o=observation(cid);s=source(cid);rays=vis.camera_rays(o['depth_native_uv'],o['Kn'],s['T']);i=0;r=rays[i];on=(r[:3]-c)@Q/a;dn=r[3:]@Q/a;lo,hi,valid=quadratic_interval(on[None],dn[None],np.exp(.2));grid=np.linspace(lo[0],hi[0],4097)
    def fun(t):
        x=on+np.asarray(t)[...,None]*dn;radius=np.linalg.norm(x,axis=-1);n=x/np.maximum(radius[...,None],1e-15);return radius-radial_factor(n.reshape(-1,3),p[9:]).reshape(radius.shape)
    values=fun(grid);ids=np.flatnonzero(values[:-1]*values[1:]<=0);roots=[brentq(lambda z:float(fun(z)),grid[k],grid[k+1])for k in ids]
    save('metrics/ROOT_BRACKETING_FAILURE.json',dict(scene='G01_004',arm='A1-3',source=cid,fixed_ray_index=i,native_uv=o['depth_native_uv'][i],native_pixel_id=int(o['depth_native_uv'][i,1]*640+o['depth_native_uv'][i,0]),old_33_samples_hit=bool(np.isfinite(first_depth(p,R0,'star',rays)[i])),diagnostic_grid_N=4097,diagnostic_roots_mm=roots,minimum_radial_implicit_value=float(values.min()),diagnosis='Two close roots in a single 33-grid cell: a narrow grazing interval is missed. Dense mesh retains hit at 1x/2x/4x, ruling out a coarse-mesh-only explanation.',formal_root_contract='FAIL',changes_formal_output=False,GT_used=False))
    table('metrics/MESH_REFINEMENT_DIAGNOSTIC.csv',rows);save('metrics/MESH_REFINEMENT_DIAGNOSTIC.json',rows);print(json.dumps(clean(rows),indent=2))
if __name__=='__main__':main()
