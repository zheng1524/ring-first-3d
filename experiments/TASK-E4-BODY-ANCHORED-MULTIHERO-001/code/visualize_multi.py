"""Actual native triangles, no smoothing or deletion; shared fixed metric bounds."""
from native_multi import *
import ast,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colormaps
SRC=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/code/figures.py';node=next(n for n in ast.parse(SRC.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='actual_mesh_image');source=ast.get_source_segment(SRC.read_text(),node).replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]','rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]');exec(compile(source,str(SRC)+':reuse_facecolors','exec'),globals())
ANGLES=[(25,-65),(5,20),(0,110)]
def color(i):return matplotlib.colors.hsv_to_rgb([(i*.61803398875)%1,.65,.85])
def combine(parts):
 V=[];F=[];C=[];off=0
 for v,f,c in parts:
  V.append(v);F.append(f+off);co=np.asarray(c);C.append(np.tile(co,(len(f),1))if co.ndim==1 else co);off+=len(v)
 return np.concatenate(V),np.concatenate(F),np.concatenate(C)
def panel(ax,parts,ring,bounds,title,angle=ANGLES[0]):
 V,F,C=combine(parts);im,sc=actual_mesh_image(V,F,ring['V'],ring['F'],bounds,*angle,'#6677aa',C);ax.imshow(im);ax.plot([15,15+2*sc],[378,378],c='k',lw=2);ax.text(15,364,'2 mm at center depth',fontsize=6);ax.set_title(title,fontsize=8);ax.axis('off')
def finish(fig,name):fig.savefig(R/'figures'/name,dpi=140,bbox_inches='tight');plt.close(fig)
def sources(g):return [Source(s)for s in load(R/'config/SOURCES.json')if s['group']==g]
def setparams(ss,data):
 ids=list(data['source_ids'])
 for s in ss:s.theta=data['theta'][ids.index(s.id)]
