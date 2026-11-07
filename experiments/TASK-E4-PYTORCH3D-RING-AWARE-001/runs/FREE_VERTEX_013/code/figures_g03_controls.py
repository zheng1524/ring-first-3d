from visual013 import *

def main():
 n='G03';tags=['A0','A1','A2','A3','O1','O2','O3','O4','O3N'];cid=review_view(n);a=np.load(R/'inputs'/n/(cid+'.npz'));rr=np.load(R/'inputs'/n/'RING.npz');cad=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640);init=np.load(R/'inputs'/n/'INITIAL.npz');b=np.r_[init['V'],rr['V']];fig,axs=plt.subplots(6,3,figsize=(18,25))
 for k,t in enumerate(tags):
  folder=R/'arms'/('PILOT_'+t);z=np.load(folder/'local_results'/n/'FINAL.npz');run=load(folder/'metrics'/(n+'_RUN.json'));i,j=divmod(k,3);ax=axs[2*i,j];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');dep=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);edge(ax,np.isfinite(dep)&(dep<cad),'purple');ax.axis('off');ax.set_title(t+' %d/%d accepted'%(run['accepted'],run['attempts'])+'\nmax displacement %.6g mm'%run['maximum_displacement_mm'],fontsize=9);im,sc=actual_mesh_image(z['V'],z['F_solid'],rr['V'],rr['F'],b,0,-65,'#a652af');ax=axs[2*i+1,j];ax.imshow(im);ax.axis('off');ax.plot([15,15+2*sc],[375,375],c='black');ax.text(15,365,'2 mm',fontsize=6)
 fig.suptitle('G03 isolated loss / optimizer / range controls | same011FINAL start and fixed120/60/40 budget\nGreen original full Mask / purple current first-visible body contour. All nine meshes use identical world-mm viewer; no amplified geometry.\nA0–A3: O0 optimizer; O1–O4/O3N: A0 loss. O3N is separately preregistered dimension repair. Do not confuse tiny accepted updates with stalk recovery.');finish(fig,'full/G03_Eight_Isolated_Controls.png')
if __name__=='__main__':main()
