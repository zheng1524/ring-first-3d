"""Bounded amendment, separate source/run record; preserves all original arms."""
from pilot_driver import setup,scores,select,MASTER,PYTHON
from common import *
import subprocess

def setup_control(tag,loss='A0',optimizer='O0',pilot=True,total=None):
 root=setup(tag,loss,optimizer,pilot);cfg=load(root/'config/PROTOCOL.json')
 if total is not None:cfg['total_trust_D']=total
 cfg['control_amendment']=asset(MASTER/'config/CONTROL_AMENDMENT_001.json');save(root/'config/PROTOCOL.json',cfg);f=load(root/'assets_index/PREOPT_FREEZE.json');f['files']=[asset(x['path'])if x['path']==str(root/'config/PROTOCOL.json')else x for x in f['files']]
 if optimizer=='O3N':f['files'] +=[asset(MASTER/'code/train_normalized.py'),asset(MASTER/'code/normalized_local.py'),asset(MASTER/'config/CONTROL_AMENDMENT_001.json'),asset(MASTER/'02_OPTIMIZER_SCALE_AMENDMENT.md')]
 f['epoch']=time.time();save(root/'assets_index/PREOPT_FREEZE.json',f);return root

def run(root,n,exact=False):
 if(root/'local_results'/n/'FINAL.npz').exists()and(root/'metrics'/(n+'_RUN.json')).exists():return
 cfg=load(root/'config/PROTOCOL.json');script=MASTER/'code'/('train012_exact.py'if exact else'train_normalized.py'if cfg['optimizer_arm']=='O3N'else'train.py');env=dict(os.environ,E4_RUN_DIR=str(root))
 with(root/'runtime'/(n+'.log')).open('w')as f:subprocess.run([PYTHON,'-B',str(script),n],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 print('FINISHED',root.name,n,flush=True)

def main():
 cfg=load(MASTER/'config/PROTOCOL.json');cases=cfg['pilot_cases'];ss={}
 for loss in ['A0','A1','A2','A3']:
  root=MASTER/'arms'/('PILOT_'+loss)
  for n in cases:assert(root/'metrics'/(n+'_RUN.json')).exists()
  ss[loss]=scores(root,cases)
 optss={'O0':ss['A0']}
 for opt in ['O1','O2','O3','O4']:
  root=MASTER/'arms'/('PILOT_'+opt)
  if not(root/'config/PROTOCOL.json').exists():root=setup('PILOT_'+opt,'A0',opt)
  for n in cases:run(root,n)
  optss[opt]=scores(root,cases)
 # Only one additional standalone optimizer control.
 root=setup_control('PILOT_O3N','A0','O3N')
 for n in cases:run(root,n)
 optss['O3N']=scores(root,cases)
 loss,lr=select(ss,ss['A0']);opt,orr=select(optss,ss['A0']);save(MASTER/'metrics/PILOT_SELECTION.json',dict(loss=loss,optimizer=opt,loss_comparison=lr,optimizer_comparison=orr,FIT_only=True,GT_read=False,HOLDOUT_used_for_selection=False,amendment=asset(MASTER/'config/CONTROL_AMENDMENT_001.json'),epoch=time.time()))
 combo=setup_control('COMBINED_VERIFY',loss,opt)
 for n in cases:run(combo,n)
 a=scores(combo,cases)
 amended=setup_control('AMENDED_A3_O3N_1D','A3','O3N',True,1.)
 for n in cases:run(amended,n)
 b=scores(amended,cases);which,cr=select({'BASELINE':ss['A0'],'COMBINED_VERIFY':a,'AMENDED_A3_O3N_1D':b},ss['A0'])
 roots={'BASELINE':MASTER/'arms/PILOT_A0','COMBINED_VERIFY':combo,'AMENDED_A3_O3N_1D':amended};chosen=load(roots[which]/'config/PROTOCOL.json');loss,opt,total=chosen['loss_arm'],chosen['optimizer_arm'],chosen['total_trust_D'];selection=dict(loss=loss,optimizer=opt,total_trust_D=total,combination=which,combo_check=cr,GT_read=False,selection_scope='predeclared FIT only plus one explicit preGT dimension amendment; general evidence separate',epoch=time.time());save(MASTER/'config/SELECTED_FINAL.json',selection)
 exact=setup('REPLAY_012_FULL','A0','O0',False)
 for n in ['G03','G01','G02','G10','G11']:run(exact,n,True)
 final=setup_control('FINAL_UNIFORM',loss,opt,False,total)
 for n in cfg['cases']:run(final,n)
 save(MASTER/'runtime/ALL_PREDICTIONS_COMPLETED.json',dict(cases=cfg['cases'],selected=selection,GT_read=False,epoch=time.time()));print('ALL_OPTIMIZATION_COMPLETED_NO_GT',flush=True)
if __name__=='__main__':main()
