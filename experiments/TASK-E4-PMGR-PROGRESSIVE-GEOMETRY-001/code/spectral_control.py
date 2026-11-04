"""CPU synthetic consistency: sphere LB spectrum, not a fitting input."""
from mesh_basis import *
def main():
    mesh=trimesh.creation.icosphere(subdivisions=3,radius=5);L,m,area=laplace(mesh.vertices,mesh.faces);lam,phi=eigsh(L,k=10,M=sparse.diags(m),sigma=-1e-8,which='LM',v0=np.linspace(1,2,len(m)),tol=1e-10);order=np.argsort(lam);lam=lam[order];phi=phi[:,order];expected=np.r_[0,np.full(3,2/25),np.full(5,6/25),12/25];rel=abs(lam[1:9]-expected[1:9])/expected[1:9];res=L@phi-m[:,None]*phi*lam
    result=dict(identity='SYNTHETIC_SPHERE_CONTROL_NOT_REAL_GT',radius_mm=5,mesh_subdivisions=3,expected_eigenvalues=expected,actual_eigenvalues=lam,nonzero_first8_relative_error_max=float(rel.max()),analytic_tolerance=.03,generalized_eigen_residual_max=float(abs(res).max()),L_symmetry_max=float(abs(L-L.T).max()),constant_null_max=float(abs(L@np.ones(len(m))).max()),passed=bool(rel.max()<.03 and abs(res).max()<1e-7))
    save('metrics/LAPLACIAN_SYNTHETIC_CONSISTENCY.json',result);assert result['passed'];print('SPECTRAL_CONTROL_PASS',float(rel.max()))
if __name__=='__main__':main()
