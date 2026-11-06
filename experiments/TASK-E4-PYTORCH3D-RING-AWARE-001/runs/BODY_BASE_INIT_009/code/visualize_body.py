from common import *
from evaluate import pointcast
import ast,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import open3d as o3d
SRC=R.parents[1]/'code/figures.py'
for n in ast.parse(SRC.read_text()).body:
 if isinstance(n,ast.FunctionDef)and n.name in['actual_mesh_image','edge']:
  s=ast.get_source_segment(SRC.read_text(),n)
  if n.name=='actual_mesh_image':
   s=s.replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]',"rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]")
  exec(compile(s,str(SRC)+':reuse','exec'),globals())
COL={'A':'#9b9da0','B':'#2f84bf','C':'#e79b2b','CONTOUR':'#ab70b5','DEPTH':'#2f84bf'}
CACHE={}
def finish(fig,name,dpi=130):
 p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=dpi,bbox_inches='tight');plt.close(fig)
def model(c,tag):
 if tag=='A':
  a=dict(np.load(R/'inputs'/c/'INITIAL.npz'));return dict(a,F_solid=a['F'],inferred_base_faces=np.zeros(len(a['F']),bool))
 return dict(np.load(R/'local_results'/c/(tag+'.npz')))
def project(P,K,T):
 p=(P-T[:3,3])@T[:3,:3];q=p@K.T;return q[:,:2]/q[:,2:]
def viewer(V0,RV,elev,azim):
 allv=np.r_[V0,RV];center=(allv.min(0)+allv.max(0))/2;rad=np.linalg.norm(allv-center,axis=1).max();el,az=np.radians([elev,azim]);pos=center+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);forward=(center-pos)/np.linalg.norm(center-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);T=np.eye(4);T[:3,:3]=np.array([right,down,forward]).T;T[:3,3]=pos;K=np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]]);return K,T

def common_bounds(c):return np.concatenate([model(c,t)['V']for t in['A','B_SELECTED','C_SELECTED']])
def plane_lines(ax,c,K,T,bounds,color='#18a9b0'):
 base=load(R/'inputs'/c/'BASE.json')
 if base['plane']is None:return
 Q=np.array(base['plane_basis']);anchor=np.array(base['anchor']);span=min(20,max(4,np.ptp(bounds,axis=0).max()*.6));P=anchor+np.array([[-span,-span],[span,-span],[span,span],[-span,span],[-span,-span]])@Q[:,:2].T;q=project(P,K,T);ax.plot(q[:,0],q[:,1],color=color,lw=.8,ls='--');p=project(np.r_[anchor[None],(anchor+Q[:,2])[None]],K,T);ax.annotate('',xy=p[1],xytext=p[0],arrowprops=dict(arrowstyle='->',color=color,lw=.8))
def meshpanel(ax,c,tag,color='B',angle=(25,-65),underground=False):
 key=(c,tag,color,angle,underground)
 if key not in CACHE:
  a=model(c,tag);rr=np.load(R/'inputs'/c/'RING.npz');bound=common_bounds(c);F=a['F_solid'];colors=np.tile(matplotlib.colors.to_rgb(COL[color]),(len(F),1));colors[a['inferred_base_faces']]=[.58,.58,.58];base=load(R/'inputs'/c/'BASE.json')
  if underground and base['plane']is not None:
   plane=np.array(base['plane']);below=(a['V'][F].mean(1)@plane[:3]+plane[3])<0;colors[below]=[.66,.66,.66]
  im,pxmm=actual_mesh_image(a['V'],F,rr['V'],rr['F'],bound,*angle,COL[color],colors);K,T=viewer(bound,rr['V'],*angle);CACHE[key]=(im,pxmm,K,T,bound)
 im,pxmm,K,T,bound=CACHE[key];ax.imshow(im);plane_lines(ax,c,K,T,bound);ax.plot([20,20+2*pxmm],[375,375],c='black',lw=1.5);ax.text(20,365,'2 mm at viewer-center',fontsize=5);ax.set(xlim=(0,400),ylim=(400,0));ax.axis('off')
 if tag in['A','B_SELECTED','C_SELECTED']:
  arm=tag[0];qa=next(x for x in load(R/'metrics/CASE_MODEL_RESULTS_WITH_GEOMETRY.json')if x['case']==c and x['arm']==arm);text='CAD pairs '+str(qa['CAD_triangle_pair_N'])+' | inside '+str(qa['Ring_inside_body_N'])+' | self '+str(qa['nonadjacent_self_pair_N']);ax.text(.02,.98,text,transform=ax.transAxes,va='top',fontsize=5,color='red'if qa['Ring_collision']or qa['Ring_inside_body_N']else'dimgray')
