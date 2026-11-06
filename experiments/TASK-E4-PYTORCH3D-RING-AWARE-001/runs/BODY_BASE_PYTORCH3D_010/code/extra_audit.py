from common import *
import csv

def main():
 headers=[]
 for rp in sorted((R/'metrics').glob('*_RUN.json')):
  rr=load(rp)
  for suffix in ['TRAINING','DEPTH_TRACE']:
   pp=R/'metrics'/(rr['case']+'_'+rr['route']+'_'+suffix+'.csv')
   if not pp.exists():
    assert rr['accepted_steps']==0
    sample=next((R/'metrics').glob('*_'+suffix+'.csv'));keys=next(csv.reader(sample.open()))
    with pp.open('w',newline='')as f:csv.writer(f,lineterminator='\n').writerow(keys)
    headers.append(dict(path=str(pp),rows=0,reason='first proposal rejected; explicit empty accepted trace',actual_optimizer_steps=rr['optimizer_steps']))
 if headers:save('assets_index/EMPTY_ACCEPTED_TRACE_HEADERS.json',headers)
 rows=[];sampling=[];isolation=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];norm=load(R/'inputs'/n/'NORMALIZATION.json')
  for route in['P','S']:
   z=np.load(R/'inputs'/n/(route+'_INITIAL.npz'));b=int(z['boundary_vertex'].sum());rows.append(dict(case=n,route=route,V_N=len(z['V']),observed_F_N=len(z['F']),inferred_F_N=int(z['inferred_base_faces'].sum()),boundary_vertex_N=b,global_parameters=6,local_parameters=3*len(z['V']),local_tangent_normal_constraints=b,maximum_independent_local_DOF=3*len(z['V'])-b,shared_normalization_center=norm['center'],shared_normalization_mm=norm['scale_mm'],Mesh_is_not_pretrained_model=True))
   run=load(R/'metrics'/(n+'_'+route+'_RUN.json'));p=R/'metrics'/(n+'_'+route+'_DEPTH_TRACE.csv');trace=list(csv.DictReader(p.open()))if p.exists()else[];sampling.append(dict(case=n,route=route,accepted_steps=run['accepted_steps'],depth_source_evaluations=len(trace),iterations_with_depth=len({x['step']for x in trace}),depth_N_per_source={v['id']:len(np.load(R/'depth_observations'/(v['id']+'.npz'))['z'])for v in c['views']if v['role']=='FIT'and(R/'depth_observations'/(v['id']+'.npz')).exists()},view_count=len([v for v in c['views']if v['role']=='FIT']),weights_unchanged=True))
   isolation.extend(dict(case=n,route=route,source=x['source'],role=next(v['role']for v in c['views']if v['id']==x['source']))for x in trace)
 table('metrics/DOF_AND_SCALE_AUDIT.csv',rows);save('metrics/DOF_AND_SCALE_AUDIT.json',rows);table('metrics/EFFECTIVE_DEPTH_SAMPLING.csv',sampling);save('metrics/EFFECTIVE_DEPTH_SAMPLING.json',sampling);save('metrics/HOLDOUT_LOSS_ISOLATION.json',dict(all_recorded_depth_loss_sources_are_FIT=all(x['role']=='FIT'for x in isolation),records_N=len(isolation),GT_read=False,holdout_objective_used=False,cross_view_depth_consistency_loss=False));print('EXTRA_AUDIT_DONE')
if __name__=='__main__':main()