def parts(ss):return [(s.vertices(),s.m['F'],color(i))for i,s in enumerate(ss)]
def main():
 assert load(R/'provenance/PREDICTIONS_FROZEN.json')['completed']==16
 data={};fig,axs=plt.subplots(4,4,figsize=(15,14))
 for gi,g in enumerate(CFG['groups']):
  ss=sources(g);ring=dict(np.load(R/'inputs'/g/'RING.npz'));initial=dict(np.load(R/'inputs'/g/'INITIAL.npz'));outs={a:dict(np.load(R/'runs'/g/a/'FINAL.npz'))for a in CFG['arms']};bounds=np.concatenate([ring['V'],initial['V']]+[s.m['V'][np.unique(s.m['F'])]for s in ss]);data[g]=(ss,ring,initial,outs,bounds)
  for j,a in enumerate(CFG['arms']):
   setparams(ss,outs[a]);pp=parts(ss);pp+=[(outs[a]['V'],outs[a]['F'],[.50,.50,.70])];panel(axs[gi,j],pp,ring,bounds,g+' '+a+' | all TRUSTED sources + Body')
 finish(fig,'Fig1_Four_Group_B0_B3.png')
 for g,(ss,ring,initial,outs,bounds)in data.items():
  fig,axs=plt.subplots(3,4,figsize=(15,11))
  for ai,angle in enumerate(ANGLES):
   for j,a in enumerate(CFG['arms']):setparams(ss,outs[a]);panel(axs[ai,j],parts(ss)+[(outs[a]['V'],outs[a]['F'],[.5,.5,.7])],ring,bounds,g+' '+a+' | '+str(angle),angle)
  finish(fig,g+'_FIXED_THREE_DIRECTIONS.png')
 # Corrected vs native source geometric relationships; do not hide residual petals.
 fig,axs=plt.subplots(4,3,figsize=(14,15))
 for gi,g in enumerate(CFG['groups']):
  ss,ring,initial,outs,bounds=data[g];setparams(ss,outs['B0']);panel(axs[gi,0],parts(ss),ring,bounds,g+' native TRUSTED')
  setparams(ss,outs['B1']);panel(axs[gi,1],parts(ss),ring,bounds,g+' B1 bias-only')
  setparams(ss,outs['B3']);panel(axs[gi,2],parts(ss),ring,bounds,g+' B3 alternating final')
 finish(fig,'Fig2_HERO_Ray_Correction.png')
 fig,axs=plt.subplots(4,3,figsize=(14,15))
 for gi,g in enumerate(CFG['groups']):
  ss,ring,initial,outs,bounds=data[g];o=outs['B3'];setparams(ss,o);body=scene(o['V'],o['F']);pp=[]
  for s in ss:
   z=np.load(R/'local_results'/(g+'_B3_'+s.id+'_CORRESPONDENCE.npz'));tree=cKDTree(s.uv);cent=s.m['V'][s.m['F']].mean(1);pu,pz=project(cent,s.C,s.K);dist,idx=tree.query(pu);state=z['state'][idx].copy();state[(dist>2)|(pz<=0)]=3;palette=np.array([[.1,.7,.3],[.95,.7,.15],[.85,.15,.15],[.6,.6,.6]]);co=palette[state];pp.append((s.vertices(),s.m['F'],co))
  panel(axs[gi,0],pp,ring,bounds,g+' MATCHED green / UNEXPLAINED yellow\nCONFLICT red / UNKNOWN gray')
  disp=np.linalg.norm(o['V']-initial['V'],axis=1);face=colormaps['viridis'](np.minimum(disp[o['F']].mean(1)/.35,1))[:,:3];panel(axs[gi,1],[(o['V'],o['F'],face)],ring,bounds,g+' Body displacement [0,0.35] mm\n'+str(round(disp.max(),6))+' mm max')
  # Actual cross sections in world Y; raw triangles crossing the plane, no fill.
  ax=axs[gi,2];y=float(np.median(initial['V'][:,1]));segments=[]
  for a,col in [('B0','gray'),('B3','#6b43ba')]:
   m=trimesh.Trimesh(outs[a]['V'],outs[a]['F'],process=False);sec=trimesh.intersections.mesh_plane(m,[0,1,0],[0,y,0])
   for line in sec:ax.plot(line[:,0],line[:,2],c=col,lw=.9)
  for i,s in enumerate(ss):
   m=trimesh.Trimesh(s.vertices(),s.m['F'],process=False);sec=trimesh.intersections.mesh_plane(m,[0,1,0],[0,y,0])
   for line in sec:ax.plot(line[:,0],line[:,2],c=color(i),lw=.4,alpha=.6)
  ax.set(title=g+' real section Y=%.3f mm'%y,xlabel='world X mm',ylabel='world Z mm');ax.axis('equal');ax.grid(alpha=.2)
 finish(fig,'Fig3_Correspondences_Displacement_Sections.png')
 fig,axs=plt.subplots(4,4,figsize=(16,13));summary=load(R/'metrics/COMPARISON.json')
 for gi,g in enumerate(CFG['groups']):
  for arm,c in [('B1','#db9c36'),('B2','#3797b1'),('B3','#7649b0')]:
   history=load(R/'metrics'/(g+'_'+arm+'_ROUNDS.json'));x=[0]+[r['round']for r in history];baseline=next(z for z in summary if z['group']==g and z['arm']=='B0');ys=[[baseline['fixed_penalty_10mm']]+[sum(z['fixed_penalty_mm']*z['N']for z in r['after']['sources'])/r['after']['N']for r in history],[baseline['hit_ratio']]+[r['after']['hit']/r['after']['N']for r in history],[0]+[r['max_Body_displacement_mm']for r in history]]
   for j,y in enumerate(ys):axs[gi,j].plot(x,y,'o-',c=c,label=arm,ms=3)
   volumes=[]
   for k in ['INITIAL']+['ROUND_%02d'%r['round']for r in history]:
    a=np.load(R/'runs'/g/arm/(k+'.npz'));m=trimesh.Trimesh(a['V'],a['F_solid'],process=False);volumes.append(abs(m.volume))
   axs[gi,3].plot(x,volumes,'o-',c=c,label=arm,ms=3)
  for j,t in enumerate(['fixed-N depth penalty (mm)','native hit ratio','cumulative Body displacement (mm)','conditional model volume (mm3)']):axs[gi,j].set(title=g+' '+t,xlabel='outer round');axs[gi,j].grid(alpha=.2);axs[gi,j].legend(fontsize=6)
 finish(fig,'Fig4_Round_Coverage_Displacement_Volume.png')
 # Saved complete objectives and candidate-vs-rollback diagnostics, not only accepted curves.
 fig,axs=plt.subplots(2,2,figsize=(12,8))
 for gi,g in enumerate(CFG['groups']):
  ax=axs.ravel()[gi]
  for arm,col in [('B1','#db9c36'),('B2','#3797b1'),('B3','#7649b0')]:
   hh=load(R/'metrics'/(g+'_'+arm+'_ROUNDS.json'));ax.plot([r['round']for r in hh],[r['initial_fixed_objective']for r in hh],'o-',c=col,label=arm+' before');ax.plot([r['round']for r in hh],[r['candidate_loss']for r in hh],'x--',c=col,label=arm+' candidate')
  ax.set(title=g+' fixed-correspondence objective (candidate may roll back)',xlabel='round',ylabel='dimensionless objective');ax.grid(alpha=.2);ax.legend(fontsize=6)
 finish(fig,'Detail_Actual_Losses_and_Rejected_Candidates.png')
 # Exact mesh/plane intersections at three preregistered relative heights; no anatomical labels invented.
 for g,(ss,ring,initial,outs,bounds)in data.items():
  setparams(ss,outs['B3']);fig,axs=plt.subplots(1,3,figsize=(14,4));zq=np.quantile(initial['V'][:,2],[.2,.5,.8])
  for j,z in enumerate(zq):
   ax=axs[j]
   for a,col in [('B0','gray'),('B3','#6b43ba')]:
    m=trimesh.Trimesh(outs[a]['V'],outs[a]['F'],process=False);section=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z])
    for line in section:ax.plot(line[:,0],line[:,1],c=col,lw=1.2)
   for i,src in enumerate(ss):
    m=trimesh.Trimesh(src.vertices(),src.m['F'],process=False);section=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z])
    for line in section:ax.plot(line[:,0],line[:,1],c=color(i),lw=.55,alpha=.7)
   ax.set(title=g+' world Z=%.3f mm'%z,xlabel='world X mm',ylabel='world Y mm');ax.axis('equal');ax.grid(alpha=.2)
  fig.suptitle('Actual 20/50/80 percent initial-world-Z sections; source-specific colors. Anatomy UNKNOWN without annotations.')
  finish(fig,g+'_Three_Actual_Sections.png')
 # Complete source legend and interactive independently switchable native/corrected geometry layers.
 exportrows=[]
 for g,(ss,ring,initial,outs,bounds)in data.items():
  sc=trimesh.Scene();sc.graph.update(frame_to='millimetres_to_metres',matrix=np.diag([.001,.001,.001,1.]));layers=[]
  def add(name,V,F,c):
   m=trimesh.Trimesh(V,F,process=False);m.remove_unreferenced_vertices();m.visual.face_colors=np.tile(np.r_[np.array(c)*255,255].astype(np.uint8),(len(F),1));sc.add_geometry(m,node_name=name,geom_name=name,parent_node_name='millimetres_to_metres');layers.append(name)
  add('Ring_CAD',ring['V'],ring['F'],[.025]*3)
  for arm in CFG['arms']:
   add('Body_'+arm,outs[arm]['V'],outs[arm]['F'],[.45,.45,.75])
   if outs[arm]['inferred_base_faces'].any():add('Inferred_CAP_'+arm,outs[arm]['V'],outs[arm]['F_solid'][outs[arm]['inferred_base_faces']],[.65,.65,.65])
  for rd in (R/'runs'/g/'B3').glob('ROUND_*.npz'):
   a=np.load(rd);add('Body_B3_'+rd.stem,a['V'],a['F_solid'],[.5,.35,.75])
  for i,s in enumerate(ss):
   for arm in ['B0','B1','B3']:
    setparams([s],outs[arm]);add('HERO_'+arm+'__'+s.id,s.vertices(),s.m['F'],color(i))
    if arm!='B0'and np.max(abs(s.theta))>0:
     dest=R/'local_results'/'derived_HERO'/g/s.id;dest.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest/(arm+'_DERIVED.npz'),V=s.vertices(),F=s.m['F'],original_face_id=s.m['original_face_id'],original_vertex_id=np.arange(len(s.m['V'])),mesh_archive_uv=s.m['uv'],mesh_archive_K=s.m['K'],native_uv=s.uv,native_pixel_id=s.o['pixel_id'],native_depth_mm=s.z0+s.A@s.theta,native_shape=s.o['native_shape'],source_id=np.array(s.id),theta=s.theta,K=s.K,C=s.C)
   if np.max(abs(s.theta))>0:
    dest=R/'local_results'/'derived_HERO'/g/s.id;dest.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest/'B3_DERIVED.npz',V=s.vertices(),F=s.m['F'],original_face_id=s.m['original_face_id'],original_vertex_id=np.arange(len(s.m['V'])),mesh_archive_uv=s.m['uv'],mesh_archive_K=s.m['K'],native_uv=s.uv,native_pixel_id=s.o['pixel_id'],native_depth_mm=s.z0+s.A@s.theta,native_shape=s.o['native_shape'],source_id=np.array(s.id),theta=s.theta,K=s.K,C=s.C)
   exportrows.append(dict(group=g,id=s.id,native_mesh=s.rec['mesh'],native_observations=s.rec['obs'],theta_B3=s.theta.tolist(),geometry_rule='V corrected along original own camera ray; original IDs unchanged'))
  dest=R/'local_results'/(g+'_LAYERS.glb');dest.write_bytes(sc.export(file_type='glb'));save('assets_index/'+g+'_GLB_LAYERS.json',dict(**asset(dest),world_unit='metres via root .001; source vertices mm',layers=layers));(R/'figures'/(g+'_viewer.html')).write_text(viewer('../local_results/'+dest.name,g));print('VIS_DONE',g,len(layers),dest.stat().st_size,flush=True)
 table('metrics/DERIVED_HERO_INDEX.csv',exportrows)
