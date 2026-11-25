"""All original sources in their original mm coordinates, fixed six-view layout."""
import math,collections,html
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import trimesh,cv2
from common import *
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
F=T/'figures';F.mkdir(exist_ok=True)
angles=[('Oblique A',20,-60),('Oblique B',20,60),('Oblique C',20,180),('World X',0,0),('World Y',0,90),('World Z',89.9999,0)]
def mesh(r):
 p=Path(r['mesh_path'])
 if p.suffix=='.npz':
  a=np.load(p);d=np.load(Path(r['output'])/'NATIVE_RGB_LABELS.npz')if r['route']=='H004_RAW_BASELINE'else np.load(p.parent/'NATIVE_RGB_LABELS.npz');uv=a['uv'].astype(int);return a['V'],a['F'],d['RGB'][uv[:,1],uv[:,0]]/255.
 m=trimesh.load(p,process=False);return np.asarray(m.vertices),np.asarray(m.faces),np.asarray(m.visual.vertex_colors)[:,:3]/255.
def scale(ax,pxmm):
 wanted=60/max(pxmm,1e-12);power=10**math.floor(math.log10(wanted));mm=min([x*power for x in [1,2,5,10]],key=lambda x:abs(x-wanted));ax.plot([15,15+mm*pxmm],[370,370],color='black',lw=2);ax.text(15,358,f'~{mm:g} mm (center depth)',fontsize=6,backgroundcolor='white')
def six(rows,data,cad,bounds,path,title,source_color=False):
 vs=[];fs=[];cs=[];offset=0;palette=plt.get_cmap('turbo')
 for i,r in enumerate(rows):
  v,f,c=data[r['source_id']];vs.append(v);fs.append(f+offset);offset+=len(v);cs.append(np.tile(palette(i/max(1,len(rows)-1))[:3],(len(f),1))if source_color else c[f].mean(1))
 fig,axs=plt.subplots(1,6,figsize=(18,4))
 if rows:
  v=np.concatenate(vs);f=np.concatenate(fs);colors=np.concatenate(cs)
  for ax,(name,e,a)in zip(axs,angles):
   im,px=actual_mesh_image(v,f,cad['V'],cad['F'],bounds,e,a,'white',face_colors=colors);ax.imshow(im);scale(ax,px);ax.set_title(name,fontsize=9);ax.axis('off')
 else:
  for ax in axs:ax.text(.5,.5,'NO GENERATED SURFACE',ha='center');ax.axis('off')
 fig.suptitle(title+'\nFull extent; physical Ring CAD black; no ICP/scale/deformation/fusion; independent pose/registered-shape GT NOT_EVALUABLE',fontsize=9);fig.tight_layout();fig.savefig(path,dpi=105);plt.close(fig)
