"""Independent dense reference; never replaces any frozen fitting basis."""
from mesh_basis import *
from scipy.linalg import eigh
def main():
    rows=[]
    for scene in protocol()['scenes']:
        for initial in ['E1','E2']:
            b=dict(np.load(R/'inputs'/f'{scene}_{initial}_basis.npz'));lam=eigh(b['L'],np.diag(b['mass']),subset_by_index=[0,157],eigvals_only=True,driver='gvx');err=abs(lam-b['raw_lam']);rel=err[1:]/np.maximum(abs(lam[1:]),1e-10)
            rows.append(dict(scene=scene,initial=initial,first158_max_absolute_eigen_error=float(err.max()),first157_nonzero_max_relative_error=float(rel.max()),min_dense_nonzero_gap=float(np.diff(lam[1:]).min()),same_candidate_spectrum=bool(rel.max()<1e-5),dense_reference=lam,frozen_ARPACK_spectrum=b['raw_lam'],fitting_inputs_changed=False))
    mesh=trimesh.creation.icosphere(subdivisions=3,radius=5);L,m,_=laplace(mesh.vertices,mesh.faces);lam=eigh(L.toarray(),np.diag(m),subset_by_index=[0,9],eigvals_only=True,driver='gvx');expected=np.r_[0,np.full(3,.08),np.full(5,.24),.48];rel=abs(lam[1:9]-expected[1:9])/expected[1:9]
    save('metrics/LAPLACIAN_DENSE_REFERENCE_AUDIT.json',dict(real_cases=rows,all_real_frozen_spectra_match=all(x['same_candidate_spectrum']for x in rows),symmetric_sphere=dict(expected=expected,dense=lam,max_first8_relative_error=float(rel.max()),same_frozen_tolerance=.03,dense_control_pass=bool(rel.max()<.03),ARPACK_failure_preserved_in='LAPLACIAN_SYNTHETIC_CONSISTENCY.json'),interpretation='ARPACK exact-eigenvalue multiplicity can be incomplete; no fitting source or model changed; real frozen spectra checked separately'))
    print('REAL_DENSE_REFERENCE_MATCH',sum(x['same_candidate_spectrum']for x in rows),'/',len(rows),'SPHERE_DENSE_REL_ERROR',float(rel.max()))
if __name__=='__main__':main()
