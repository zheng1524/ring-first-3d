"""Read-only numerical summary of the already-frozen spectral inputs."""
from inputs import *
def main():
    rows=[]
    for scene in protocol()['scenes']:
        for initial in ['E1','E2']:
            b=dict(np.load(R/'inputs'/f'{scene}_{initial}_basis.npz'));P=b['phi'];mass=b['mass'];gram=P.T@(mass[:,None]*P);diag=np.sqrt(np.diag(gram));corr=gram/(diag[:,None]*diag[None,:]);V=b['V'];F=b['F'];G=b['G'];motions=(G*b['n'][:,:,None]).sum(1);overlap=P.T@(mass[:,None]*motions);mesh=trimesh.Trimesh(V,F,process=False);cad=ringmesh(scene)
            rows.append(dict(scene=scene,initial=initial,vertex_N=len(V),face_N=len(F),components=len(mesh.split(only_watertight=False)),P0_mathematically_closed=bool(mesh.is_watertight),unknown_back_is_observed=False,min_face_area_mm2=float(b['area'].min()),mass_min_mm2=float(mass.min()),mass_total_area_mm2=float(mass.sum()),raw_eigen_min=float(b['raw_lam'][0]),raw_zero_eigen_N=int((abs(b['raw_lam'])<1e-8).sum()),raw_spectrum=b['raw_lam'],candidate_frequency_proxy=b['lam'],raw_M_orth_max=float(b['raw_orth']),final_mass_normalized_orth_max=float(abs(corr-np.eye(128)).max()),P0_normal_tangent_rank=int(b['p0_normal_rank']),P0_motion_inner_product_max=float(abs(overlap).max()),candidate_N=P.shape[1],constant_modes_released=0,final_modes_are_projected_eigenfields=True,max_normal_length_error=float(abs(np.linalg.norm(b['n'],axis=1)-1).max()),Ring_CAD_closed=bool(cad.is_watertight),Ring_CAD_winding_consistent=bool(cad.is_winding_consistent)))
            rows[-1].update(L_symmetry_max=float(abs(b['L']-b['L'].T).max()),L_constant_null_max=float(abs(b['L']@np.ones(len(V))).max()))
    save('metrics/BASIS_AUDIT.json',rows);table('metrics/BASIS_AUDIT.csv',[{k:v for k,v in row.items()if k not in ['raw_spectrum','candidate_frequency_proxy']}for row in rows]);print('BASIS_AUDITED',len(rows))
if __name__=='__main__':main()
