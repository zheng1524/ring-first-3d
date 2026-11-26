"""Render full triangle surfaces; no point-splat proxy or per-method alignment."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np,cv2
from common import *
from evaluate import mesh_for,safe_project
from ring_first_3d.sim.geometry import transform
from ring_first_3d.synthetic.raster import ray_map
from ring_first_3d.multisurface.geometry import mesh_sections,plane_coordinates

OUT=T/'evidence'
def merged(surfs):
 A,B=surfs['004'],surfs['005'];return np.r_[A[0],B[0]],np.r_[A[1],B[1]+len(A[0])]
def meshes(cond,method):
 frames=read(RUN/'public/FRAMES.json');po={r['id']:np.array(r['C'])for r in read(RUN/'public/conditions'/(cond+'.json'))['frames']};t=np.array(read(RUN/'predictions'/cond/(method+'.json'))['T_005']);return {v:mesh_for(v,frames,po,np.eye(4)if v=='004'else t)for v in ['004','005']}
def camera(az,elev=30):
 center=np.array([0.,0.,-3.]);a,e=np.deg2rad([az,elev]);eye=center+32*np.array([np.cos(a)*np.cos(e),np.sin(a)*np.cos(e),np.sin(e)]);z=(center-eye)/np.linalg.norm(center-eye);x=np.cross(z,[0,0,1.]);x/=np.linalg.norm(x);y=np.cross(z,x);C=np.eye(4);C[:3,:3]=np.c_[x,y,z];C[:3,3]=eye;return C

def render(V,F,C):
 K=np.array([[370.,0,159.5],[0,370.,119.5],[0,0,1.]]);r=ray_map(V,F,K,C,(240,320));rgb=np.ones((240,320,3))*.96;valid=r['valid'];tri=V[F];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(1e-12,np.linalg.norm(n,axis=1))[:,None];shade=.35+.65*abs(n@C[:3,2]);rgb[valid]=np.array([.82,.44,.48])*shade[r['face'][valid],None];return rgb

def six_views():
 gt=np.load(T/'inputs/virtual_GT.npz');before=merged(meshes('V1','M0'));after=merged(meshes('V1','M2'));fig,axes=plt.subplots(6,3,figsize=(10,13));items=[(gt['V'],gt['F']),before,after]
 for i,az in enumerate([0,60,120,180,240,300]):
  C=camera(az)
  for j,(V,F)in enumerate(items):
   axes[i,j].imshow(render(V,F,C));axes[i,j].plot([15,15+5*370/32],[220,220],color='black',lw=2);axes[i,j].text(15,212,'5 mm at center plane',fontsize=6);axes[i,j].axis('off');axes[i,j].set_title(['GT (evaluation only)','V1 / M0 before','V1 / M2 Ring + RGB'][j]+f' | az {az} deg',fontsize=9)
 fig.suptitle('Same six cameras and mm scale | real triangles | SYNTHETIC_HERO_PROXY\nStatic original G01; no alignment / scaling / deformation',fontsize=12);fig.tight_layout();fig.savefig(OUT/'SIX_VIEWS.png',dpi=130);plt.close(fig)

def sections():
 gt=np.load(T/'inputs/virtual_GT.npz');fig,axes=plt.subplots(1,3,figsize=(12,4));styles=[('GT',(gt['V'],gt['F']),'black'),('M0',merged(meshes('V1','M0')),'#e78b24'),('M2',merged(meshes('V1','M2')),'#1669b4')]
 for ax,(axis,offset)in zip(axes,[(0,0),(1,0),(2,-2)]):
  for label,(V,F),color in styles:
   lines=plane_coordinates(mesh_sections(V,F,axis,offset),axis);ax.add_collection(LineCollection(lines,colors=color,linewidths=.7,label=label,alpha=.8))
  ax.autoscale();ax.set_aspect('equal');ax.set_title(f'Plane {"XYZ"[axis]} = {offset} mm');ax.set_xlabel('mm');ax.set_ylabel('mm');ax.legend(fontsize=8)
 fig.suptitle('Exact triangle / plane intersections | V1 | GT only for evaluation');fig.tight_layout();fig.savefig(OUT/'TRIANGLE_SECTIONS.png',dpi=150);plt.close(fig)

def matches():
 frames=read(RUN/'tracks/ADAPTER.json')['frames'];tr=np.load(RUN/'tracks/observations/tracks005.npz');lm=np.load(RUN/'predictions/V1/LANDMARKS.npz');fit=lm['track_ids'][~lm['held']];held=lm['track_ids'][lm['held']]
 # Deterministic diagnostic pair: most common accepted training tracks, no GT.
 choices=[]
 for i,a in enumerate(frames):
  for j,b in enumerate(frames):
   if a['video']=='004'and b['video']=='005':choices.append((int((np.isfinite(tr['xy'][fit,i,0])&np.isfinite(tr['xy'][fit,j,0])).sum()),-i,-j))
 _,ni,nj=max(choices);i,j=-ni,-nj;im=[cv2.imread(str(RUN/'public/images'/(frames[k]['id']+'.png')))[:,:,::-1]for k in [i,j]];canvas=np.concatenate(im,axis=1);fig,axes=plt.subplots(2,1,figsize=(12,7))
 axes[0].imshow(canvas);common=[tid for tid in fit if np.isfinite(tr['xy'][tid,[i,j]]).all()][:40]
 for k,tid in enumerate(common):
  p,q=tr['xy'][tid,i],tr['xy'][tid,j]+[640,0];axes[0].plot([p[0],q[0]],[p[1],q[1]],'-',lw=.5,color=plt.cm.hsv(k/max(len(common),1)))
 axes[0].set_title(f'Original V6 SIFT / mutual ratio .72 / RGB-only | {frames[i]["id"]} - {frames[j]["id"]} | first {len(common)} training links');axes[0].axis('off')
 axes[1].imshow(im[0]);poses={r['id']:np.array(r['C'])for r in read(RUN/'public/conditions/V1.json')['frames']};K=np.array(frames[i]['K']);C=poses[frames[i]['id']];Ts={m:np.array(read(RUN/'predictions/V1'/(m+'.json'))['T_005'])for m in ['M1','M2']}
 count=0
 for k,tid in enumerate(lm['track_ids']):
  if not lm['held'][k] or not np.isfinite(tr['xy'][tid,i]).all():continue
  obs=tr['xy'][tid,i];B=lm['points'][k,1];q1=safe_project(transform(B[None],Ts['M1']),K,C)[0];q2=safe_project(transform(B[None],Ts['M2']),K,C)[0];axes[1].plot(*obs,'go',ms=3);axes[1].plot([obs[0],q1[0]],[obs[1],q1[1]],color='orange',lw=1);axes[1].plot(*q2,'b+',ms=5);count+=1
 axes[1].set_xlim(0,640);axes[1].set_ylim(360,0);axes[1].set_title(f'{count} unused modulo-5 tracks: green RGB observation; orange Ring-only residual; blue Ring+RGB projection');axes[1].axis('off');fig.tight_layout();fig.savefig(OUT/'RGB_MATCH_REPROJECTION.png',dpi=150);plt.close(fig)
 save(OUT/'MATCH_FIGURE.json',dict(first=frames[i]['id'],second=frames[j]['id'],training_links_displayed=len(common),held_links_displayed=count,selection='maximum available training tracks; no GT selection'))

def failures():
 rows=read(OUT/'RESULTS.json');v2=[r for r in rows if r['condition'].startswith('V2')and r['method']=='M2'];chosen=next((r for r in v2 if not r['pose_pass']),v2[0]);cond=chosen['condition'];fig,axes=plt.subplots(1,3,figsize=(12,4));gt=np.load(T/'inputs/virtual_GT.npz');C=camera(90,80)
 for ax,(title,VF)in zip(axes,[('GT (same fixed scale)',(gt['V'],gt['F'])),('V1 M1: unresolved 30 deg yaw',merged(meshes('V1','M1'))),(cond+' M2: camera-noise residual',merged(meshes(cond,'M2')))]):ax.imshow(render(*VF,C));ax.set_title(title,fontsize=9);ax.axis('off')
 fig.suptitle('Retained negative controls / limitations | GT not used to select registration');fig.tight_layout();fig.savefig(OUT/'FAILURE_CONDITIONS.png',dpi=150);plt.close(fig)
 save(OUT/'FAILURE_FIGURE.json',dict(condition=cond,selection='first seed failing pre-registered pose threshold, else first seed; illustrative only',metrics=chosen))
if __name__=='__main__':six_views();sections();matches();failures()
