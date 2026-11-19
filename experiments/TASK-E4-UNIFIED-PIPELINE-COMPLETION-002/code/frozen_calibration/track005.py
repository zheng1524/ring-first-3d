from v6_common import *
cv2.setNumThreads(2)
def main():
 verify('ring_inputs');freeze('tracking_protocol',[Path(__file__),R/'scripts/v6_common.py',R/'config.json']);L=ledger();sift=cv2.SIFT_create(nfeatures=cfg()['SIFT_features'],contrastThreshold=.01);xy=[];desc=[];cat=[];offset=[0]
 for a in L:
  rgb=image(a);l=labels(a);gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);mask=(cv2.dilate((l==2).astype(np.uint8),np.ones((5,5),np.uint8))==0)&(gray<245);mask[:8]=False;mask[-8:]=False;mask[:,:8]=False;mask[:,-8:]=False;kp,de=sift.detectAndCompute(gray,mask.astype(np.uint8)*255);p=np.array([x.pt for x in kp]);ij=np.rint(p).astype(int);xy.append(p);desc.append(de);cat.append(l[ij[:,1],ij[:,0]]);offset.append(offset[-1]+len(p))
 par=np.arange(offset[-1]);members={i:{int(np.searchsorted(offset,i,side='right')-1)} for i in range(offset[-1])}
 def find(x):
  while par[x]!=x:par[x]=par[par[x]];x=par[x]
  return x
 bf=cv2.BFMatcher();pairs=[];edges=[]
 for i in range(len(L)):
  for skip in cfg()['pair_offsets']:
   j=i+skip
   if j>=len(L):continue
   f=[m for m,n in bf.knnMatch(desc[i],desc[j],k=2) if m.distance<cfg()['SIFT_ratio']*n.distance];b={m.queryIdx:m.trainIdx for m,n in bf.knnMatch(desc[j],desc[i],k=2) if m.distance<cfg()['SIFT_ratio']*n.distance};matches=[m for m in f if b.get(m.trainIdx)==m.queryIdx and cat[i][m.queryIdx]==cat[j][m.trainIdx]];pair=[]
   for m in sorted(matches,key=lambda x:x.distance):
    x=find(offset[i]+m.queryIdx);y=find(offset[j]+m.trainIdx)
    if x!=y:
     if members[x]&members[y]:continue
     par[y]=x;members[x]|=members.pop(y)
    pair.append([m.queryIdx,m.trainIdx])
   pairs.append(dict(i=i,j=j,raw_i=L[i]['raw_frame'],raw_j=L[j]['raw_frame'],appearance_matches=len(matches),union_consistent=len(pair),background=sum(cat[i][x]==0 for x,y in pair),polyp=sum(cat[i][x]==1 for x,y in pair)));edges.append((i,j,np.array(pair,int).reshape(-1,2)));print('TRACK_PAIR',i,j,'matches',len(pair),flush=True)
 roots={}
 for i in range(len(L)):
  for k,p in enumerate(xy[i]):
   rt=find(offset[i]+k)
   if len(members.get(rt,[]))>=3:roots.setdefault(rt,[]).append((i,k))
 tracks=[];cats=[]
 for root,t in sorted(roots.items()):
  z=np.full((len(L),2),np.nan)
  for i,k in t:z[i]=xy[i][k]
  tracks.append(z);cats.append(int(cat[t[0][0]][t[0][1]]))
 T=np.array(tracks);hold=np.arange(len(T))%5==0;keytrack={}
 for id,(_,t) in enumerate(sorted(roots.items())):
  for i,k in t:keytrack[(i,k)]=id
 pairpacks={}
 for n,(i,j,pairs0) in enumerate(edges):
  rows=[]
  for p,q in pairs0:
   t=keytrack.get((i,int(p)))
   if t is not None:rows.append((t,*xy[i][p],*xy[j][q]))
  pairpacks[f'pair{n}']=np.array(rows).reshape(-1,5)
 np.savez_compressed(R/'observations/tracks005.npz',xy=T,category=cats,held=hold,ids=[a['id'] for a in L],frame_raw=[a['raw_frame'] for a in L]);np.savez_compressed(R/'observations/pairs005.npz',ij=np.array([[i,j] for i,j,_ in edges]),**pairpacks);save('metrics/track005.json',dict(frames=len(L),tracks=len(T),held_tracks=int(hold.sum()),background_tracks=int((np.array(cats)==0).sum()),polyp_tracks=int((np.array(cats)==1).sum()),pairs=pairs,per_frame=[dict(id=a['id'],features=len(xy[i]),track_observations=int(np.isfinite(T[:,i,0]).sum()),background=int(((np.array(cats)==0)&np.isfinite(T[:,i,0])).sum()),polyp=int(((np.array(cats)==1)&np.isfinite(T[:,i,0])).sum())) for i,a in enumerate(L)],no_geometric_filter_using_heldout=True));freeze('tracks',[R/'observations/tracks005.npz',R/'observations/pairs005.npz',R/'metrics/track005.json']);print('TRACKS005',len(T),'held',hold.sum(),flush=True)
if __name__=='__main__':main()