def rgbpanel(ax,c,cid,overlays=False):
 a=np.load(R/'inputs'/c/(cid+'.npz'));ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan')
 if overlays:
  rr=np.load(R/'inputs'/c/'RING.npz');cz=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640)
  for arm,tag in[('A','A'),('B','B_SELECTED'),('C','C_SELECTED')]:
   b=model(c,tag);z=cast(scene(b['V'],b['F']),a['K'],a['T'],360,640);edge(ax,np.isfinite(z)&(z<cz),COL[arm])
 ax.set(xlim=(0,640),ylim=(360,0));ax.axis('off')
def bgpanel(ax,c):
 base=load(R/'inputs'/c/'BASE.json');cid=base['primary'];a=np.load(R/'inputs'/c/(cid+'.npz'));ev=np.load(R/'inputs'/c/'BASE_EVIDENCE.npz');q=ev['background_RGB_uv'];q=q[:,:2]/q[:,2:];ax.imshow(a['RGB']);ax.scatter(q[:,0],q[:,1],s=.2,c='#1a9bc4',alpha=.4);plane_lines(ax,c,a['K'],a['T'],common_bounds(c));ax.set(xlim=(0,640),ylim=(360,0));ax.axis('off');ax.set_title('HERO background ROI + independent plane\n'+base['base_status']+' | contact '+base['contact_status'],fontsize=7)
def detail(c,core=False):
 meta=getcase(c);base=load(R/'inputs'/c/'BASE.json');fig,axs=plt.subplots(4,4,figsize=(17,15));vs=meta['views'];fit=[v for v in vs if v['role']=='FIT'];held=[v for v in vs if v['role']!='FIT'];shown=(fit[:2]+held[:1])[:3]
 for j,v in enumerate(shown):rgbpanel(axs[0,j],c,v['id'],True);axs[0,j].set_title(v['id']+' | '+v['role']+'\ntarget lime, A gray, B blue, C orange',fontsize=8)
 axs[0,3].axis('off');axs[0,3].text(0,.95,f"{c} | {meta['morphology']} | {meta['ring']}\nphysical: {meta['physical_specimen']}\n\nInput complete; historical gates diagnostic only\nBase: {base['base_status']}\nContact: {base['contact_status']}\nSupported/contact samples: {base['contact_supported_N']}/{base['contact_N']}\nC hard truncation permitted: {base['truncate_allowed']}\n\nAbsolute shape/height/volume GT:\nNOT_EVALUABLE",va='top',fontsize=9)
 cid=base['primary'];a=np.load(R/'inputs'/c/(cid+'.npz'));o=np.load(R/'depth_observations'/(cid+'.npz'));rgbpanel(axs[1,0],c,cid);sc=axs[1,0].scatter(o['RGB_uv'][:,0],o['RGB_uv'][:,1],c=o['z'],s=6,cmap='viridis');fig.colorbar(sc,ax=axs[1,0],fraction=.035,label='native HERO axial Z mm');axs[1,0].set_title('Fixed reliable internal observations\nN=%d; original Pixel IDs; no boundary fit'%len(o['z']),fontsize=8);bgpanel(axs[1,1],c)
 meshpanel(axs[1,2],c,'A','A',angle=(10,-65));ev=np.load(R/'inputs'/c/'BASE_EVIDENCE.npz');rr=np.load(R/'inputs'/c/'RING.npz');K,T=viewer(common_bounds(c),rr['V'],10,-65);xy=project(ev['background_XYZ'],K,T);ok=np.isfinite(xy).all(1);axs[1,2].scatter(xy[ok,0],xy[ok,1],c=ev['background_RGB'][ok]/255,s=.4,alpha=.7);axs[1,2].set(xlim=(0,400),ylim=(400,0));axs[1,2].set_title('Actual background XYZ + CAD\ncyan estimated plane, not Ring plane',fontsize=8)
 h=ev['background_XYZ']@np.array(base['plane'])[:3]+base['plane'][3]if base['plane']is not None else np.empty(0);axs[1,3].hist(h,bins=40,color='#459bb7');axs[1,3].axvline(-.3,c='red',ls=':');axs[1,3].axvline(.3,c='red',ls=':');axs[1,3].set(xlabel='background signed residual mm',ylabel='point count',title='Fixed 5-45px ROI RANSAC residual\nROI normal spread %.2f deg / offset %.2f mm'%(base['max_normal_change_deg']or 0,base['max_anchor_offset_change_mm']or 0));axs[1,3].tick_params(labelsize=7)
 for j,(tag,color,title)in enumerate([('A','A','P0-A original baseline'),('B_SELECTED','B','P0-B refit; gray = below estimated base'),('C_SELECTED','C','P0-C; gray closure is inferred, not observed')]):
  meshpanel(axs[2,j],c,tag,color,angle=(0,-65),underground=tag!='C_SELECTED');axs[2,j].set_title(title,fontsize=8)
 C=load(R/'local_results'/c/'C_SELECTED.json');B=load(R/'local_results'/c/'B_SELECTED.json');axs[2,3].axis('off');axs[2,3].text(0,.95,'B: '+B['selection_status']+'\n'+B['meta']['family']+f", {len(B['p'])} parameters\n\nC: "+C['selection_status']+'\n'+C['meta']['family']+f", {len(C['p'])} parameters\n\nGray below-plane faces: visualization only.\nOriginal HERO/old P0 never trimmed.\nC closure is bookkeeping only and\nexcluded from silhouette/depth rays.\n\nNo real 3D GT, no depth registration.",va='top',fontsize=8,wrap=True)
 seed=B.get('seed')
 if seed is None:
  first=np.array(B['history'][0]['parameters'])[:9];dist=[np.linalg.norm(np.array(load(R/'local_results'/c/f'B_seed{s}_DEPTH.json')['p'])-first)for s in[0,1,2]];seed=int(np.argmin(dist))
 for j,(tag,col,title)in enumerate([('A','A','Initial baseline'),(f'B_seed{seed}_CONTOUR','CONTOUR','Actual contour stage'),('B_SELECTED','B','Actual internal-depth stage'),('C_SELECTED','C','Final base relationship')]):meshpanel(axs[3,j],c,tag,col,angle=(25,-65),underground=tag not in['C_SELECTED']);axs[3,j].set_title(title,fontsize=8)
 fig.suptitle(c+' | '+meta['morphology']+' body/base initialization | same mm frame and common viewer across model stages\nOriginal RGB/labels and native HERO evidence; black solid CAD; dashed cyan plane is estimated from tissue background.\nHistorical quality labels never prevent running. Truncation is observation-driven; inferred closure/hidden geometry is not accuracy truth.',fontsize=11);fig.tight_layout(rect=[0,0,1,.93]);finish(fig,('Fig_'+meta['morphology']+'_Detailed.png')if core else('full/'+c+'_Detailed.png'))

