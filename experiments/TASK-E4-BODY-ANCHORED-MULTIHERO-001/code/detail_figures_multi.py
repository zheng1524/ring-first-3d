from visualize_multi import *

def main():
 fig,axs=plt.subplots(4,6,figsize=(20,13))
 for gi,g in enumerate(CFG['groups']):
  initial=np.load(R/'inputs'/g/'INITIAL.npz');rv=np.load(R/'inputs'/g/'RING.npz');bounds=np.r_[initial['V'],rv['V']];history=load(R/'metrics'/(g+'_B3_ROUNDS.json'));files=[R/'runs'/g/'B3'/'INITIAL.npz']+sorted((R/'runs'/g/'B3').glob('ROUND_*.npz'))
  for j in range(6):
   if j>=len(files):axs[gi,j].text(.5,.5,'Stopped: exact outer rollback\nNo later state invented',ha='center',va='center');axs[gi,j].axis('off');continue
   p=files[j];a=np.load(p);title=g+' '+p.stem
   if j:title+='\n'+('ACCEPTED'if history[j-1]['accepted']else'ROLLBACK')
   panel(axs[gi,j],[(a['V'],a['F'],[.45,.43,.75])],rv,bounds,title)
  # Three view actual Body-only comparison at consistent P0 bounds; full HERO atlas remains separate.
  f,ax=plt.subplots(3,2,figsize=(8,11));final=np.load(R/'runs'/g/'B3'/'FINAL.npz')
  for ai,ang in enumerate(ANGLES):
   for jj,(name,a)in enumerate([('B0',initial),('B3',final)]):panel(ax[ai,jj],[(a['V'],a['F'],[.45,.43,.75])],rv,bounds,g+' '+name+' Body / angle '+str(ang),ang)
  finish(f,g+'_BODY_ONLY_FIXED_VIEWS.png')
  # Same true source view, exact original intrinsics; masks are not redefined.
  meta=load(R/'inputs'/g/'ALL_VIEW_META.json');chosen=[next(v for v in meta['views']if v['role']=='FIT'),next(v for v in meta['views']if v['role']!='FIT')];f,ax=plt.subplots(2,4,figsize=(15,7));scores=load(R/'metrics/PER_VIEW.json')
  for ii,v in enumerate(chosen):
   p=R/'inputs'/g/(v['id']+'.npz')
   if not p.exists():p=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018/holdout'/g/(v['id']+'.npz')
   a=np.load(p);h,w=a['labels'].shape;cad=cast(scene(rv['V'],rv['F']),a['K'],a['T'],h,w)
   for jj,arm in enumerate(CFG['arms']):
    b=np.load(R/'runs'/g/arm/'FINAL.npz');z=cast(scene(b['V'],b['F']),a['K'],a['T'],h,w);pred=np.isfinite(z)&(z<cad);ax[ii,jj].imshow(a['RGB'])
    for mask,col in [(a['labels']==1,'lime'),(a['labels']==2,'cyan'),(pred,'magenta')]:
     cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
     for cc in cs:ax[ii,jj].plot(cc[:,0,0],cc[:,0,1],c=col,lw=.75)
    sc=next(r for r in scores if r['group']==g and r['arm']==arm and r['view']==v['id']);ax[ii,jj].set_title(v['id']+' '+v['role']+'\n'+arm+' IoU %.4f'%sc['IoU'],fontsize=8);ax[ii,jj].axis('off')
  f.suptitle('Original RGB / Polyp green / Ring cyan / actual Body magenta; cameras and pixel mapping fixed.');finish(f,g+'_REAL_PROJECTIONS.png')
  ss=sources(g);f,ax=plt.subplots(figsize=(11,max(4,len(ss)*.22)));ax.axis('off')
  for i,s in enumerate(ss):ax.text(.03,1-i/(len(ss)+1),s.id,color=color(i),fontsize=8,transform=ax.transAxes)
  ax.set_title(g+' source color legend | separate native predictions, not independent anatomical surfaces');finish(f,g+'_SOURCE_LEGEND.png')
 finish(fig,'Detail_Body_Round_Evolution.png')
if __name__=='__main__':main()
