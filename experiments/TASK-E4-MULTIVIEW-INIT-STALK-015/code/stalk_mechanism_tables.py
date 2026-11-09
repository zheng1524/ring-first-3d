"""Current-resolution and executed vertex motion evidence; no anatomical GT labels."""
from visual_base import *

def project(V,K,T):
 p=(V-T[:3,3])@T[:3,:3];h=p@K.T;return h[:,:2]/h[:,2,None]
def main():
 ips=load(R/'config/PROTOCOL.json')['phase_B']['cases'];selection=load(R/'config/VIEW_SELECTION.json');rows=[];fig,ax=plt.subplots(len(ips),3,figsize=(18,3.5*len(ips)))
 for i,n in enumerate(ips):
  src=R/'arms/Stalk-A';seed=load(src/'inputs'/n/'STALK_SEED.json');p=np.load(src/'inputs'/n/'INITIAL.npz');edges=np.unique(np.sort(np.r_[p['F'][:,[0,1]],p['F'][:,[1,2]],p['F'][:,[2,0]]],axis=1),axis=0);l=np.linalg.norm(p['V'][edges[:,0]]-p['V'][edges[:,1]],axis=1);s=np.asarray(seed.get('s',[]));ss=np.unique(s[s>0]);probe=load(src/'metrics'/(n+'_STALK_PROBE.json'));cid=selection[n]['FIT'][0];obs=np.load(R/'inputs'/n/(cid+'.npz'));ring=np.load(R/'inputs'/n/'RING.npz');cad=cast(scene(ring['V'],ring['F']),obs['K'],obs['T'],*obs['labels'].shape)
  for j,t in enumerate(['Stalk-A','Stalk-B','Stalk-C']):
   root=R/'arms'/t;out=root/'local_results'/n/'FINAL.npz';ax[i,j].imshow(obs['RGB']);edge(ax[i,j],obs['labels']==1,'lime');edge(ax[i,j],obs['labels']==2,'cyan');ax[i,j].axis('off')
   if not out.exists():ax[i,j].set_title(n+' '+t+' NO_SIGNAL',fontsize=8);continue
   z=np.load(out);le=np.linalg.norm(z['V'][edges[:,0]]-z['V'][edges[:,1]],axis=1);row=dict(case=n,arm=t,vertices=len(p['V']),seed_patch_vertex_N=seed.get('patch_vertex_N'),far_associated_N=probe['far_associated_N'],old_band_far_covered_N=probe['old_local_candidates_cover_far_N'],expanded_far_nonzero_N=probe['expanded']['far_with_actual_nonzero_candidate_N'],seed_length_proxy_mm=seed.get('length0_mm'),initial_edge_mm=stats(l),final_edge_mm=stats(le),edge_stretch_ratio_p95=float(np.quantile(le/np.maximum(l,1e-12),.95)),edge_stretch_ratio_max=float((le/np.maximum(l,1e-12)).max()),maximum_axial_material_gap=float(np.diff(ss).max())if len(ss)>1 else None,anatomical_stalk_GT_metric='NOT_EVALUABLE_NO_AUTHORED_REGION_LABEL',seed_is_residual_proxy=True);rows.append(row)
   files=list((root/'local_results'/n).glob('MECHANISM_*.npz'));a=np.load(sorted(files)[-1])if files else None
   if a is None:ax[i,j].set_title(n+' '+t+' no accepted step',fontsize=8);continue
   bv,av=a['before_V'],a['after_V'];delta=av-bv;mag=np.linalg.norm(delta,axis=1);ix=np.flatnonzero(mag>1e-9);ix=ix[np.argsort(mag[ix])[-24:]];uv=project(bv[ix],obs['K'],obs['T']);un=project(av[ix],obs['K'],obs['T']);ax[i,j].quiver(uv[:,0],uv[:,1],un[:,0]-uv[:,0],un[:,1]-uv[:,1],angles='xy',scale_units='xy',scale=1,color='magenta',width=.003)
   for verts,color in [(bv,'gold'),(av,'deepskyblue')]:
    depth=cast(scene(verts,a['F']),obs['K'],obs['T'],*obs['labels'].shape);edge(ax[i,j],np.isfinite(depth)&(depth<cad),color)
   ax[i,j].set_title(n+' '+t+' actual accepted '+str(int(a['accepted']))+' step max %.4fmm'%mag.max(),fontsize=8)
 fig.suptitle('Actual projected vertex displacement | before gold / after blue / arrows magenta, scale1 pixel\n24 largest moving vertices of the last saved accepted step; gradient != momentum optimizer displacement. Original green Mask and cyan Ring.');fig.subplots_adjust(top=.95,hspace=.2);finish(fig,'details/Actual_Accepted_Vertex_Displacements.png',120);save('metrics/STALK_RESOLUTION_AND_COVERAGE.json',rows);table('metrics/STALK_RESOLUTION_AND_COVERAGE.csv',rows);print('STALK_MECHANISM_COMPLETE',flush=True)
if __name__=='__main__':main()
