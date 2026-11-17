"""Post-freeze endpoint proposal diagnosis only; never commits a new prediction."""
from ba021 import *
from geometry021 import wait_freeze
from scipy.spatial.transform import Rotation
def main():
 wait_freeze();out=[];vv=load(R/'config/VIEWS.json');ids=[v['id']for v in vv if v['video']=='005'and v['role']=='FIT'];before=load(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json')['files']
 for arm in ['B1','B2','B3']:
  obj=BA('CROSS',ids,arm);s=torch.load(R/'optimization'/arm/'ITER_100.pt',map_location=device,weights_only=False);q=s['q'].detach().clone().requires_grad_(True);X=s['X'].detach().clone().requires_grad_(True);seed=s['seed'];params=[dict(params=[q],lr=.01)]+([dict(params=[X],lr=.02)]if arm!='B1'else[]);opt=torch.optim.Adam(params);opt.load_state_dict(s['Adam']);L,p=obj.evaluate(q,X,seed,True);gq=q.grad.detach().clone();gx=X.grad.detach().clone();oldq=q.detach().clone();oldX=X.detach().clone();oldH=obj.transform(q,seed).detach().cpu().numpy();opt.step();dq=q.detach()-oldq;dx=X.detach()-oldX if arm!='B1'else torch.zeros_like(oldX)
  repeat=[]
  with torch.no_grad():
   for _ in range(3):repeat.append(obj.evaluate(oldq,oldX,seed)[0])
   for mode in ['JOINT','POSE_ONLY','POINT_ONLY']:
    if arm=='B1'and mode=='POINT_ONLY':continue
    for alpha in [1.,.5,.125,1/128]:
     tq=oldq+alpha*dq if mode!='POINT_ONLY'else oldq;tx=oldX+alpha*dx if mode!='POSE_ONLY'else oldX;new,parts=obj.evaluate(tq,tx,seed);H=obj.transform(tq,seed).detach().cpu().numpy();D=H@np.linalg.inv(oldH);out.append(dict(arm=arm,mode=mode,alpha=alpha,old_loss=L,candidate_loss=new,delta_loss=new-L,old_parts=p,candidate_parts=parts,predicted_gradient_dot=float((gq*(tq-oldq)).sum()+(gx*(tx-oldX)).sum()),actual_delta_translation_mm=float(np.linalg.norm(D[:3,3])),actual_delta_rotation_deg=float(np.degrees(Rotation.from_matrix(D[:3,:3]).magnitude())),max_X_step_mm=float((tx-oldX).norm(dim=1).max()),fixed_state_repeat_loss_range=max(repeat)-min(repeat),not_optimizer_output=True,not_historical_trial_replay=True))
  print('SHADOW021',arm,flush=True)
 save('metrics/ENDPOINT_SHADOW_PROPOSALS.json',out);table('metrics/ENDPOINT_SHADOW_PROPOSALS.csv',out);assert all(sha(a['path'])==a['sha256']for a in before);save('runtime/SHADOW_COMPLETE.json',dict(epoch=time.time(),all_predictions_unchanged=True));print('SHADOW021_COMPLETE',flush=True)
if __name__=='__main__':main()
