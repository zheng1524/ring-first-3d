"""Independent005 triangulation and traceable symmetric correspondences; no body/HERO."""
from common import *
import features019 as f
import collections

def make(scope,refs,targets,reverse_label,lmname):
 lm=dict(np.load(R/'landmarks'/(lmname+'.npz')));f.cross(refs,targets,lm,reverse_label)
 oldname='CROSS_004'if scope=='CROSS'else'NEGATIVE_004'
 A=load(R/'landmarks'/(oldname+'_OBSERVATIONS.json'));B=load(R/'landmarks'/(lmname+'_OBSERVATIONS.json'));amap={(o['view'],o['feature_id']):i for i,t in enumerate(A)for o in t['observations']};bmap={(o['view'],o['feature_id']):i for i,t in enumerate(B)for o in t['observations']};votes=collections.defaultdict(list)
 for m in load(R/'features'/(scope+'_EPI.json')):
  raw=np.load(R/'matches'/(m['a']+'__'+m['b']+'.npz'))
  for k in np.flatnonzero(raw['RGB_RANSAC']):
   ia,ib=raw['index_pairs'][k];a=amap.get((m['a'],int(ia)));b=bmap.get((m['b'],int(ib)))
   if a is not None and b is not None:votes[(a,b)].append(dict(a=m['a'],b=m['b'],a_feature=int(ia),b_feature=int(ib),match_index=int(k),p=raw['p'][k],q=raw['q'][k]))
 ranked=sorted(votes,key=lambda k:(-len(votes[k]),k));selected=[];useda=set();usedb=set();rejected=[]
 for a,b in ranked:
  e=votes[a,b];reason=[]
  if len(e)<2 or len({x['a']for x in e})<2 or len({x['b']for x in e})<2:reason.append('INSUFFICIENT_DISTINCT_VIEW_SUPPORT')
  if a in useda or b in usedb:reason.append('ONE_TO_ONE_TRACK_AMBIGUITY')
  x=dict(landmark004=a,landmark005=b,evidence=e,actual_RGB_descriptor_RANSAC=True)
  if reason:rejected.append(x|dict(reason=reason))
  else:selected.append(x);useda.add(a);usedb.add(b)
 XA=np.load(R/'landmarks'/(oldname+'.npz'))['X'];XB=lm['X']
 save('features/'+scope+'_NAMED_3D_TRACK_PAIRS.json',dict(matches=[x|dict(X004=XA[x['landmark004']],X005=XB[x['landmark005']])for x in selected],rejected=rejected,matching='actual SIFT descriptor correspondences plus RGB RANSAC, >=2 views on EACH side, greedy one-to-one by votes; never spatial nearest points'))
 # Retain 2D-only epipolar evidence; avoid counting reliable 3D-3D endpoints again.
 epi=[]
 for m in load(R/'features'/(scope+'_EPI.json')):
  raw=np.load(R/'matches'/(m['a']+'__'+m['b']+'.npz'));ii=np.asarray(m['match_indices']);ids=raw['index_pairs'][ii];keep=np.array([not((m['a'],int(ia))in amap and(m['b'],int(ib))in bmap)for ia,ib in ids]);
  if keep.any():epi.append(m|dict(p=np.asarray(m['p'])[keep],q=np.asarray(m['q'])[keep],match_indices=ii[keep]))
 save('features/'+scope+'_EPI_2D_ONLY.json',epi)
 print('SYMMETRIC_TRACK_PAIRS',scope,len(selected),'reverse',sum(x['success']for x in load(R/'features'/(reverse_label+'_PNP.json'))),flush=True)

def main():
 f.VIEWS={v['id']:v for v in load(R/'config/VIEWS.json')};fit4=[v['id']for v in f.VIEWS.values()if v['video']=='004'and v['role']=='FIT'];fit5=[v['id']for v in f.VIEWS.values()if v['video']=='005'and v['role']=='FIT']
 f.landmarks(fit5,'INDEPENDENT_005');make('CROSS',fit5,fit4,'REVERSE','INDEPENDENT_005');n=load(R/'config/NEGATIVE_SPLIT.json');f.landmarks(n['target_fit'],'NEGATIVE_LATE_004');make('NEGATIVE',n['target_fit'],n['reference_fit'],'NEGATIVE_REVERSE','NEGATIVE_LATE_004')
 save('provenance/SYMMETRIC_FEATURES_FROZEN.json',dict(epoch=time.time(),HOLDOUT=False,body=False,HERO=False,feature_ancestor_019='004 and forward observations originally obtained without body/HERO',files=[asset(p)for folder in ['features','landmarks']for p in(R/folder).glob('*.json')],independent005=asset(R/'landmarks/INDEPENDENT_005.npz'),source=asset(Path(__file__))))
if __name__=='__main__':main()
