"""Known-coordinate control, NOT a real cross-video registration claim."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from snapshot import load_snapshot,move_video
from pilot import TASK
from ring_first_3d.sim.geometry import se3,rigid_fit,transform,pose_error
from ring_first_3d.contracts.coordinates import project

def main():
    a=load_snapshot();H=se3([.12,-.18,.25,3.,-2.,1.5]);b=move_video(a,H)
    # Existing paired-landmark Kabsch; synthetic identity pairs are explicit.
    ids=np.arange(len(a['landmarks']));fit=ids[::2];held=ids[1::2]
    T=rigid_fit(b['landmarks'][fit],a['landmarks'][fit]);registered=move_video(b,T)
    residual=np.linalg.norm(registered['landmarks'][held]-a['landmarks'][held],axis=1)
    per=[]
    for i,f in enumerate(a['frames']):
        uv,_=project(a['hero'],f['K'],a['cameras'][i]);same,_=project(b['hero'],f['K'],b['cameras'][i]);after,_=project(registered['hero'],f['K'],registered['cameras'][i])
        per.append(dict(id=f['id'],transport_projection_max_px=float(abs(uv-same).max()),recovery_projection_max_px=float(abs(uv-after).max())))
    baseline=max(float(abs(np.linalg.inv(a['cameras'][0])@a['cameras'][i]-np.linalg.inv(b['cameras'][0])@b['cameras'][i]).max()) for i in range(4))
    # Three disjoint landmark subsets check transform consistency, not independent videos.
    transforms=[rigid_fit(b['landmarks'][ids%3==j],a['landmarks'][ids%3==j]) for j in range(3)]
    consistency=[pose_error(t@H) for t in transforms]
    ring_error=float(np.linalg.norm(registered['ring']-a['ring'],axis=1).max())
    result=dict(status='CONTROL_PASS',real_registration='NOT_EVALUABLE',physical_groups=1,real_videos=1,synthetic_coordinate_frames=2,scale=1.,GT_read=False,landmark_pairs='same retained reference landmark IDs; known synthetic correspondence',fit_landmarks=len(fit),held_landmarks=len(held),landmark_holdout_max_mm=float(residual.max()),ring_recovery_max_mm=ring_error,hero_recovery_max_mm=float(np.linalg.norm(registered['hero']-a['hero'],axis=1).max()),relative_camera_max_abs=baseline,recovery_error=pose_error(T@H),subset_consistency=consistency,per_frame=per,known_A_to_B=H.tolist(),estimated_B_to_A=T.tolist(),limitations=['No real 004/005 common landmark identities verified','Ring axial symmetry does not determine yaw','Subset tests and four frame projections share one synthetic transform; not independent registration evidence'])
    assert residual.max()<1e-9 and ring_error<1e-9 and baseline<1e-10
    assert max(r['transport_projection_max_px'] for r in per)<1e-8
    out=TASK/'evidence';(out/'RIGID_CONTROL.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,axes=plt.subplots(2,4,figsize=(16,8))
    for i,f in enumerate(a['frames']):
        for j,s in enumerate([b,registered]):
            uv,z=project(s['hero'],f['K'],a['cameras'][i]);ax=axes[j,i];ax.imshow(f['RGB']);ax.scatter(uv[::40,0],uv[::40,1],s=1,c='#00ffff');ax.set_xlim(0,639);ax.set_ylim(359,0);ax.axis('off');ax.set_title(f['id']+'\n'+('B local in A camera (unregistered)' if j==0 else 'T(B) in A camera'))
    fig.suptitle('KNOWN SE3 CONTROL | actual RGB + sampled native HERO vertices | mm world | GT not used');fig.tight_layout();fig.savefig(out/'RIGID_PROJECTIONS.png',dpi=130);plt.close(fig)
    fig=plt.figure(figsize=(12,5));allp=np.r_[a['hero'],b['hero'],a['ring'],b['ring']];lo=allp.min(0);hi=allp.max(0);center=(lo+hi)/2;radius=max(hi-lo)/2
    for i,s in enumerate([b,registered]):
        ax=fig.add_subplot(1,2,i+1,projection='3d');ax.plot_trisurf(*a['hero'].T,triangles=a['faces'],color='#4488bb',alpha=.75,linewidth=0,shade=False);ax.plot_trisurf(*s['hero'].T,triangles=s['faces'],color='#ff8844',alpha=.75,linewidth=0,shade=False);ax.scatter(*a['ring'][::100].T,s=1,c='gray');ax.set(xlim=(center[0]-radius,center[0]+radius),ylim=(center[1]-radius,center[1]+radius),zlim=(center[2]-radius,center[2]+radius),xlabel='x mm',ylabel='y mm',zlabel='z mm',title='Before (different coordinate frames)' if i==0 else 'After recovered video SE3');ax.set_box_aspect([1,1,1])
    fig.suptitle('KNOWN SE3 CONTROL | blue=A, orange=B | same mm axes | GT absent');fig.tight_layout();fig.savefig(out/'RIGID_SURFACES.png',dpi=130);plt.close(fig)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
