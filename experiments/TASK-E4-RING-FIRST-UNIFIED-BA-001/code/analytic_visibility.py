"""Visibility of exact torus tangent loci from the same implicit torus equation.
Known tangent root t=1 is double. Divide it out, solve the remaining quadratic.
No mesh MISS rule and no change to RF physical parameters.
"""
from torus import *
def torus_polynomial(C,X):
 d=X-C;a=(d*d).sum(1);b=2*(d*C).sum(1);c=(C*C).sum()+5.6**2-.6**2
 coeff=np.stack([np.full(len(X),c*c-4*5.6**2*(C[0]**2+C[1]**2)),2*b*c-8*5.6**2*(C[0]*d[:,0]+C[1]*d[:,1]),b*b+2*a*c-4*5.6**2*(d[:,0]**2+d[:,1]**2),2*a*b,a*a],1)
 # ascending quotient by (t-1)^2: q2=p4,q1=p3+2q2,q0=p2+2q1-q2
 q2=coeff[:,4];q1=coeff[:,3]+2*q2;q0=coeff[:,2]+2*q1-q2;rem0=coeff[:,0]-q0;rem1=coeff[:,1]-q1+2*q0
 discriminant=q1*q1-4*q2*q0;real=discriminant>=0;ds=np.sqrt(np.maximum(discriminant,0));roots=np.stack([(-q1-ds)/(2*q2),(-q1+ds)/(2*q2)],1);front=(real[:,None]&(roots>1e-8)&(roots<1-1e-6)).any(1);near=(real[:,None]&(abs(roots-1)<1e-6)).any(1);states=np.where(front,1,np.where(near,2,0))
 return dict(states=states,roots=roots,real_roots=real,remainder=np.maximum(abs(rem0),abs(rem1))/np.maximum(abs(coeff).max(1),1),sdf=(np.hypot(np.linalg.norm(X[:,:2],axis=1)-5.6,X[:,2])-.6))
def main():
 rows=[]
 for v in load(N/'config/VIEWS.json'):
  C=np.array(v['T']);cr=curves(C,np.array(v['K']));X=cr['X'].reshape(-1,3);r=torus_polynomial(C[:3,3],X);rows.append(dict(group=v['group'],id=v['id'],visible_N=int((r['states']==0).sum()),occluded_N=int((r['states']==1).sum()),unknown_N=int((r['states']==2).sum()),max_polynomial_remainder=float(r['remainder'].max()),max_torus_surface_error_mm=float(abs(r['sdf']).max())))
 save('metrics/EXACT_TORUS_VISIBILITY.json',rows);table('metrics/EXACT_TORUS_VISIBILITY.csv',rows);print('analytic',len(rows),'maxoccluded',max(r['occluded_N']for r in rows),'maxremainder',max(r['max_polynomial_remainder']for r in rows))
if __name__=='__main__':main()
