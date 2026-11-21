"""Traceable fixed-scale auxiliary 3D landmark proposal, never final GT."""
from common import *
from scipy.spatial.transform import Rotation
def rigid(A,B):
 a=A.mean(0);b=B.mean(0);rot,_=Rotation.align_vectors(A-a,B-b);H=np.eye(4);H[:3,:3]=rot.as_matrix();H[:3,3]=a-H[:3,:3]@b;return H
def main():
 p=load(R/'features/CROSS_NAMED_3D_TRACK_PAIRS.json')['matches'];A=np.array([x['X004']for x in p]);B=np.array([x['X005']for x in p]);rng=np.random.default_rng(20261111);c=[]
 if len(p)>=3:
  for i in range(256):
   idx=rng.choice(len(p),3,replace=False);H=rigid(A[idx],B[idx]);d=np.linalg.norm(A-(B@H[:3,:3].T+H[:3,3]),axis=1);c.append((int((d<=.75).sum()),float(np.median(d)),H,d))
  best=min(c,key=lambda a:(-a[0],a[1]));keep=best[3]<=.75;H=rigid(A[keep],B[keep])if keep.sum()>=3 else best[2];d=np.linalg.norm(A-(B@H[:3,:3].T+H[:3,3]),axis=1);count=int((d<=.75).sum());center=float(np.linalg.norm(H[:3,3]));tilt=float(np.degrees(np.arccos(np.clip(abs(H[2,2]),-1,1))));feasible=bool(count>=8 and count/len(p)>=.5 and center<=1.2 and tilt<=10);save('metrics/NAMED_LANDMARK_RIGID_PROPOSAL.json',dict(T=H,named_pairs=len(p),within_075mm=count,residual_mm=stats(d),Ringcenter_mm=center,Ring_normal_tilt_deg=tilt,feasible_extra_candidate=feasible,scale=1.,source='SciPy Rotation.align_vectors + fixed256 RANSAC trials on ACTUAL named landmark pairs, no nearest-point assignment',GT=False,body=False,not_final_selection=True));print('NAMED_3D_PROPOSAL',len(p),count,center,tilt,feasible,flush=True)
if __name__=='__main__':main()
