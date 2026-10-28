from scene_renderer import *
def main():
    checks=[]
    def check(n,x):assert x,n;checks.append(n)
    a,m,rp=layers('G01_005_raw00459');pc,bc,meta,Z=depth_colors(a);C=np.r_[pc,bc];valid=np.isfinite(Z)&(Z>0);L=(C.max(1)+C.min(1))/2;order=np.argsort(Z[valid]);t=(Z-meta['min_Z_mm'])/(meta['max_Z_mm']-meta['min_Z_mm']);check('shared physical min/max from both retained layers',meta['min_Z_mm']==float(Z[valid].min())and meta['max_Z_mm']==float(Z[valid].max()));check('same lightness law for both hues',np.allclose(L[valid],.82-.55*t[valid]));check('near brighter, far darker, no ordering reversals',np.all(np.diff(L[valid][order])<=1e-12));check('Polyp pink identity R>G',np.all(pc[:,0]>pc[:,1]));check('Background teal identity G>R',np.all(bc[:,1]>bc[:,0]));check('point count unchanged',len(pc)==len(a['Polyp_XYZ_mm'])and len(bc)==len(a['Background_XYZ_mm']));check('no display color outside RGB domain',np.all((C>=0)&(C<=1)))
    both('small_tests',[dict(check=n,passed=True)for n in checks]);print('SMALL_TESTS_PASS',len(checks))
if __name__=='__main__':main()
