"""Supplement full-extent images with counted-frustum close views and original aliases."""
import ast
from common import *
p=T/'code/render_all.py';tree=ast.parse(p.read_text());prefix=[]
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='rows'for t in n.targets):break
 prefix.append(n)
exec(compile(ast.Module(body=prefix,type_ignores=[]),str(p),'exec'))
def clipped(v,f,cad,bounds,e,a):
 allv=np.r_[bounds,cad['V']];center=(allv.min(0)+allv.max(0))/2;rad=np.linalg.norm(allv-center,axis=1).max();el,az=np.radians([e,a]);pos=center+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
 forward=(center-pos)/np.linalg.norm(center-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);q=(v-pos)@np.array([right,down,forward]).T;uv=q[:,:2]/q[:,2,None]*490+199.5;outside=(q[:,2]<=0)|(~np.isfinite(uv).all(1))|(uv<0).any(1)|(uv>=400).any(1)
 return dict(vertices_outside=int(outside.sum()),faces_partly_or_fully_outside=int(outside[f].any(1).sum()),total_vertices=len(v),total_faces=len(f))
rows=read(B/'ALL_UNIQUE_SOURCES.json');aliases=read(B/'ALL_ALIAS_RESULTS.json');index=read(T/'evidence/VISUALIZATION_INDEX.json');receipts=[]
for entry in index:
 rr=sorted([r for r in rows if r['case']==entry['case']and r['route']==entry['route']and r['renderable']],key=lambda r:(r['input_identity'][0]['raw_frame'],r['source_id']))
 aa=sorted([r for r in aliases if r['case']==entry['case']and r['route']==entry['route']and r['renderable']],key=lambda r:(r['input_identity'][0]['raw_frame'],r['source_id']))
 if not rr:continue
 cad=dict(np.load(W/'runs/m2f5_unified/cad'/('R10.npz'if rr[0]['ring_inner_mm']==10 else'R5.npz')));data={r['source_id']:mesh(r)for r in rr+aa};prefix=entry['route']+'__'+entry['case'];near=np.array([[-12,-12,-12],[12,12,12]],float)
 groups=collections.defaultdict(list)
 for r in rr:groups[r.get('v6_root','H004')].append(r)
 entry['near_images']=[]
 for j,(g,ss) in enumerate(groups.items()):
  vs=[];fs=[];cs=[];off=0
  for i,r in enumerate(ss):
   v,f,c=data[r['source_id']];vs.append(v);fs.append(f+off);off+=len(v);cs.append(np.tile(plt.get_cmap('turbo')(i/max(1,len(ss)-1))[:3],(len(f),1)))
  v=np.concatenate(vs);f=np.concatenate(fs);color=np.concatenate(cs);fig,axs=plt.subplots(1,6,figsize=(18,4));counts=[]
  for ax,(name,e,a)in zip(axs,angles):
   im,px=actual_mesh_image(v,f,cad['V'],cad['F'],near,e,a,'white',face_colors=color);count=clipped(v,f,cad,near,e,a);counts.append(dict(view=name,**count));ax.imshow(im);scale(ax,px);ax.set_title(name+f"\nclipped V {count['vertices_outside']}/{len(v)}, F {count['faces_partly_or_fully_outside']}/{len(f)}",fontsize=7);ax.axis('off')
  fig.suptitle(prefix+f' | original gauge {j} | CLOSE VIEW ONLY (viewer bounds +/-12 mm)\nAll triangles retained; per-view frustum clipping counted, including partial faces. Full extent in companion images.',fontsize=9);fig.tight_layout();name=prefix+f'__NEAR_GAUGE_{j:02d}.png';fig.savefig(F/name,dpi=105);plt.close(fig);entry['near_images'].append(dict(gauge=g,image=name,sources=[r['source_id']for r in ss]));receipts.append(dict(case=entry['case'],route=entry['route'],gauge=g,counts=counts))
 if aa:
  cols=4;nrows=math.ceil(len(aa)/cols);fig,axs=plt.subplots(nrows,cols,figsize=(13,3.2*nrows),squeeze=False);bounds=np.concatenate([cad['V']]+[data[r['source_id']][0]for r in rr+aa])
  for ax,r in zip(axs.flat,aa):
   v,f,c=data[r['source_id']];im,px=actual_mesh_image(v,f,cad['V'],cad['F'],bounds,0,90,'white',face_colors=c[f].mean(1));ax.imshow(im);scale(ax,px);ax.axis('off');ax.set_title(r['source_id'].replace(entry['case'],'')+f"\nRAW {r['input_identity'][0]['raw_frame']}; Ring {r['ring']['MAE_mm']:.2f}/{r['ring']['p95_mm']:.2f} mm",fontsize=6)
  for ax in list(axs.flat)[len(aa):]:ax.axis('off')
  fig.suptitle(prefix+' | ALL DUPLICATE-INPUT ORIGINAL OUTPUTS\nNot counted twice. Own original mesh definition and metrics preserved; no output averaging.',fontsize=9);fig.tight_layout();name=prefix+'__ALIAS_ORIGINALS.png';fig.savefig(F/name,dpi=110);plt.close(fig);entry['images'].append(name)
 save(T/'evidence/VISUALIZATION_INDEX.json',index);print('SUPPLEMENT',prefix,len(groups),len(aa),flush=True)
save(T/'evidence/CLOSE_VIEW_CLIPPING.json',receipts)
