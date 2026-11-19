"""Copy original frozen identities; never reselect views or regenerate historical results."""
from _bootstrap import ROOT
from pathlib import Path
import json,yaml,shutil,datetime
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.contour_contracts import TASK_ID,BASELINE,CONTOUR_STAGES,MODULE_FILES
from ring_first_3d.policy.contracts import MODULES

def main():
 td=ROOT/'experiments'/TASK_ID;assert not(td/'TASK.yaml').exists();td.mkdir(parents=True,exist_ok=True);old=Path('/home/liu/ring_first_3d_multivideo_init_a/experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001');t=yaml.safe_load((old/'TASK.yaml').read_text());inp=td/'inputs';inp.mkdir();(td/'legacy015').mkdir();rec=lambda p:dict(path=str(p),sha256=sha256(p));code=[]
 for p in sorted((old/'legacy015').glob('*.py')):
  q=td/'legacy015'/p.name;shutil.copyfile(p,q);prior=next(r for r in json.loads((old/'inputs/CODE_LOCK.json').read_text())['files']if Path(r['path']).name==p.name);code.append(dict(prior,path=str(q)))
 (inp/'CODE_LOCK.json').write_text(json.dumps(dict(commit=t['inita']['legacy_commit'],files=code),indent=2)+'\n');shutil.copyfile(old/'inputs/SOURCES.json',inp/'SOURCES.json');(td/'evaluation_only').mkdir();shutil.copyfile(old/'evaluation_only/GT_META.json',td/'evaluation_only/GT_META.json');shutil.copyfile(old/'inputs/INIT_A_ALL_IP_SOURCE_REVIEW.png',inp/'INIT_A_ALL_IP_SOURCE_REVIEW.png')

 for key,r in t['inputs'].items():
  if isinstance(r,dict) and 'path'in r and str(r['path']).startswith(str(old.parents[1])):
   r['path']=str(ROOT/Path(r['path']).relative_to(old.parents[1]))
 i=t['inita'];i['assets']['sources']=rec(inp/'SOURCES.json');i['assets']['code_lock']=rec(inp/'CODE_LOCK.json');i['assets']['GT_metadata']=rec(td/'evaluation_only/GT_META.json');i['assets']['Ip_source_review']=rec(inp/'INIT_A_ALL_IP_SOURCE_REVIEW.png');baseline={};assets=[rec(old/'TASK.yaml'),rec(old/'TASK_FREEZE.json')]
 for g in i['cases']:
  baseline[g]={}
  for arm in ['A0','A2']:
   p=old/'review_meshes'/g/(arm+'_WORLD.npz')
   if p.is_file():baseline[g][arm]=rec(p);assets.append(rec(p))
 t.update(schema=8,task_id=TASK_ID,goal='Explicit bidirectional normal-contour E/M on frozen 013 shared Init-A, then real Mesh-boundary HERO controls; all cameras fixed',modules=list(MODULES)+list(MODULE_FILES),output_root=str(td/'runs'));t['authorization'].update(reference='Explicit user '+TASK_ID,stages=list(CONTOUR_STAGES));t['acceptance']['required_stages']=list(CONTOUR_STAGES);t['budget']=dict(max_seconds=14400,stage_timeout_seconds=7200,max_attempts_per_stage=2,max_output_bytes=4000000000);i['smoke_cases']=['G01','G05','G11'];i['arms']=['A0','A2','A2D','A3'];i['camera_parameters']='ALL_FIXED'
 t['contour']=dict(parent_commit=BASELINE,Body_arms=['A0','A2','A2D','A3'],HERO_methods=['M0','H1','H2','H3','H4','ICP'],smoke_cases=['G01','G05','G11'],camera_parameters='ALL_FIXED',A3_depth_loss=False,HERO_updates_Body=False,pairing=dict(max_distance_px=40.,mutual_radius_px=4.,max_tangent_px=8.,normal_cos_min=0.7071067811865476),baseline_assets=assets,baseline_meshes=baseline,tracking='edge IDs + interpolation + direction; accepted-pair target displacement retained',E_M='all FIT detached assignments at gradient start; candidates evaluate fixed assignment; rebuild after every accepted change before next proposal; final explicit rebuild',new_loss_coefficient=.01,loss_control='A2D: same2D-only loss using original ContourDistance; same renderer/FG/FP/prior',HERO_mapping='visible actual Mesh contour; mutual normal boundary pairs; local inverse-distance boundary transfer; visible actual ray Face/bary; no ellipse',GT_identity='immutable source identities only before predictor freeze; GT geometry evaluator only')
 (td/'TASK.yaml').write_text(yaml.safe_dump(t,sort_keys=False,allow_unicode=True));(td/'TASK_FREEZE.json').write_text(json.dumps(dict(task_sha256=sha256(td/'TASK.yaml'),parent_commit=BASELINE,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),no_GT_selection=True,unchanged_views_split_camera_topology_budget=True),indent=2)+'\n');print(td/'TASK.yaml')
if __name__=='__main__':main()
