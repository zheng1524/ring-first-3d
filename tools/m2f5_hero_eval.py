#!/usr/bin/env python3
"""M2F5: HERO, Raw metric mesh, B-camera A-to-B and six-view for fresh 13-group selections."""
import sys,json,pathlib,hashlib,time
import numpy as np,pandas as pd
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f5_unified'
sys.path[:0]=[str(WS/'src'),str(WS/'src/ring_first_3d/mainline/frozen_registry'),str(WS/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code')]
from ring_first_3d.mainline.input_identity import verify_w0_packet
from ring_first_3d.mainline.native.hero import load_official,infer
from ring_first_3d.mainline.native.geometry import native_rgb_labels
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
import reprojection as rp, open3d as o3d
from matplotlib import pyplot as plt
from matplotlib import colors

def write_json(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=1,default=str)+'\n')
def trace(g,v,stage,route,entry,inputs,outputs,status,extra=None):
 p=O/'RUN_TRACE'/f'{g}_{v}.jsonl';p.parent.mkdir(parents=True,exist_ok=True);rec=dict(run_id='M2F5-UNIFIED-001',group_id=g,video_id=v,stage=stage,route_id=route,route_version='1',entrypoint=entry,inputs=inputs,outputs=outputs,status=status,code_commit=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=WS,text=True).strip(),config_hash=hashlib.sha256((WS/'mainline/configs/SITE.local.json').read_bytes()).hexdigest());
 if extra:rec.update(extra)
 with p.open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')
def load_clean(g,v,vid):
 return np.load(O/'clean_labels'/f'{g}_{v}'/(vid+'.npz'))['labels']
def frames(packet,target,supports):
 out=[]
 for vid in [target]+supports:
  e=packet['views'][vid];z=np.load(e['cache']);out.append(dict(id=vid,RGB=z['RGB'],labels=load_clean(packet['group'],packet['video'],vid),K=np.asarray(z['K'],float),c2w_mm=packet['cameras'][vid]))
 return out
def scene(kind):
 d=dict(np.load(O/'cad'/f'{kind}.npz'));s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(d['V'].astype(np.float32)),o3d.core.Tensor(d['F'].astype(np.uint32)));return s
rp.cad_scene=scene

