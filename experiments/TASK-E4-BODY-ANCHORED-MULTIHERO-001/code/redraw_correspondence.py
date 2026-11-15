"""Face display uses own native pixel lookup, never 3D NN to another layer."""
from visualize_multi import *
def main():
 fig,axs=plt.subplots(4,3,figsize=(14,15));maps=[]
 for gi,g in enumerate(CFG['groups']):
  ss=sources(g);ring=dict(np.load(R/'inputs'/g/'RING.npz'));initial=dict(np.load(R/'inputs'/g/'INITIAL.npz'));outs={a:dict(np.load(R/'runs'/g/a/'FINAL.npz'))for a in CFG['arms']};bounds=np.concatenate([ring['V'],initial['V']]+[s.m['V'][np.unique(s.m['F'])]for s in ss]);o=outs['B3'];setparams(ss,o);pp=[]
  for s in ss:
   z=np.load(R/'local_results'/(g+'_B3_'+s.id+'_CORRESPONDENCE.npz'));uv,dep=project(s.m['V'][s.m['F']].mean(1),s.C,s.K);dist,idx=cKDTree(s.uv).query(uv);state=z['state'][idx].copy();state[(dist>2)|(dep<=0)]=3;palette=np.array([[.1,.7,.3],[.95,.7,.15],[.85,.15,.15],[.6,.6,.6]]);pp.append((s.vertices(),s.m['F'],palette[state]));maps.append(dict(source=s.id,rule='source-face centroid projected to its own native UV; closest trusted pixel <=2px for display, else UNKNOWN. No 3D nearest layer assignment.',original_face_IDs=len(s.m['original_face_id']),display_unknown_faces=int((state==3).sum())))
  panel(axs[gi,0],pp,ring,bounds,g+' MATCHED green / UNEXPLAINED yellow\nCONFLICT red / UNKNOWN gray')
  disp=np.linalg.norm(o['V']-initial['V'],axis=1);face=colormaps['viridis'](np.minimum(disp[o['F']].mean(1)/.35,1))[:,:3];panel(axs[gi,1],[(o['V'],o['F'],face)],ring,bounds,g+' Body displacement [0,0.35] mm\n'+str(round(disp.max(),6))+' mm max')
  ax=axs[gi,2];y=float(np.median(initial['V'][:,1]))
  for arm,col in [('B0','gray'),('B3','#6b43ba')]:
   m=trimesh.Trimesh(outs[arm]['V'],outs[arm]['F'],process=False);sec=trimesh.intersections.mesh_plane(m,[0,1,0],[0,y,0])
   for line in sec:ax.plot(line[:,0],line[:,2],c=col,lw=.9)
  for i,s in enumerate(ss):
   sec=trimesh.intersections.mesh_plane(trimesh.Trimesh(s.vertices(),s.m['F'],process=False),[0,1,0],[0,y,0])
   for line in sec:ax.plot(line[:,0],line[:,2],c=color(i),lw=.4,alpha=.6)
  ax.set(title=g+' actual section Y=%.3f mm'%y,xlabel='world X mm',ylabel='world Z mm');ax.axis('equal');ax.grid(alpha=.2)
 finish(fig,'Fig3_Correspondences_Displacement_Sections.png');save('assets_index/CORRESPONDENCE_FIGURE_MAPPING.json',maps)
if __name__=='__main__':main()
