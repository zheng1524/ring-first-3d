"""Same-state full-gradient repeat control. No optimizer, no GT, no new prediction.

Run with E4_RUN_DIR pointing at arms/C4_ALL in an isolated reproduction.
Preserve the already recorded control rather than overwriting it.
"""
from multiview import *
def main():
 guard_optimizer();name='G02';dest=R/'metrics/G02_GRADIENT_REPEAT_CONTROL.json'
 assert not dest.exists(),'Preserve recorded evidence; reproduce in a fresh copy'
 c=Case(name);ch=FreeVertices(c);o=MultiObjective(c,ch,'D0_013');o.attempt=40;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True)
 v,_=o.compute(q,True);a=q.grad.detach().clone();v2,_=o.compute(q,True);b=q.grad.detach().clone();old=np.load(R/'metrics/G02_GRADIENT_DIAGNOSTIC.npz');summed=np.sum([old[k]for k in ['silhouette','missing','extra','contour','absolute','relative','prior']],axis=0)
 ans=dict(objective_repeat_difference=v2-v,full_repeat_abs=float((a-b).norm()),full_repeat_relative=float((a-b).norm()/b.norm()),split_vs_full_abs=float(np.linalg.norm(summed-b.cpu().numpy())),split_vs_full_relative=float(np.linalg.norm(summed-b.cpu().numpy())/b.norm()),full_norm=float(b.norm()),finite=bool(torch.isfinite(a).all()and torch.isfinite(b).all()),optimizer_updates=0,GT_used=False,original_additivity_test_is_still_FAIL=True)
 save('metrics/G02_GRADIENT_REPEAT_CONTROL.json',ans);print(ans)
if __name__=='__main__':main()