def viewer(path,g):
 return '''<!doctype html><meta charset="utf-8"><title>''' +g+''' native HERO / shared Body</title><style>body{margin:0;background:#ddd;font:13px sans-serif}#ui{position:absolute;left:8px;top:8px;background:#fffe;padding:8px;max-height:90vh;overflow:auto;z-index:2}canvas{display:block}</style><div id="ui"><b>'''+g+''' | Ring-First metric coordinates</b><p>Independent raw/corrected layers; no fusion. Root units: metres.</p><div id="layers">Loading local GLB…</div></div><script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/"}}</script><script type="module">import * as THREE from 'three';import {OrbitControls} from 'three/addons/controls/OrbitControls.js';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';const scene=new THREE.Scene();scene.background=new THREE.Color(0xeeeeee);const camera=new THREE.PerspectiveCamera(40,innerWidth/innerHeight,.00001,10);const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);document.body.appendChild(renderer.domElement);const ctl=new OrbitControls(camera,renderer.domElement);scene.add(new THREE.HemisphereLight(0xffffff,0x888888,2));new GLTFLoader().load('''+json.dumps(path)+''',g=>{scene.add(g.scene);const box=new THREE.Box3().setFromObject(g.scene),center=box.getCenter(new THREE.Vector3()),r=box.getSize(new THREE.Vector3()).length();camera.position.copy(center).add(new THREE.Vector3(r,-r,r*.65));ctl.target.copy(center);document.querySelector('#layers').textContent='';g.scene.traverse(o=>{if(!o.isMesh)return;o.material.side=THREE.DoubleSide;o.visible=o.name==='Ring_CAD'||o.name==='Body_B3'||o.name==='Inferred_CAP_B3'||o.name.startsWith('HERO_B3__');const label=document.createElement('label'),ck=document.createElement('input');ck.type='checkbox';ck.checked=o.visible;ck.onchange=()=>o.visible=ck.checked;label.append(ck,document.createTextNode(o.name));document.querySelector('#layers').append(label,document.createElement('br'));});document.body.dataset.loaded='true';},undefined,e=>document.querySelector('#layers').textContent='Load failed: '+e);function render(){requestAnimationFrame(render);ctl.update();renderer.render(scene,camera)}render();onresize=()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)};</script>'''
if __name__=='__main__':main()
