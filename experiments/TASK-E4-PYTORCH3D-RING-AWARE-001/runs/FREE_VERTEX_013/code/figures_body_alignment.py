"""Pure body views; Ring/background absent. Shared camera, extent and scale per case."""
from visual013 import *
import matplotlib.colors as mcolors
ANGLES=[(89.999,0),(-89.999,0),(0,0),(0,90),(0,180),(0,270)]
def camera(bounds,angle):
 center=(bounds.min(0)+bounds.max(0))/2;rad=max(1e-6,np.linalg.norm(bounds-center,axis=1).max());el,az=np.radians(angle);pos=center+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);fw=(center-pos)/np.linalg.norm(center-pos);right=np.cross(fw,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(fw,right);T=np.eye(4);T[:3,:3]=np.c_[right,down,fw];T[:3,3]=pos;return np.array([[440.,0,179.5],[0,440.,179.5],[0,0,1.]]),T,440/np.linalg.norm(pos-center)
def render(V,F,bounds,angle,color,face_colors=None):
 K,T,scale=camera(bounds,angle);h=w=360;y,x=np.mgrid[:h,:w];d=np.c_[x.ravel(),y.ravel(),np.ones(h*w)]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(T[:3,3],d.shape),d@T[:3,:3].T].astype(np.float32);rt=scene(V,F);hits=rt.cast_rays(o3d.core.Tensor(rays));ids=hits['primitive_ids'].numpy().astype(int);hit=ids<len(F);rgb=np.ones((h*w,3))*.97;norm=trimesh.Trimesh(V,F,process=False).face_normals;light=(T[:3,3]-bounds.mean(0));light/=np.linalg.norm(light);shade=.5+.5*np.maximum(0,norm[ids[hit]]@light);colors=np.broadcast_to(mcolors.to_rgb(color),(hit.sum(),3))if face_colors is None else face_colors[ids[hit]];rgb[hit]=colors*shade[:,None];return rgb.reshape(h,w,3),hit.reshape(h,w),scale
def show(ax,V,F,bound,angle,title,GT=None,errors=None):
 colors=None
 if errors is not None:colors=plt.get_cmap('magma')(np.clip(errors,0,2)/2)[:,:3]
 im,mask,scale=render(V,F,bound,angle,'#9255ad',colors)
 if GT is not None:
  gi,gm,_=render(GT['V'],GT['F'],bound,angle,'#8d9299');background=np.ones_like(im)*.97;background[gm]=.45*gi[gm]+.55*.97;both=mask&gm;only=mask&~gm;background[only]=im[only];background[both]=.65*im[both]+.35*background[both];im=background
 ax.imshow(im);ax.plot([15,15+2*scale],[340,340],c='black',lw=1);ax.text(15,330,'2 mm (viewer-center)',fontsize=5);ax.axis('off');ax.set_title(title,fontsize=7)
def main():
 rows=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json');cases=load(R/'config/CASE_LOCK.json');fig,axs=plt.subplots(len(cases),4,figsize=(17,len(cases)*3))
 for i,c in enumerate(cases):
  n=c['name'];gp=R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz'
  if not gp.exists():
   for ax in axs[i]:ax.axis('off');ax.text(.5,.5,n+' GT NOT_EVALUABLE',ha='center')
   continue
  g=dict(np.load(gp));z={t:dict(np.load(R/'local_results/aligned'/n/(t+'.npz')))for t in ['FINAL011','FINAL012','FINAL013']};b=np.r_[g['V'],*[x['V']for x in z.values()]];show(axs[i,0],g['V'],g['F'],b,(20,-65),n+' original Blender body')
  for j,t in enumerate(z,1):
   m=z[t];r=next(x for x in rows if x['case']==n and x['label']==t);show(axs[i,j],m['V'],m['F'],b,(20,-65),t+' Chamfer %.3f mm'%r['Chamfer_MAE_mm'],g)
  # Complete individual before/after, six shared directions, 3-stage fair comparison.
  f,aa=plt.subplots(5,6,figsize=(23,18));before=dict(np.load(R/'local_results/metric'/n/'FINAL013.npz'));bb=np.r_[b,before['V']]
  for k,ang in enumerate(ANGLES):
   show(aa[0,k],g['V'],g['F'],bb,ang,n+' GT only')
   show(aa[1,k],before['V'],before['F'],bb,ang,'013 before rigid alignment',g)
   for rr,t in enumerate(z,2):
    m=z[t];show(aa[rr,k],m['V'],m['F'],bb,ang,t+' after bestSE3',g)
  f.suptitle(n+' pure bodies, six fixed directions | GT transparentgray; prediction purple\n'+EVAL+' | common extent includes before alignment; noRing/background. No smoothing.');finish(f,'full/'+n+'_Body_Six_Views.png')
  m=z['FINAL013'];err=distance(scene(g['V'],g['F']),m['V'][m['F']].mean(1));f,aa=plt.subplots(1,3,figsize=(13,5))
  for ax,ang in zip(aa,[(0,-65),(25,-65),(70,-90)]):show(ax,m['V'],m['F'],b,ang,'013 face-centroid distance 0–2 mm',errors=err)
  f.suptitle(n+' true mesh surface error; dark0 / yellow>=2mm, saturated values retained in metrics');finish(f,'full/'+n+'_Surface_Error.png')
 fig.suptitle('Eleven pure-body comparisons | same new best rigid evaluator for 011 / 012 / 013\n'+EVAL+'\nThese are shape errors after pose removal, not end-to-end localization accuracy.');finish(fig,'Fig4_Best_Rigid_Body_Comparison.png')
EVAL='After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment'
if __name__=='__main__':main()
