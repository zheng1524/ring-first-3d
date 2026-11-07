"""Post-freeze replay of saved rejected candidates; never used to rank/train."""
from contour_objective import *
import argparse

def main():
 guard_optimizer();name='G03';c=Case(name);ch=FreeVertices(c);obj=Objective(c,ch);rows=[];folder=R/'local_results'/name
 for p in sorted(folder.glob('REJECTED_FIRST_*.npz')):
  a=np.load(p);obj.attempt=int(a['attempt']);before=a['before_V'];q=tensor(before-c.V,torch.float64)
  with torch.no_grad():L0,p0=obj(q);L1,p1=obj(tensor(a['parameters'],torch.float64))
  row=dict(case=name,arm=R.name,saved_rejection=p.name,reasons=a['reason'].tolist(),attempt=int(a['attempt']),before_total=float(L0),candidate_total=float(L1),same_current_weight=True,initial_replay_world_error_mm=float(np.max(abs(ch.vertices(q).detach().cpu().numpy()-before))),before_parts=p0,candidate_parts=p1,deltas={k:p1[k]-p0[k]for k in ['silhouette','absolute','relative','prior','foreground_miss','background_false','contour_distance','added_loss']if k in p0 and k in p1},diagnostic_only_after_selection=True,GT_read=False);rows.append(row)
 save('metrics/G03_REJECTED_LOSS_BREAKDOWN.json',rows);print(R.name,[(x['saved_rejection'],x['deltas'])for x in rows],flush=True)
if __name__=='__main__':main()
