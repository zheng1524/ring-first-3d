"""Serial fixed-budget pilots, FIT-only selection and one common final protocol."""
from arm_setup import *
import subprocess
PYTHON='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
def run(root,n,exact=False):
 log=root/'runtime'/(n+'.log');script=MASTER/'code'/('train012_exact.py'if exact else'train.py');env=dict(os.environ,E4_RUN_DIR=str(root));p=root/'local_results'/n/'FINAL.npz'
 if p.exists()and(root/'metrics'/(n+'_RUN.json')).exists():return
 with log.open('w')as f:subprocess.run([PYTHON,'-B',str(script),n],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 print('FINISHED',root.name,n,flush=True)
def scores(root,cases):
 env=dict(os.environ,E4_RUN_DIR=str(root))
 for n in cases:
  subprocess.run([PYTHON,'-B',str(MASTER/'code/fit_score.py'),n,str(root/'local_results'/n/'FINAL.npz')],env=env,stdout=subprocess.DEVNULL,check=True)
 return [load(root/'metrics'/(n+'_FIT_SCORE.json'))for n in cases]
def select(arms,baseline):
 out=[]
 for tag,s in arms.items():
  diff=[x['mean']['score']-b['mean']['score']for x,b in zip(s,baseline)];rec=[x['mean']['recall']-b['mean']['recall']for x,b in zip(s,baseline)];dep=[x['mean']['raw_fixed_depth_cost']-b['mean']['raw_fixed_depth_cost']for x,b in zip(s,baseline)];out.append(dict(arm=tag,mean_gain=float(np.mean(diff)),positive_cases=int(sum(d>1e-5 for d in diff)),recall_change=rec,depth_cost_change=dep,paired_score_gains=diff,eligible=min(rec)>=-.05 and max(dep)<=.5,general_evidence=sum(d>1e-5 for d in diff)>=3 and min(rec)>=-.05 and max(dep)<=.5))
 feasible=[x for x in out if x['eligible']];winner=max(feasible or out,key=lambda x:round(x['mean_gain']/1e-5))['arm'];return winner,out

def main():
 cfg=load(MASTER/'config/PROTOCOL.json');cases=cfg['pilot_cases'];ss={}
 for loss in ['A0','A1','A2','A3']:
  root=setup('PILOT_'+loss,loss)
  for n in cases:run(root,n)
  ss[loss]=scores(root,cases)
 optss={'O0':ss['A0']}
 for opt in ['O1','O2','O3','O4']:
  root=setup('PILOT_'+opt,'A0',opt)
  for n in cases:run(root,n)
  optss[opt]=scores(root,cases)
 loss,lr=select(ss,ss['A0']);opt,orr=select(optss,ss['A0']);save(MASTER/'metrics/PILOT_SELECTION.json',dict(loss=loss,optimizer=opt,loss_comparison=lr,optimizer_comparison=orr,FIT_only=True,GT_read=False,HOLDOUT_used_for_selection=False,epoch=time.time()))
 combo=setup('COMBINED_VERIFY',loss,opt)
 for n in cases:run(combo,n)
 cs=scores(combo,cases);_,cr=select({'combined':cs},ss['A0'])
 if not cr[0]['eligible']:loss,opt='A0','O0'
 selection=dict(loss=loss,optimizer=opt,combo_check=cr,combo_rejected=not cr[0]['eligible'],GT_read=False,selection_scope='predeclared FIT only; short pilots; general benefit not guaranteed',epoch=time.time());save(MASTER/'config/SELECTED_FINAL.json',selection)
 # Full 012 replication from identical initial states, no selection on these outputs.
 exact=setup('REPLAY_012_FULL','A0','O0',False)
 for n in ['G03','G01','G02','G10','G11']:run(exact,n,True)
 final=setup('FINAL_UNIFORM',loss,opt,False)
 for n in cfg['cases']:run(final,n)
 save(MASTER/'runtime/ALL_PREDICTIONS_COMPLETED.json',dict(cases=cfg['cases'],selected=selection,GT_read=False,epoch=time.time()))
 print('ALL_OPTIMIZATION_COMPLETED_NO_GT',flush=True)
if __name__=='__main__':main()
