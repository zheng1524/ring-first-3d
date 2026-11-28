"""Post-freeze objective probes and upstream camera-quality summaries; never replace predictions."""
from fit import *
from visualize import load_views
def main():
 rows=[]
 for item in read(M4/'GROUP_INDEX.json')['groups']:
  g=item['group'];root=T/'runs/results'/g
  if not(root/'GROUP_RESULT.json').exists():continue
  group=read(root/'GROUP_RESULT.json');joint=next((r for r in group['results']if r['configuration']=='JOINT'),None)
  if joint is None:continue
  fs,ss=load_views(g,joint);base=read(root/'JOINT/BASE.json');plane=np.array(base['plane'])if joint['base_applied']else None;prob=Problem([f for f in fs if f['role']=='FIT'],ss,np.array(joint['initial_p']),plane);b=np.array([r['b_mm']for r in joint['bias']]);value=sum(prob.values(np.array(joint['p']),b).values());expected=joint['stages'][-1]['objective_after'];assert abs(value-expected)<1e-7
  probes=[]
  for single in group['results']:
   if single['configuration']=='JOINT':continue
   p=np.array(single['p']);parts=prob.values(p,b);probes.append(dict(configuration=single['configuration'],objective_with_joint_b_fixed=sum(parts.values()),within_joint_bounds=bool(((p>=prob.lo)&(p<=prob.hi)).all()),components=parts,center_to_joint_mm=float(np.linalg.norm(p[:3]-np.array(joint['p'][:3])))))
  a=read(T/'runs/inputs'/g/'AUDIT.json');quality=[]
  for v in a['videos']:
   gates=read(Path(v['run'])/'metrics/GATES.json');q=[x for x in gates if x['id']in[f['id']for f in fs if f['case']==v['case']]];errors=[x['metrics']['held_reprojection']['MAE']for x in q if x.get('metrics',{}).get('held_reprojection',{}).get('MAE')is not None]
   quality.append(dict(case=v['case'],sampled_frames=len(q),R1_new_pass=sum(bool(x.get('new_pass'))for x in q),R1_held_MAE_px_median=float(np.median(errors))if errors else None,gate_reasons=sorted({reason for x in q for reason in x.get('reasons',[])})))
  row=dict(group=g,official_joint_objective=value,single_parameter_probes=probes,any_feasible_single_has_lower_objective=any(p['within_joint_bounds']and p['objective_with_joint_b_fixed']<value-1e-6 for p in probes),upstream_quality=quality,not_optimization=True,prediction_replaced=False)
  save(root/'POST_FREEZE_DIAGNOSTIC.json',row);rows.append(row)
 save(T/'evidence/POST_FREEZE_DIAGNOSTICS.json',rows);print('DIAGNOSTICS',len(rows),sum(r['any_feasible_single_has_lower_objective']for r in rows),flush=True)
if __name__=='__main__':main()
