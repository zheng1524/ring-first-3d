from common import *
def main():
 rows=[]
 for rec in load(R/'evaluation/metrics/COMPARISON.json'):
  if rec['status']=='MISSING_FINAL':continue
  g,arm=rec['group'],rec['arm']
  for role in ['FIT','HOLDOUT']:
   arr=[]
   for v in load(R/'config/VIEW_PLAN.json'):
    if v['group']==g and v['role']==role:
     a=np.load(R/'evaluation/local_results'/g/arm/(v['view_id']+'_EVAL.npz'));active=a['active'];arr.append(a['z'][active]-a['z_H'][active])
   rows.append(dict(group=g,arm=arm,role=role,definition='all active original native first-hit rays pooled without subsampling; misses separately preserved in COMPARISON.csv fixed denominator',**stats(np.concatenate(arr))))
 save('evaluation/metrics/POOLED_NATIVE_DEPTH_RESIDUALS.json',rows);table('evaluation/metrics/POOLED_NATIVE_DEPTH_RESIDUALS.csv',rows)
if __name__=='__main__':main()
