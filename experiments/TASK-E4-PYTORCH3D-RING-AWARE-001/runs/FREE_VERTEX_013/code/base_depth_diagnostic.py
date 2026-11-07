"""Read-only source constraint conflict audit; no weights, samples or cameras changed."""
from common import *
def main():
 rows=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];z=np.load(R/'inputs'/n/'INITIAL.npz');bs=load(R/'inputs'/n/'BASE_SELECTION.json');pl=bs.get('selected_plane');cap=bool(z['inferred_base_faces'].any());plane=None if pl is None else np.asarray(pl)
  for v in c['views']:
   p=R/'depth_observations'/(v['id']+'.npz')
   if not p.exists():continue
   a=np.load(p);ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(a['K']).T;P=(ray*a['z'][:,None])@a['T'][:3,:3].T+a['T'][:3,3];h=P@plane[:3]+plane[3]if plane is not None else np.empty(0);rows.append(dict(case=n,view=v['id'],cap=cap,base_uncertain=bs['uncertain_base'],fixed_reliable_HERO_N=len(P),HERO_signed_base_height_mm=stats(h),HERO_below_base_0p1mm_N=int((h<-.1).sum()),HERO_below_base_0p5mm_N=int((h<-.5).sum()),HERO_below_base_1mm_N=int((h<-1).sum()),input_conflict_proxy_only=True,diagnostic_never_enters_loss_or_sampling=True,GT_read=False))
 save('metrics/BASE_HERO_CONSTRAINT_DIAGNOSTIC.json',rows);table('metrics/BASE_HERO_CONSTRAINT_DIAGNOSTIC.csv',rows)
if __name__=='__main__':main()
