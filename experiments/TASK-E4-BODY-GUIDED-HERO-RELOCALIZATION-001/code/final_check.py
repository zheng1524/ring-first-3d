from common import *
import struct,ast

def main():
 errors=[];fr=load(R/'provenance/ALL_REAL_PREDICTIONS_FROZEN.json');v=load(R/'metrics/VALIDATION.json');sources=load(R/'config/REAL_SOURCES.json');checks={}
 checks['numeric_states_150']=len(fr['results'])==150 and len(v)==150;checks['source_ids_75']=len(sources)==75 and len(set(s['id']for s in sources))==75
 checks['frozen_candidate_hashes']=all(sha(x['result']['path'])==x['result']['sha256']for x in fr['results']);sf=load(R/'provenance/REAL_SOLVER_CODE_FREEZE.json');checks['solver_and_protocol_unchanged']=all(sha(x['path'])==x['sha256']for x in sf['code']+[sf['protocol'],sf['sources'],sf['bodies']])
 checks['original_assets_and_Bodies_unchanged']=load(R/'provenance/FINAL_IMMUTABILITY_CHECK.json')['passed'];checks['rigid_contract']=load(R/'metrics/NUMERICAL_CONTRACT_TESTS.json')['pass_contracts'];checks['A1_exact_replay']=all(load(R/'metrics'/(g+'_A1_REPLAY.json'))['parameters_max_difference']==0 for g in ['G03','G05','G01','G06']);checks['four_core_images']=len(list((R/'figures').glob('Fig*.png')))==4
 checks['E_U_same_source_sets']=set(x['source']for x in v if x['Body']=='Body-E')==set(x['source']for x in v if x['Body']=='Body-U');checks['all_TRUSTED_faces_retained']=all(x['retained_face_ratio']==1 for x in load(R/'metrics/SOURCE_SHAPE_RETENTION.json'))
 glbs=[]
 for g in ['G03','G05','G01','G06']:
  p=R/'local_results'/g/(g+'_ALL_LAYERS.glb')
  with p.open('rb')as f:
   magic,version,length=struct.unpack('<4sII',f.read(12));size,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(size))
  glbs.append(dict(group=g,magic=magic.decode(),version=version,meshes=len(data['meshes']),expected_mesh_layers=4*sum(s['group']==g for s in sources)+3,valid=magic==b'glTF'and length==p.stat().st_size))
 checks['GLB_four_groups_and_layers']=all(x['valid']and x['meshes']==x['expected_mesh_layers']for x in glbs)
 for p in (R/'code').glob('*.py'):ast.parse(p.read_text())
 checks['code_syntax']=True;save('provenance/FINAL_CONSISTENCY_CHECK.json',dict(epoch=time.time(),checks=checks,GLB=glbs,engineering_checks_passed=all(checks.values()),scientific_success=False,numeric_candidates=len(v),conditional_constraint_supported=sum(x['accepted_H']is not None for x in v),controlled_scientific_failures_preserved=True,real_absolute_accuracy='NOT_EVALUABLE'));assert all(checks.values()),checks;print(checks)
if __name__=='__main__':main()
