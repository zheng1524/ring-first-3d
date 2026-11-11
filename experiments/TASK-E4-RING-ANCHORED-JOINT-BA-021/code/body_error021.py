"""Transfer actual native-ray axial residuals to the actual hit body triangles."""
from geometry021 import *
from visualize021 import layer,composite,free_camera,panel,body_layer,plt,finish,matplotlib
def one(group):
 conf=next(g for g in load(R/'config/FOUR_GROUP_INPUTS.json')if g['group']==group);rv=np.load(conf['ring']['path']);bodies={k:dict(np.load(a['path']))for k,a in conf['bodies'].items()};fig,axs=plt.subplots(3,2,figsize=(11,14));bounds=np.r_[rv['V'],bodies['B0']['V'],bodies['B2']['V']];views=[free_camera(bounds,*a)for a in [(25,-65),(0,-90),(0,90)]];bad=[]
 for j,(name,z)in enumerate(bodies.items()):
  F=z['F'];count=np.zeros(len(F),int);total=np.zeros(len(F));by=[]
  for s in conf['sources']:
   e=np.load(R/'evaluation/groups'/group/(s['id']+'_SOURCE_EVIDENCE.npz'));active=e[name+'_active'];fid=e[name+'_body_face_id'][active];assert (fid<len(F)).all();err=abs(e[name+'_depth_mm'][active]-e['HERO_depth_mm'][active]);ct=np.bincount(fid,minlength=len(F));sm=np.bincount(fid,weights=err,minlength=len(F));count+=ct;total+=sm;by.append(ct)
  mean=np.divide(total,count,out=np.full(len(F),np.nan),where=count>0);np.savez_compressed(R/'evaluation/groups'/group/(name+'_BODY_FACE_MM_ERROR.npz'),face_id=np.arange(len(F)),mean_abs_axial_error_mm=mean,observation_count=count,per_source_counts=np.array(by),source_ids=[s['id']for s in conf['sources']],cap_excluded=True);table('metrics/groups/'+group+'_'+name+'_BODY_FACE_MM_ERROR.csv',[dict(group=group,body=name,body_visible_face_id=k,original_frozen_face_id=k,native_hit_observation_N=int(n),mean_abs_axial_error_mm=float(mean[k])if n else None,unknown_no_hit=not bool(n))for k,n in enumerate(count)])
  fc=np.tile([.65,.65,.65],(len(z['F_solid']),1));lookup={tuple(f):i for i,f in enumerate(F)}
  for k,f in enumerate(z['F_solid']):
   if tuple(f)in lookup:
    v=mean[lookup[tuple(f)]]
    if np.isfinite(v):fc[k]=plt.get_cmap('viridis')(min(v/2,1))[:3]
  prepared=composite([layer(z['V'],z['F_solid'],fc,name),layer(rv['V'],rv['F'],'black','CAD')])
  for i,v in enumerate(views):panel(axs[i,j],prepared,v,bounds,name+' actual hit-triangle |dz|\n0..2 mm; gray = cap or no active observation')
  for k in np.argsort(np.nan_to_num(mean,nan=-1))[::-1][:15]:bad.append(dict(group=group,body=name,body_face_id=int(k),XYZ_mm=z['V'][F[k]].mean(0),native_hit_observation_N=int(count[k]),mean_abs_axial_error_mm=float(mean[k])if count[k]else None))
 fig.colorbar(plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0,2),cmap='viridis'),ax=axs.ravel().tolist(),shrink=.55,label='Native HERO axial residual transferred to body face (mm)');fig.suptitle(group+' actual B0/B2 body error distribution | no GT / ICP / new optimization\nAll source observations included; repeated source rays are not independent. Unhit triangles are UNKNOWN, not zero error.');fig.subplots_adjust(top=.91,hspace=.25,wspace=.12,right=.82);finish(fig,'groups/'+group+'/Body_Surface_Native_Depth_Error_mm.png',115);save('metrics/groups/'+group+'_BODY_ERROR_LOCATIONS.json',bad);save('runtime/'+group+'_BODY_ERROR_MAP_COMPLETE.json',dict(epoch=time.time()));print('BODY_ERROR_MAP021',group,flush=True)
def main():
 for g in ['G03','G05','G06','G01']:
  while not(R/'runtime'/(g+'_QUANTITATIVE_COMPLETE.json')).exists():time.sleep(5)
  if not(R/'runtime'/(g+'_BODY_ERROR_MAP_COMPLETE.json')).exists():one(g)
 save('runtime/BODY_ERROR_MAPS_COMPLETE.json',dict(epoch=time.time()))
if __name__=='__main__':main()
