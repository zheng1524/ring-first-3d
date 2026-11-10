from objective019 import *
from evaluate019 import methods

def main():
 assert(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json').exists();vv=load(R/'config/VIEWS.json');neg=load(R/'config/NEGATIVE_SPLIT.json');rows=[]
 for scope in ['CROSS','NEGATIVE']:
  for role in ['FIT','HOLDOUT']:
   ids=[v['id']for v in vv if v['video']=='005'and v['role']==role]if scope=='CROSS'else neg['target_fit'if role=='FIT'else'target_holdout'];feat=FeatureLoss(scope if role=='FIT'else scope+'_HOLDOUT',ids)
   with torch.no_grad():
    for meth in methods(scope):
     value,s=feat(tensor(meth['T'],torch.float64),True);rows.append(dict(scope=scope,role=role,method=meth['tag'],normalized_robust_feature_loss=float(value),**s))
 save('metrics/SIFT_GEOMETRIC_EVALUATION.json',rows);table('metrics/SIFT_GEOMETRIC_EVALUATION.csv',rows);print('FROZEN_SIFT_FIT_HOLDOUT_EVALUATION_COMPLETE',flush=True)
if __name__=='__main__':main()