def main():
 # selection tables
 sels=sorted((O/'selection').glob('*.csv'));rows=[]
 for f in sels:
  d=pd.read_csv(f);rows.extend(d[d.ready==True].to_dict('records'))
 uni=[];seen=set()
 for r in rows:
  key=(r['group_id'],r['video_id'],r['target_id'],r['support_ids'])
  if key not in seen:seen.add(key);uni.append(r)
 print('ready rows',len(rows),'unique',len(uni),flush=True)
 model=None;cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text());sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
 model,receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text()));write_json(O/'hero/MODEL_RECEIPT.json',receipt)
 hero=[];a2b=[]
 for n,r in enumerate(uni,1):
  g,v,target=str(r['group_id']),f"{int(r['video_id']):03d}",str(r['target_id']);sups=str(r['support_ids']).split(';');packet=verify_w0_packet(O/'w0'/f'{g}_{v}',WS);out=O/'hero'/g/v/target;out.mkdir(parents=True,exist_ok=True)
  try:
   if not (out/'HERO_native.npz').exists():
    rec=infer(model,frames(packet,target,sups),out);status='PASS'
   else:rec=json.loads((out/'INFERENCE.json').read_text());status='REUSED'
   hero.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(sups),status=status,output_dir=str(out),seconds=rec.get('seconds'),raw_faces=rec.get('raw_faces'),tuple_sha=hashlib.sha256((g+'|'+v+'|'+target+'|'+';'.join(sups)).encode()).hexdigest()[:16]))
   trace(g,v,'hero','rf-m2f5-hero-native','native/hero.py::infer',[str(O/'clean_labels'/g_v) for g_v in []],[str(out)],status,{'target':target,'supports':sups})
  except Exception as e:
   hero.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(sups),status='FAIL',error=repr(e),output_dir=str(out)));print('HEROFAIL',g,v,target,e,flush=True);continue
  # A2B against all supports
  raw=np.load(out/'RAW_NATIVE_MESH.npz');V=raw['V'];F=raw['F'];ta=np.load(packet['views'][target]['cache']);K=np.asarray(ta['K'],float);rn,_,_=native_rgb_labels(ta['RGB'],ta['labels'],K);Cv=rn[raw['uv'][:,1],raw['uv'][:,0]]/255.
  for B in sups:
   b=np.load(packet['views'][B]['cache']);BK=np.asarray(b['K'],float);Bpose=packet['cameras'][B];pred=rp.render(V,F,Cv,BK,Bpose,np.eye(4),'R5' if '_R5_' in g else 'R10');met,mae,common=rp.evaluate(pred,np.asarray(b['RGB']),load_clean(g,v,B));met.update(group_id=g,video_id=v,target_id=target,support_id=B,target_B_camera_used=True,source_mesh=str(out/'RAW_NATIVE_MESH.npz'),status='GATED_NEW_HERO');a2b.append(met)
  print('HERO',n,'/',len(uni),g,v,'pairs',len(a2b),flush=True)
 pd.DataFrame(hero).to_csv(O/'hero/HERO_EXECUTION_RESULTS.csv',index=False);pd.DataFrame(a2b).to_csv(O/'evaluation/A_TO_B_METRICS.csv',index=False)
 # six view per actual hero; fixed group bounds; all surfaces
 cad=np.load(O/'cad'/('R5.npz' if '_R5_' in g else 'R10.npz'))
 for g in sorted(set(x['group_id'] for x in hero if x['status']!='FAIL')):
  for v in sorted(set(x['video_id'] for x in hero if x['group_id']==g and x['status']!='FAIL')):
   hs=[x for x in hero if x['group_id']==g and x['video_id']==v and x['status']!='FAIL'];V0=[]
   for x in hs:
    try:V0.append(np.load(pathlib.Path(x['output_dir'])/'RAW_NATIVE_MESH.npz')['V'])
    except:pass
   if not V0:continue
   Vall=np.concatenate(V0,0);packet=verify_w0_packet(O/'w0'/f'{g}_{v}',WS)
   for x in hs:
    try:
     raw=np.load(pathlib.Path(x['output_dir'])/'RAW_NATIVE_MESH.npz');V=raw['V'];F=raw['F'];target=x['target_id'];sups=x['support_ids'].split(';');center=V.mean(0);views=[]
     C=packet['cameras'][target];d=C[:3,3]-center;d/=np.linalg.norm(d);views.append(('target',np.degrees(np.arcsin(d[2])),np.degrees(np.arctan2(d[1],d[0]))))
     for k,B in enumerate(sups[:2]):
      C=packet['cameras'][B];d=C[:3,3]-center;d/=np.linalg.norm(d);views.append((f'support{k+1}',np.degrees(np.arcsin(d[2])),np.degrees(np.arctan2(d[1],d[0]))))
     views += [('X',0,0),('Y',0,90),('Z',89.9999,0)]
     fig,ax=plt.subplots(1,6,figsize=(15,3))
     for k,(name,e,a) in enumerate(views):im,_=actual_mesh_image(V,F,cad['V'],cad['F'],Vall,e,a,'#d98989');ax[k].imshow(im);ax[k].set_title(name,fontsize=8);ax[k].axis('off')
     fig.suptitle(f'{g}/{v}/{target} | raw metric mesh | black Ring CAD');fig.tight_layout();p=O/'visualization/six_views'/f'{g}_{v}_{x["tuple_sha"]}.png';p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=90);plt.close(fig);trace(g,v,'six_view','rf-m2f5-six-view','_mesh_renderer.py::actual_mesh_image',[x['output_dir']],[str(p)],'PASS')
    except Exception as e:print('SIXFAIL',g,v,x['target_id'],e,flush=True)
   # multisurface contact
   if len(hs)>1:
    Vs=[];Fs=[];cols=[];pal=[(.86,.36,.36),(.25,.55,.82),(.28,.72,.45),(.86,.67,.15),(.55,.35,.75),(.15,.75,.75),(.8,.4,.7),(.5,.5,.2)]
    for k,x in enumerate(hs):
     d=np.load(pathlib.Path(x['output_dir'])/'RAW_NATIVE_MESH.npz');off=sum(len(q) for q in Vs);Vs.append(d['V']);Fs.append(d['F']+off);cols.append(np.tile(pal[k%len(pal)],(len(d['F']),1)))
    Vc=np.concatenate(Vs);Fc=np.concatenate(Fs);fc=np.concatenate(cols);fig,ax=plt.subplots(1,3,figsize=(12,4))
    for k,(name,e,a) in enumerate([('real',20,-60),('X',0,0),('Z',89.9999,0)]):
     im,_=actual_mesh_image(Vc,Fc,cad['V'],cad['F'],Vall,e,a,'#d98989',face_colors=fc);ax[k].imshow(im);ax[k].set_title(name);ax[k].axis('off')
    fig.suptitle(f'{g}/{v} | {len(hs)} HERO surfaces');fig.tight_layout();p=O/'visualization/multisurface'/f'{g}_{v}.png';p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=90);plt.close(fig)
 print('DONE hero',len(hero),'a2b',len(a2b))
if __name__=='__main__':main()
