"""Read-only post-freeze objective decomposition, no backward or optimizer calls."""
from stable import *

def main():
 guard_optimizer()
 for a in load(R/'assets_index/PREDICTIONS_FROZEN.json')['files']:assert sha(a['path'])==a['sha256']
 rows=[]
 for name in load(R/'config/PROTOCOL.json')['cases']:
  c=Case(name);ch=Chart(c)
  def verify_support(path,**arrays):
   saved=np.load(path);assert set(saved.files)==set(arrays)
   for k,v in arrays.items():assert np.array_equal(saved[k],v),(name,k,'support replay mismatch')
  original_save=np.savez_compressed
  try:
   np.savez_compressed=verify_support;obj=Objective(c,ch)
  finally:np.savez_compressed=original_save
  for label in ['INITIAL','FINAL']:
   q=np.zeros(54)if label=='INITIAL'else np.load(R/'local_results'/name/'FINAL.npz')['parameters']
   with torch.no_grad():total,parts=obj(tensor(q,torch.float64))
   row=dict(case=name,label=label,total=float(total),silhouette=parts['silhouette'],prior=parts['prior'],absolute_raw=parts['absolute'],relative_raw=parts['relative'],weighted_absolute=.01*parts['absolute'],weighted_relative=.01*parts['relative'],depth=parts['depth'],optimizer_steps=0,postfreeze_readonly=True)
   if label=='FINAL':
    row['replay_difference']=abs(row['total']-load(R/'metrics'/(name+'_TRAINING.json'))[-1]['accepted_loss']);row['replay_within_training_tolerance']=row['replay_difference']<=1e-7
   rows.append(row)
  print('OBJECTIVE_REPLAY',name,flush=True)
 for a in load(R/'assets_index/PREDICTIONS_FROZEN.json')['files']:assert sha(a['path'])==a['sha256']
 save('metrics/FULL_OBJECTIVE_COMPONENTS.json',rows);table('metrics/FULL_OBJECTIVE_COMPONENTS.csv',rows)

if __name__=='__main__':main()