rows=read(B/'ALL_UNIQUE_SOURCES.json');assert len(rows)==174 and len(read(B/'H004_RESULTS.json'))==76
index=[]
for reg in read(P12/'evidence/INPUT_REGISTRY.json'):
 for route in ['H004_RAW_BASELINE','V6']:
  rr=sorted([r for r in rows if r['case']==reg['case']and r['route']==route],key=lambda r:(r['input_identity'][0]['raw_frame'],r['source_id']));usable=[r for r in rr if r.get('renderable')];data={r['source_id']:mesh(r)for r in usable};cad=dict(np.load(W/'runs/m2f5_unified/cad'/('R10.npz'if reg['ring_inner_mm']==10 else'R5.npz')));bounds=np.concatenate([cad['V']]+[data[r['source_id']][0]for r in usable]);prefix=route+'__'+reg['case'];formal=[r for r in usable if r['formal']];gauges=collections.defaultdict(list)
  for r in usable:gauges[r.get('v6_root','M2F12 independent video map')].append(r)
  caption=reg['case']+' / '+route;images=[]
  for subset,ss in [('ALL_NUMERIC',usable),('FORMAL',formal)]:
   for colored in [False,True]:
    name=prefix+'__'+subset+('__SOURCE'if colored else'__RGB')+'.png';six(ss,data,cad,bounds,F/name,caption+f' | {subset} {len(ss)} sources | '+('source colors in RAW-frame order'if colored else'actual RGB')+(' | multiple attempt gauges NOT registered'if subset=='ALL_NUMERIC'and len(gauges)>1 else''),colored);images.append(name)
  # Separate attempt gauges make diagnostic pooling explicit; never align them.
  gauge_images=[]
  if len(gauges)>1:
   for i,(g,ss)in enumerate(gauges.items()):
    name=prefix+f'__GAUGE_{i:02d}.png';own_bounds=np.concatenate([cad['V']]+[data[r['source_id']][0]for r in ss]);six(ss,data,cad,own_bounds,F/name,caption+f' | gauge {i} | '+g.split('/m2f10_v6_multiview/')[-1],True);gauge_images.append(dict(gauge=g,image=name,sources=[x['source_id']for x in ss]))
  # Every source receives its own side-view cell; occluded union surfaces remain visible here.
  if usable:
   cols=6;nrows=math.ceil(len(usable)/cols);fig,axs=plt.subplots(nrows,cols,figsize=(15,2.7*nrows),squeeze=False)
   for ax,r in zip(axs.flat,usable):
    v,f,c=data[r['source_id']];im,px=actual_mesh_image(v,f,cad['V'],cad['F'],bounds,0,90,'white',face_colors=c[f].mean(1));ax.imshow(im);scale(ax,px);ax.set_title(f"RAW {r['input_identity'][0]['raw_frame']} | {'formal'if r['formal']else'diagnostic'}\nRing MAE {r['ring']['MAE_mm']:.2f}, P95 {r['ring']['p95_mm']:.2f} mm",fontsize=7);ax.axis('off')
   for ax in list(axs.flat)[len(usable):]:ax.axis('off')
   fig.suptitle(caption+' | EVERY unique source, World Y, shared full extent; no hidden-source omission',fontsize=10);fig.tight_layout();name=prefix+'__EVERY_SOURCE_ATLAS.png';fig.savefig(F/name,dpi=100);plt.close(fig);images.append(name)
   # Three predetermined chronological representatives, not quality-selected.
   picks=sorted(set([0,len(usable)//2,len(usable)-1]));fig,axs=plt.subplots(len(picks),6,figsize=(18,3.2*len(picks)),squeeze=False)
   for i,j in enumerate(picks):
    r=usable[j];fs0=oldhero.frames(r);d=np.load(r['display_diagnostics']);ax=axs[i]
    ax[0].imshow(fs0[0]['RGB']);ax[0].set_title(f"Target RAW {fs0[0]['raw_frame']} qualified={r['target_qualified']}",fontsize=8)
    ax[1].imshow(fs0[0]['labels'],vmin=0,vmax=2,cmap='viridis');ax[1].set_title('Actual target labels: 0/1/2',fontsize=8)
    supports=np.concatenate([cv2.resize(f['RGB'],(213,120))for f in fs0[1:]],axis=0);ax[2].imshow(supports);ax[2].set_title('Supports '+','.join(str(f['raw_frame'])for f in fs0[1:])+'\nqualified='+str(r['support_qualified']),fontsize=7)
    im=ax[3].imshow(d['ring_heat_mm'],cmap='magma',vmin=0,vmax=5);fig.colorbar(im,ax=ax[3],fraction=.035,extend='max');ax[3].set_title(f"Ring MAE/P95 {r['ring']['MAE_mm']:.2f}/{r['ring']['p95_mm']:.2f} mm\n>5mm: {r['ring']['over_5mm_count']} ({r['ring']['over_5mm_fraction']:.1%}); max {r['ring']['max_mm']:.2f}",fontsize=7)
    ax[4].imshow(d['A_to_B_RGBA']);ax[4].set_title('A original triangles/RGB → B\nB participated as HERO support',fontsize=8)
    im=ax[5].imshow(d['A_to_B_error'],vmin=0,vmax=80,cmap='magma');fig.colorbar(im,ax=ax[5],fraction=.035,extend='max');ax[5].set_title(f"conditional A→B: coverage {r['a_to_b']['target_coverage']:.1%}\nRGB MAE {r['a_to_b']['RGB_MAE_0_255']:.2f} /255",fontsize=8)
    for a in ax:a.axis('off')
   fig.suptitle(caption+' | first / middle / last generated source; Ring physical inner diameter '+str(reg['ring_inner_mm'])+' mm; no pose GT',fontsize=10);fig.tight_layout();name=prefix+'__REPRESENTATIVES.png';fig.savefig(F/name,dpi=100);plt.close(fig);images.append(name)
   fig=plt.figure(figsize=(8,6));ax=fig.add_subplot(projection='3d');th=np.linspace(0,2*np.pi,120);rad=reg['ring_inner_mm']/2+.6;ax.plot(rad*np.cos(th),rad*np.sin(th),0*th,color='black');allc=[]
   for i,(g,ss)in enumerate(gauges.items()):
    seen={}
    for r in ss:
     for x in r['input_identity']:seen[(x['raw_frame'],json.dumps(x['C']))]=x
    cc=sorted(seen.values(),key=lambda x:x['raw_frame']);C=np.array([x['C']for x in cc])[:,:3,3];allc.append(C);ax.plot(*C.T,marker='.',label=f'gauge {i}')
    for x,c in zip(cc,C):ax.text(*c,str(x['raw_frame']),fontsize=5)
   ax.set(xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');ax.set_title(caption+'\nAll source Target/Support centers and RAW frame IDs; original gauges',fontsize=8);ax.legend(fontsize=7);fig.tight_layout();name=prefix+'__CAMERAS.png';fig.savefig(F/name,dpi=120);plt.close(fig);images.append(name)
  index.append(dict(case=reg['case'],route=route,sources=len(rr),renderable=len(usable),formal=len(formal),bbox_min_mm=bounds.min(0).tolist(),bbox_max_mm=bounds.max(0).tolist(),images=images,gauge_images=gauge_images));save(T/'evidence/VISUALIZATION_INDEX.json',index);print('VIDEO_FIGURES',reg['case'],route,len(usable),flush=True)
