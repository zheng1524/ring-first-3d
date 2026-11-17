"""Native masks/availability/missing first hits, shown without inventing depths."""
from geometry021 import *
from visual_base import plt,finish,edge,matplotlib
def one(group):
 H=np.asarray(load(R/'results/B3.json')['T'])if group=='G01'else np.eye(4);conf,src=group_data(group,H);first=next(a for a in src if a['role']=='FIT');u=first['C'][:3,3]/np.linalg.norm(first['C'][:3,3]);second=max(src,key=lambda a:np.arccos(np.clip(u@a['C'][:3,3]/np.linalg.norm(a['C'][:3,3]),-1,1)));fig,axs=plt.subplots(2,4,figsize=(17,8))
 for i,a in enumerate([first,second]):
  d=np.load(a['cache']);h,w=map(int,a['obs']['native_shape']);y,x=np.mgrid[:h,:w];p=np.c_[x.ravel(),y.ravel(),np.ones(h*w)]@np.linalg.inv(a['obs']['K']).T@d['K'].T;p=p[:,:2]/p[:,2:];rgb=cv2.remap(d['RGB'],p[:,0].reshape(h,w).astype(np.float32),p[:,1].reshape(h,w).astype(np.float32),cv2.INTER_LINEAR);lab=mapped_labels(d['labels'],d['K'],a['obs']['K'],(h,w));uv=a['obs']['uv'];trust=np.zeros((h,w),bool);trust[uv[:,1],uv[:,0]]=True;e=np.load(R/'evaluation/groups'/group/(a['id']+'_SOURCE_EVIDENCE.npz'));active=e['B2_active'];heat=np.full((h,w),np.nan);heat[uv[active,1],uv[active,0]]=e['B2_depth_mm'][active]-e['HERO_depth_mm'][active];miss=np.zeros((h,w),bool);valid=e['HERO_own_CAD_order_valid']if'HERO_own_CAD_order_valid'in e else np.ones(len(active),bool);miss[uv[~active&valid,1],uv[~active&valid,0]]=True;unknown=np.zeros((h,w),bool);unknown[uv[~valid,1],uv[~valid,0]]=True;C=np.ones((h,w,3))*.95;C[lab==1]=[.6,.6,.6];C[trust]=[.2,.75,.3];C[lab==2]=[.12,.35,.8];trans=np.ones((h,w,3))*.95
  for key,col in [('common',[.2,.75,.3]),('gained',[.1,.75,.9]),('lost',[.9,.12,.12])]:
   selected=e[key];trans[uv[selected,1],uv[selected,0]]=col
  axs[i,0].imshow(rgb);edge(axs[i,0],lab==1,'lime');edge(axs[i,0],lab==2,'cyan');axs[i,0].set_title(a['id']+' '+a['role']+'\noriginal RGB / mapped native Masks')
  axs[i,1].imshow(C);axs[i,1].set_title('Actual TRUSTED availability green\n%d / %d Polyp native pixels; unavailable gray'%(trust.sum(),(lab==1).sum()))
  axs[i,2].imshow(rgb.astype(float)/255*.4);im=axs[i,2].imshow(heat,cmap='coolwarm',vmin=-2,vmax=2);axs[i,2].imshow(np.ma.masked_where(~miss,miss),cmap=matplotlib.colors.ListedColormap(['magenta']),alpha=.9,vmin=0,vmax=1);axs[i,2].imshow(np.ma.masked_where(~unknown,unknown),cmap=matplotlib.colors.ListedColormap(['orange']),alpha=.9,vmin=0,vmax=1);axs[i,2].set_title('B2 actual native first-depth error\n±2mm display; miss magenta; source-CAD unknown orange');fig.colorbar(im,ax=axs[i,2],shrink=.6,label='axial dz mm')
  axs[i,3].imshow(trans);axs[i,3].set_title('Same original Pixel IDs: B0→B2\ncommon green / gained cyan / lost red')
  for ax in axs[i]:ax.axis('off')
 fig.suptitle(group+' native coverage and missing observations: no interpolation of depth / no fake geometry\nOnly RGB is resampled for display via the verified K map. Gray availability may be missing depth, excluded reliability or visibility; not anatomy GT.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'groups/'+group+'/Native_Observation_Coverage_And_Missing_Hits.png',125);save('runtime/'+group+'_COVERAGE_FIGURE_COMPLETE.json',dict(epoch=time.time()));print('COVERAGE_FIGURE021',group,flush=True)
def main():
 for g in ['G03','G05','G06','G01']:
  while not(R/'runtime'/(g+'_QUANTITATIVE_COMPLETE.json')).exists():time.sleep(5)
  one(g)
 save('runtime/COVERAGE_FIGURES_COMPLETE.json',dict(epoch=time.time()))
if __name__=='__main__':main()