def main():
 assert(R/'assets_index/PREDICTIONS_FROZEN.json').exists();cases=load(R/'config/CASE_LOCK.json');fig=plt.figure(figsize=(28,20));gs=fig.add_gridspec(3,3,hspace=.24,wspace=.08)
 for i,kind in enumerate(['Ip','Is','IIa']):
  cc=[c for c in cases if c['morphology']==kind]
  for j,c in enumerate(cc):
   n=c['name'];sub=gs[i,j].subgridspec(2,3,hspace=.22,wspace=.05);axs=np.array([[fig.add_subplot(sub[a,b])for b in range(3)]for a in range(2)]);primary=load(R/'inputs'/n/'BASE.json')['primary'];rgbpanel(axs[0,0],n,primary);axs[0,0].set_title(n+' | '+kind+' | real RGB + original Mask',fontsize=8);bgpanel(axs[0,1],n);meshpanel(axs[0,2],n,'A','A',underground=True);axs[0,2].set_title('P0-A frozen/old-rule baseline',fontsize=8)
   for a,tag,col in[(axs[1,0],'B_SELECTED','B'),(axs[1,1],'C_SELECTED','C')]:
    meshpanel(a,n,tag,col,underground=tag=='B_SELECTED');m=load(R/'local_results'/n/(tag+'.json'));a.set_title(tag[0]+' | '+m['meta']['family']+' | '+str(len(m['p']))+' parameters\n'+m['selection_status'],fontsize=6,color='red'if'INFEASIBLE'in m['selection_status']or'NO_FEASIBLE'in m['selection_status']else'black')
   held=next(v for v in c['views']if v['role']!='FIT');rgbpanel(axs[1,2],n,held['id'],True);axs[1,2].set_title('Fixed heldout projection A/B/C\n'+held['id'],fontsize=7)
 fig.suptitle('Nine independent real polyps | rows Ip / Is / IIa, three distinct physical groups each\nPer case: RGB/Mask, background ROI/base, P0-A, P0-B, P0-C, fixed heldout overlay.\nBlack solid Ring CAD; gray below-plane/inferred closure is not a measured surface. Same viewer/physical scale across A/B/C within each case. No GT accuracy claim.',fontsize=13);finish(fig,'Fig_Overview_Nine_Cases.png',130)
 for c in cases:detail(c['name'],core=False)
 for n in['G01','G07','G06']:detail(n,core=True)
 save('assets_index/VISUALIZATION_SOURCE.json',dict(reused_renderer=asset(SRC),source_functions=['actual_mesh_image','edge'],adaptation='face colors for inferred base/below-plane diagnostic only; annotation projection uses identical viewer transform',viewer_bounds='one common union of A/B/C per case, shared across all stages; no clipping unfavorable geometry',inferred_base_not_observed=True,all_nine_cases_shown=True,selected_detail_cases_frozen=['G01','G07','G06']))
 print('NINE_OVERVIEW_AND_DETAILS_DONE')
if __name__=='__main__':main()
