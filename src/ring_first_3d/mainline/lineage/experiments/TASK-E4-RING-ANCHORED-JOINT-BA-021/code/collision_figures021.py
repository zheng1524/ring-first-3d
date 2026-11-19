"""Show inherited CAD contact and actual local triangle deformation, without editing geometry."""
from geometry021 import *
from visualize021 import layer,composite,free_camera,panel,plt,finish

def one(group):
 conf=next(g for g in load(R/'config/FOUR_GROUP_INPUTS.json')if g['group']==group);rv=np.load(conf['ring']['path']);bodies={k:dict(np.load(a['path']))for k,a in conf['bodies'].items()};fig,axs=plt.subplots(2,3,figsize=(16,10));bounds=np.r_[rv['V'],bodies['B0']['V'],bodies['B2']['V']];rows=[]
 for i,(name,z)in enumerate(bodies.items()):
  q=np.load(R/'evaluation/groups'/group/(name+'_QUALITY.npz'));bad=q['Ring_face_min_mm']<-.001;F=z['F_solid'];fc=np.tile([.35,.65,.8],(len(F),1));fc[bad]=[.95,.1,.12];cad=layer(rv['V'],rv['F'],'black','CAD');ss=composite([layer(z['V'],F,fc,name),cad]);panel(axs[i,0],ss,free_camera(bounds,25,-65),bounds,name+' inherited CAD conflict faces red\nmin %.6fmm; N=%d beyond -0.001mm'%(q['Ring_face_min_mm'].min(),bad.sum()))
  if bad.any():local=z['V'][F[bad]].reshape(-1,3)
  else:local=z['V'][F[[int(np.argmin(q['Ring_face_min_mm']))]]].reshape(-1,3)
  lo,hi=local.min(0)-.3,local.max(0)+.3;zoom=np.array([lo,hi]);panel(axs[i,1],ss,free_camera(zoom,25,-65),zoom,'Same actual full geometry; local contact zoom\nNo clipping / face deletion / collision repair')
  stretch=q['edge_stretch'];area=q['area_ratio'];cc=plt.get_cmap('magma')(np.clip((stretch-1)/.8,0,1))[:,:3];panel(axs[i,2],composite([layer(z['V'],F,cc,name),cad]),free_camera(bounds,0,-90),bounds,'Actual edge stretch 1..1.8 display\nmax %.3f; minimum area ratio %.3f'%(stretch.max(),area.min()))
  for k in np.flatnonzero(bad):rows.append(dict(group=group,body=name,solid_body_face_id=int(k),vertices=F[k],XYZ_mm=z['V'][F[k]].mean(0),sampled_signed_CAD_min_mm=float(q['Ring_face_min_mm'][k]),max_edge_stretch=float(stretch[k]),area_ratio=float(area[k]),inherited_from018=True))
 fig.suptitle(group+' frozen018 B0/B2 CAD-contact and mesh-quality audit: real triangles in mm\nRed is sampled body-to-CAD intrusion proxy, not a repaired surface. FCL surface test and reverse CAD containment are separate in numeric reports.\nDisplay zoom may show sub-pixel contact in whole views; maximum intrusion and actual solid-face IDs are preserved.');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'groups/'+group+'/Ring_Contact_And_Local_Mesh_Quality.png',125);save('metrics/groups/'+group+'_BODY_RING_CONFLICT_FACES.json',rows);table('metrics/groups/'+group+'_BODY_RING_CONFLICT_FACES.csv',rows);save('runtime/'+group+'_COLLISION_FIGURE_COMPLETE.json',dict(epoch=time.time()));print('COLLISION_FIG021',group,flush=True)
def main():
 for g in ['G03','G05','G06','G01']:
  while not(R/'runtime'/(g+'_QUANTITATIVE_COMPLETE.json')).exists():time.sleep(5)
  one(g)
 save('runtime/COLLISION_FIGURES_COMPLETE.json',dict(epoch=time.time()))
if __name__=='__main__':main()
