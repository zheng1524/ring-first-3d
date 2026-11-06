from common import *
import subprocess

def main():
 assert load(R/'metrics/PREFLIGHT.json')['passed'];assert load(R/'metrics/PROJECTION_GATE.json')['passed'];assert all(x['nonadjacent_self_N']==0 for x in load(R/'metrics/INITIAL_BLENDER.json'));assert not list((R/'local_results').glob('*/FINAL.npz'))
 for a in load(R/'assets_index/HISTORY_PROTECTION.json'):assert sha(a['path'])==a['sha256'],a['path']
 # Initialization objective files, not later guard helpers, must still match their preregistration.
 early=load(R/'assets_index/INIT_PROTOCOL_FREEZE.json');core=['prepare_caps.py','parametric.py','fit_body.py','p3d.py','components.py','depth_terms.py']
 for a in early['files']:
  if Path(a['path']).parent==R/'code'and Path(a['path']).name in core:assert sha(a['path'])==a['sha256'],a['path']
 case=load(R/'metrics/C_INHERITANCE.json');assert sum(x['needs_cap']for x in case)==7;assert all(x['underground_vertex_N']==0 for x in case if x['needs_cap']);assert sum(x['action']=='EXACT_FROZEN_C_REUSED'for x in case)==7
 cfg=load(R/'config/PROTOCOL.json');cfg['trust']['max_total_displacement_over_D']=.25;cfg['trust']['D_definition']='maximum extent of retained INITIAL visible surface; no volume truth';save('config/PROTOCOL.json',cfg)
 files=[asset(p)for folder in['code','config','inputs','depth_observations']for p in sorted((R/folder).rglob('*'))if p.is_file()]+[asset(R/'01_PROTOCOL.md')]+[asset(R/'figures'/p)for p in['Fig1_Nine_B_to_C_Initialization.png','Fig2_G05_G09_Cap_Repair.png']];save('assets_index/PREOPT_FREEZE.json',dict(files=files,time_epoch=time.time(),formal_optimizer_steps=0,GT_read=False,C_initialized_and_visually_audited=True,nine_cases_locked=True,initialization_source='009C; only untruncated broad-contact exceptions refit'))
 save('assets_index/IMPLEMENTATION_NOTES.json',dict(preflight_setup_corrections=['preflight helper import self_intersections added after initial NameError; no formal optimizer steps','read-only normal array copied before torch conversion; no numerical/model change'],old_guard_reuse='PMGR signed-distance and reversible proposal mechanism; coplanar SAT added to distinguish actual coplanar overlap',type_specific_branch=False,ring_baseline_epsilon_mm=1e-5))
 print('MAIN_FROZEN',len(files),flush=True)
if __name__=='__main__':main()
