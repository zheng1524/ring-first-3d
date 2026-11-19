"""Closed-body reverse CAD containment audit, complementary to surface FCL/dense tests."""
from geometry021 import *
def main():
 for group in ['G03','G05','G06','G01']:
  while not(R/'runtime'/(group+'_QUANTITATIVE_COMPLETE.json')).exists():time.sleep(5)
  g=next(g for g in load(R/'config/FOUR_GROUP_INPUTS.json')if g['group']==group);rv=np.load(g['ring']['path']);P=np.r_[rv['V'],rv['V'][rv['F']].mean(1)];quality={q['body']:q for q in load(R/'metrics/groups'/f'{group}_BODY_QUALITY.json')};rows=[]
  for name,b in g['bodies'].items():
   z=np.load(b['path']);valid=quality[name]['watertight']and quality[name]['winding_consistent']and quality[name]['self_intersection_pairs_N']==0
   if valid:
    sd=scene(z['V'],z['F_solid']).compute_signed_distance(o3d.core.Tensor(P.astype(np.float32)),nsamples=11).numpy();np.savez_compressed(R/'evaluation/groups'/group/(name+'_REVERSE_RING_CONTAINMENT.npz'),signed_distance_mm=sd,CAD_vertex_N=len(rv['V']),CAD_face_center_N=len(rv['F']),tolerance_mm=.001);rows.append(dict(group=group,body=name,status='CLOSED_MODEL_SAMPLE_PROXY',fixed_CAD_samples_N=len(P),CAD_vertices_inside_body_N=int((sd[:len(rv['V'])]<-.001).sum()),CAD_face_centers_inside_body_N=int((sd[len(rv['V']):]<-.001).sum()),min_CAD_to_body_signed_mm=float(sd.min()),tolerance_mm=.001,inferred_cap_in_closed_model=True,not_physical_truth=True))
   else:rows.append(dict(group=group,body=name,status='NOT_EVALUABLE_INVALID_CLOSED_MODEL',fixed_CAD_samples_N=len(P),CAD_vertices_inside_body_N=None,CAD_face_centers_inside_body_N=None,min_CAD_to_body_signed_mm=None))
  save('metrics/groups/'+group+'_REVERSE_RING_CONTAINMENT.json',rows);table('metrics/groups/'+group+'_REVERSE_RING_CONTAINMENT.csv',rows);save('runtime/'+group+'_REVERSE_RING_COMPLETE.json',dict(epoch=time.time()));print('REVERSE_RING021',group,flush=True)
 save('runtime/REVERSE_RING_COMPLETE.json',dict(epoch=time.time()))
if __name__=='__main__':main()
