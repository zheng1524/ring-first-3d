from visual_common import *

def overview():
 cases=load(R/'config/CASE_LOCK.json');fig=plt.figure(figsize=(28,22));gs=fig.add_gridspec(3,3,hspace=.12,wspace=.04)
 for i,kind in enumerate(['Ip','Is','IIa']):
  for j,c in enumerate([x for x in cases if x['morphology']==kind]):
   n=c['name'];views=c['views'];fit=next(x['id']for x in views if x['role']=='FIT');held=next(x['id']for x in views if x['role']!='FIT');sub=gs[i,j].subgridspec(3,3,wspace=.02,hspace=.1)
   for k,tag in enumerate(['C011','FINAL011','FINAL012']):
    ax=fig.add_subplot(sub[0,k]);rgb(ax,n,fit,[tag]);ax.set_title(n+' '+kind+' '+tag+' FIT',fontsize=7)
    ax=fig.add_subplot(sub[1,k]);meshpanel(ax,n,tag,(0,-65),title=tag+' side')
    ax=fig.add_subplot(sub[2,k]);meshpanel(ax,n,tag,(30,-65),title=tag+' oblique')
 fig.suptitle('Nine same-input free-vertex routes | 011 C -> 011 FINAL -> 012 FREE FINAL\nBlue / gold / purple; gray inferred base, black fixed CAD. Identical mm viewer in each case, no mesh postprocess.\nFree vertex displacement, not new camera or neural-network training. Numerical output is not anatomical accuracy.',fontsize=12);finish(fig,'Fig1_Nine_Free_Vertex_Overview.png')

def ip():
 fig=plt.figure(figsize=(22,19));gs=fig.add_gridspec(3,1,hspace=.18);crops=[]
 for i,n in enumerate(['G01','G02','G03']):
  c=getcase(n);cid=next(v['id']for v in c['views']if v['role']=='FIT');a=np.load(R/'inputs'/n/(cid+'.npz'));rr=np.load(R/'inputs'/n/'RING.npz');z=model(n,'FINAL011');pred=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);cz=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640);missing=(a['labels']==1)&~(np.isfinite(pred)&(pred<cz));N,labels,stats0,cent=cv2.connectedComponentsWithStats(missing.astype(np.uint8),8)
  if N>1:idx=1+np.argmax(stats0[1:,4]);x,y,w,h,_=stats0[idx];crop=[max(0,x-20),max(0,y-20),min(640,x+w+20),min(360,y+h+20)]
  else:
   yy,xx=np.nonzero(a['labels']==1);crop=[max(0,int(xx.min())-20),max(0,int(yy.min())-20),min(640,int(xx.max())+20),min(360,int(yy.max())+20)]
  crops.append(dict(case=n,view=cid,crop=crop,selection='largest missing connected silhouette of frozen011FINAL; never012 result, not a stem segmentation'));sub=gs[i].subgridspec(2,5,wspace=.03,hspace=.12)
  ax=fig.add_subplot(sub[0,0]);rgb(ax,n,cid,['C011','FINAL011','FINAL012']);ax.set_title(n+' full raw RGB / Mask / three contours',fontsize=8)
  ax=fig.add_subplot(sub[1,0]);rgb(ax,n,cid,['C011','FINAL011','FINAL012'],crop=crop);ax.set_title('Initial missing contour region: zoom\nNot an anatomical head/stem segmentation',fontsize=8)
  for k,tag in enumerate(['C011','FINAL011','FINAL012']):
   ax=fig.add_subplot(sub[0,k+1]);meshpanel(ax,n,tag,(65,-90),title=tag+' front')
   ax=fig.add_subplot(sub[1,k+1]);meshpanel(ax,n,tag,(0,-65),title=tag+' side')
  ax=fig.add_subplot(sub[0,4]);meshpanel(ax,n,'FINAL012',(30,-65),title='012 oblique: head / possible stalk')
  ax=fig.add_subplot(sub[1,4]);run=load(R/'metrics'/(n+'_RUN.json'));ax.axis('off');ax.text(0,.95,n+'\n'+str(run['accepted'])+' accepted / '+str(run['attempts'])+' attempts\n'+run['status']+'\nMax actual displacement %.4f mm'%run['maximum_displacement_mm']+'\n\nStalk existence/direction requires\nreal-view and 3D inspection.\nNo GT or old result generated this mesh.',va='top',fontsize=9)
 fig.suptitle('Ip stalk review | same world-mm coordinates, black CAD, complete masks including stalk\nNo head/stalk model or hard segmentation was used. Enlarged crop is fixed by the 011 residual, independent of 012 outcome.',fontsize=12);finish(fig,'Fig2_Three_Ip_Stalk_Review.png');save('metrics/IP_VISUALIZATION_CROPS.json',crops)

def process():
 fig=plt.figure(figsize=(25,14));gs=fig.add_gridspec(3,1,hspace=.15)
 for row,c in enumerate(['G01','G07','G06']):
  sub=gs[row].subgridspec(1,6,wspace=.03)
  for j,k in enumerate([0,25,50,100,200]):
   ax=fig.add_subplot(sub[0,j]);tag='ACCEPTED_%04d'%k;path=R/'local_results'/c/(tag+'.npz')
   if path.exists():meshpanel(ax,c,tag,title=c+' accepted '+str(k))
   else:ax.axis('off');ax.text(.5,.5,c+' accepted '+str(k)+'\nNOT REACHED',ha='center',transform=ax.transAxes)
  ax=fig.add_subplot(sub[0,5]);run=load(R/'metrics'/(c+'_RUN.json'));meshpanel(ax,c,'FINAL012',title=c+' FINAL accepted '+str(run['accepted']))
 fig.suptitle('Actual accepted-update checkpoints | fixed representatives G01 / G07 / G06\nMissing milestones are explicitly not reached; FINAL is never a selected best intermediate.\nSame mm viewer per case; no smoothing, no generated intermediate shapes.',fontsize=12);finish(fig,'Fig3_Free_Vertex_Update_Process.png')

def details():
 for c in load(R/'config/PROTOCOL.json')['cases']:
  meta=getcase(c);fit=next(v['id']for v in meta['views']if v['role']=='FIT');held=next(v['id']for v in meta['views']if v['role']!='FIT');fig,axs=plt.subplots(4,3,figsize=(15,17))
  for j,tag in enumerate(['C011','FINAL011','FINAL012']):
   rgb(axs[0,j],c,fit,[tag]);axs[0,j].set_title(tag+' FIT',fontsize=9);rgb(axs[1,j],c,held,[tag]);axs[1,j].set_title(tag+' HOLDOUT',fontsize=9);meshpanel(axs[2,j],c,tag,(0,-65));meshpanel(axs[3,j],c,tag,(30,-65))
  fig.suptitle(c+' actual geometry and original-camera projection | same mm scale, no registration in these views',fontsize=12);fig.tight_layout(rect=[0,0,1,.96]);finish(fig,'full/'+c+'_Three_Stage_Detail.png')

if __name__=='__main__':overview();ip();process();details();print('NATIVE_FIGURES_COMPLETE')
