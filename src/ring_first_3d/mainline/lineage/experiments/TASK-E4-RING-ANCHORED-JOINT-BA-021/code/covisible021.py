"""Explicit first-layer co-visibility subset; deeper/self-occluded points are NOT errors."""
from geometry021 import *
def one(group):
 H=load(R/'results/B3.json')['T']if group=='G01'else np.eye(4);conf,src=group_data(group,H);rv=np.load(conf['ring']['path']);cad=scene(rv['V'],rv['F']);rows=[];allerr=[];visible=[];compatible=[];total=0;known=0;cov=0;source_unknown=0
 for a in src:
  rz=cad.cast_rays(rays(a['obs']['uv'],a['obs']['K'],a['C']))['t_hit'].numpy();source_valid=a['obs']['z']<rz-.05
  for b in src:
   if a['id']==b['id']:continue
   q=visibility_query(a['X'],b['C'],b['obs']['K'],b['grid'],cad);k=q['known']&source_valid;support=q['supported']&source_valid;front=q['front']&source_valid;behind=q['behind']&source_valid;occ=q['cad_occluded']&source_valid;co=support|front;N=len(k);total+=N;known+=int(k.sum());cov+=int(co.sum());source_unknown+=int((~source_valid).sum());allerr.extend(q['dz'][k]);visible.extend(q['dz'][co]);compatible.extend(q['dz'][support]);rows.append(dict(group=group,source=a['id'],target=b['id'],fixed_source_N=N,strict_comparable_N=int(k.sum()),co_visible_first_layer_candidate_N=int(co.sum()),compatible_within05mm_N=int(support.sum()),front_disagreement_proxy_N=int(front.sum()),deeper_self_occlusion_possible_N=int(behind.sum()),CAD_occluded_N=int(occ.sum()),UNKNOWN_N=int((~k&~occ).sum()),own_source_CAD_order_UNKNOWN_N=int((~source_valid).sum()),strict_comparable_depth_mm=stats(q['dz'][k]),co_visible_candidate_depth_mm=stats(q['dz'][co]),compatible_conditioned_depth_mm=stats(q['dz'][support])))
 summary=dict(group=group,source_count=len(src),ordered_source_target_pairs=len(rows),fixed_source_target_N=total,strict_comparable_N=known,co_visible_first_layer_candidate_N=cov,co_visible_candidate_fraction_fixed=cov/total,own_source_CAD_order_UNKNOWN_N=source_unknown,strict_comparable_depth_mm=stats(allerr),co_visible_candidate_depth_mm=stats(visible),compatible_conditioned_depth_mm=stats(compatible),definition='Source TRUSTED sample before its own CAD, target native first visible depth valid and beforeCAD. Co-visible candidate = supported ±0.5mm OR in front of target; deeper source is excluded as possible normal self-occlusion. This is an uncalibrated visibility proxy, not GT.',no_depth_or_geometry_changed=True)
 save('metrics/groups/'+group+'_CO_VISIBLE_FIRST_LAYER.json',summary);save('metrics/groups/'+group+'_CO_VISIBLE_PER_PAIR.json',rows);table('metrics/groups/'+group+'_CO_VISIBLE_PER_PAIR.csv',rows);save('runtime/'+group+'_CO_VISIBLE_COMPLETE.json',dict(epoch=time.time()));print('CO_VISIBLE021',group,summary['co_visible_candidate_depth_mm'],flush=True)
def main():
 for g in ['G03','G05','G06','G01']:
  while not(R/'runtime'/(g+'_QUANTITATIVE_COMPLETE.json')).exists():time.sleep(5)
  one(g)
 save('runtime/CO_VISIBLE_COMPLETE.json',dict(epoch=time.time()))
if __name__=='__main__':main()
