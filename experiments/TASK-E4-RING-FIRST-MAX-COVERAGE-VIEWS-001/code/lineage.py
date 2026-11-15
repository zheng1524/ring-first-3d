"""Report upstream RGB correlation without deleting unique native geometry.
Post-freeze diagnostic only; weights below never enter cameras, selection or HERO.
"""
from evaluate_geometry import *
def main():
 plans=load(P18/'config/VIEW_PLAN.json');allr=[];pair=[];summ=[]
 for g in GROUPS:
  vv=load(camera_file(g));by={a:v for v in vv for a in [v['id']]+v.get('aliases',[])};conf,old=frozen_sources(g,False);new=new_sources(g);parents={}
  def key(cid):
   v=by.get(cid)
   return g+'|'+v['video']+'|'+str(v.get('raw_frame',v['id']))if v else g+'|UNRESOLVED|'+cid
  for s in old:
   p=next((p for p in plans if p['view_id']==s['id']),None);ps=[key(s['id'])]+[key(c)for c in p['support_views']]if p else[];parents['OLD|'+s['id']]=set(ps);allr.append(dict(group=g,source='OLD|'+s['id'],role=s['role'],RGB_parent_ids=ps,DAG_known=bool(p),HERO_is_independent_measurement=False))
  for s in new:
   ps=[key(s['source']['view_id'])]+[key(c)for c in s['source']['source_ids']];parents['NEW|'+s['id']]=set(ps);allr.append(dict(group=g,source='NEW|'+s['id'],role='FIT',RGB_parent_ids=ps,DAG_known=True,HERO_is_independent_measurement=False))
  per=[r for r in load(N/'metrics/HERO_PER_NATIVE_PAIR.json')if r['group']==g];acc=dict(weighted_den=0.,weighted_known=0.,weighted_support=0.,shared_pairs=0,known_DAG_pairs=0)
  for r in per:
   a=parents.get('NEW|'+r['source'],set());b=parents.get(('NEW|'if r['scope']=='NEW_NEW'else'OLD|')+r['target'],set());known=bool(a and b);shared=len(a&b);w=1/(1+shared)if known else None;pr=dict(group=g,source=r['source'],target=r['target'],scope=r['scope'],shared_upstream_RGB_N=shared if known else None,DAG_known=known,uncalibrated_correlation_weight=w,weight_NOT_used_optimization_or_selection=True);pair.append(pr)
   if r['scope']=='NEW_OLD_FIT'and known:
    acc['weighted_den']+=w*r['fixed_native_pixel_N'];acc['weighted_known']+=w*r['known_N'];acc['weighted_support']+=w*r['same_layer_N'];acc['shared_pairs']+=int(shared>0);acc['known_DAG_pairs']+=1
  acc.update(group=g,uncalibrated_weight_formula='1/(1+shared_RGB_parents)',weighted_support_fraction_fixed=acc['weighted_support']/max(1,acc['weighted_den']),not_independent_statistical_replicates=True,source_voxel_area_dedup_separate_from_upstream_correlation=True);summ.append(acc)
 table('metrics/HERO_RGB_SOURCE_DAG.csv',allr);save('metrics/HERO_RGB_SOURCE_DAG.json',allr);table('metrics/HERO_PAIR_UPSTREAM_CORRELATION.csv',pair);save('metrics/HERO_CORRELATION_SENSITIVITY.json',summ);print('LINEAGE_DONE',len(allr),'native sources',len(pair),'actual pairs',flush=True)
if __name__=='__main__':main()
