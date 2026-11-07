from visual013 import *
def main():
 n='G03';tags=['PILOT_A0','PILOT_O3','PILOT_O3N','AMENDED_A3_O3N_1D'];titles=['A0 baseline','O3 local raw step','O3N normalized local (A0)','A3 +O3N +1D'];zz=[dict(np.load(R/'arms'/tag/'local_results'/n/'FINAL.npz'))for tag in tags];rr=np.load(R/'inputs'/n/'RING.npz');b=np.r_[*[z['V']for z in zz],rr['V']];cid=review_view(n);a=np.load(R/'inputs'/n/(cid+'.npz'));cad=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640);fig,axs=plt.subplots(3,4,figsize=(19,14))
 for j,(tag,z,title)in enumerate(zip(tags,zz,titles)):
  run=load(R/'arms'/tag/'metrics'/(n+'_RUN.json'));ax=axs[0,j];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');d=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);edge(ax,np.isfinite(d)&(d<cad),'purple');ax.axis('off');ax.set_title(title+'\n%d/%d accepted; max %.6g mm'%(run['accepted'],run['attempts'],run['maximum_displacement_mm']),fontsize=8)
  for i,ang in enumerate([(0,-65),(30,-65)],1):
   im,sc=actual_mesh_image(z['V'],z['F_solid'],rr['V'],rr['F'],b,*ang,'#a652af');ax=axs[i,j];ax.imshow(im);ax.axis('off');ax.plot([20,20+2*sc],[375,375],c='black');ax.text(20,365,'2 mm',fontsize=6)
 fig.suptitle('G03 fixed short pilots, same actual011FINAL start and world-mm viewer\nGreen originalMask; purple real mesh contour; black CAD. NoGT or heldout used.\nLarge displacement is not proof of correct stalk direction; body/heldout/GT evidence remains separate.');finish(fig,'full/G03_Normalization_Combination.png')
if __name__=='__main__':main()
