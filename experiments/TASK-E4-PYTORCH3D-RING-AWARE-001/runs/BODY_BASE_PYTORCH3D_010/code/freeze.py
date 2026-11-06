from common import *
import inspect,subprocess
from p3d import *
from pytorch3d.utils import ico_sphere

def main():
 assert load(R/'metrics/PREFLIGHT.json')['passed']and load(R/'metrics/PROJECTION_GATE.json')['passed'];assert not list((R/'local_results').glob('*/*/FINAL.npz'))
 rec=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];s=load(R/'inputs'/n/'SPHERE_INITIALIZATION.json');s.pop('HERO_native_pixel_ids');b=load(R/'inputs'/n/'BASE_SELECTION.json');rec.append(dict(case=n,S=s,P=dict(input=str(R/'inputs'/n/'P_INITIAL.npz'),B_source=str(R.parent/'BODY_BASE_INIT_009/local_results'/n/'B_SELECTED.npz'),clipped=b['truncate_allowed'],plane=b['selected_plane'],base_status=b['base_status'],base_uncertain=b['uncertain_base'],contact=b['contact_status'])))
 save('config/INITIALIZATIONS.json',rec)
 sourcefile=Path(inspect.getsourcefile(ico_sphere));save('assets_index/FRAMEWORK_REUSE.json',dict(official_PyTorch3D_commit=subprocess.check_output(['git','-C',str(R.parents[1]/'runtime/pytorch3d'),'rev-parse','HEAD'],text=True).strip(),ico_sphere=asset(sourcefile),generator_is_not_pretrained_reconstruction=True,upstream=['BODY_BASE_INIT_009','VISIBILITY_ORDER_REPAIR_001','PROGRESSIVE_HERO_001','BOUNDARY_RELATIVE_DEPTH_D2_001'],changes=['unit/acute plane equivalence; no old file edit','exact B halfspace clipping and tagged cap','data-only sphere and common physical normalization','p3d.Case input route + same normalization; all rendering/aware math unchanged','Depth constructor FIT-only, skip RGB-only views','100global6+200local old schedule; cap boundary tangential constraint only when metadata present','same D2E3 losses/SGD/priors'],new_dependencies=False,new_HERO=False,new_camera_recovery=False))
 files=[asset(p)for sub in['code','config','inputs','depth_observations']for p in sorted((R/sub).rglob('*'))if p.is_file()]+[asset(R/'01_PROTOCOL.md')];save('assets_index/PREOPT_FREEZE.json',dict(files=files,time_epoch=time.time(),formal_optimizer_steps=0,real_GT_read=False,all_nine_cases_locked=True,arms=['P','S']))
 print('FROZEN',len(files),flush=True)
if __name__=='__main__':main()
