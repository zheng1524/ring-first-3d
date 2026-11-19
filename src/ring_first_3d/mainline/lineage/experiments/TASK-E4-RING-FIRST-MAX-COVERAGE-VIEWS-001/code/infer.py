"""Unchanged official HERO, exact native axial Z, original018 mesher on native lattice.
Unlike018, no depth resizing: native352x640 plus half-pixel Kn and nearest labels.
"""
from geometry_io import *
import torch,copy,gc
F1=OLD/'experiments/surface_fusion_v1';BENCH=F1.parent/'surface_benchmark_v1';MVS=BENCH/'vendor/mvsanywhere_minimal'

def loader():
 ns=dict(sys=sys,json=json,copy=copy,torch=torch,R=F1,BENCH=BENCH,MVS=MVS);extract(F1/'scripts/run_mvs_adapter3.py',['load_official'],ns);ck=F1/'weights/mvsanywhere_hero_full.ckpt';assert sha(ck)=='00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d';model,info=ns['load_official']([352,640]);info.update(checkpoint=asset(ck),official_commit=subprocess.check_output(['git','-C',str(MVS),'rev-parse','HEAD'],text=True).strip(),GT=False,optimizer_steps=0,new_native_depth_interpolation=0);save('provenance/HERO_MODEL.json',info);return model

def meshfn():return extract(OLD/'experiments/ring_first_v1/scripts/common.py',['unproject','depth_mesh'],dict(np=np,cfg=lambda:dict(mesh_max_depth_jump_mm=.75)))['depth_mesh']

def one(model,r,mf):
 root=N/'hero_fit'/r['id'];root.mkdir(parents=True,exist_ok=True);start=time.time();v=r['target'];ss=r['support_views'];rec=dict(id=r['id'],view_id=v['id'],group=r['group'],rank=r['rank'],variant=r['variant'],success=False,reused=False,source_ids=[s['id']for s in ss],target_SHA=v['RGB_SHA256'],source_SHA=[s['RGB_SHA256']for s in ss],source_Mask_SHA=[s['Mask_SHA256']for s in ss],depth_interpolation=0,GT=False)
 try:
  assert v['formal']and v['role']=='FIT'and len(ss)==3 and all(s['formal']and s['role']=='FIT'and s['group']==v['group']for s in ss);C=np.array(v['C']);Cs=np.array([s['C']for s in ss]);d=np.load(v['cache']);ds=[np.load(s['cache'])for s in ss];pm=C.copy();pm[:3,3]/=1000;ps=Cs.copy();ps[:,:3,3]/=1000;k=np.eye(4);k[:3,:3]=v['K'];k[:2,2]+=.5;ks=np.repeat(k[None],3,axis=0);torch.cuda.reset_peak_memory_stats();print('HERO_START',r['id'],flush=True)
  with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):out=model.preprocess_and_run(cur_image=np.array(d['RGB']).copy(),src_image=[np.array(s['RGB']).copy()for s in ds],cur_pose=pm.copy(),src_pose=ps.copy(),cur_intrinsics=k.copy(),src_intrinsics=ks.copy(),depth_range=None,num_refinement_steps=1,target_image_size=[352,640],device='cuda')
  torch.cuda.synchronize();z=np.squeeze(out['depth'].float().cpu().numpy())*1000;assert z.shape==(352,640)and(np.isfinite(z)&(z>0)).any();A=np.diag([1.,352/360,1.]);A[1,2]=.5*352/360-.5;Kn=A@np.array(v['K']);np.savez_compressed(root/'HERO_native.npz',depth_mm=z,K_index_native=Kn,reference_pose_mm=C,source_poses_mm=Cs,reference_view=v['id'],source_views=np.array(rec['source_ids']),unit='mm',depth_definition='camera axial Z',new_inference=True)
  # Pixel-center mapping only labels/RGB; depth values remain byte-exact nativeoutput.
  yy,xx=np.mgrid[:352,:640];uv=np.c_[xx.ravel(),yy.ravel()];p=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@np.array(v['K']).T;p=np.floor(p[:,:2]/p[:,2:]+.5).astype(int);lab=d['labels'][p[:,1],p[:,0]].reshape(352,640);rgb=d['RGB'][p[:,1],p[:,0]].reshape(352,640,3);Image.fromarray(lab).save(root/'NATIVE_LABELS.png');np.savez_compressed(root/'pack_native.npz',depth_mm=z,labels=lab,K=Kn,pose=C,native_source=str(root/'HERO_native.npz'),unit='mm');m=mf(z,lab==1,C,Kn,rgb);m.export(root/'Raw_open_mesh.ply');y,x=np.nonzero((lab==1)&np.isfinite(z)&(z>0));uv=np.c_[x,y];V=np.asarray(m.vertices);F=np.asarray(m.faces);assert len(V)==len(uv);np.savez_compressed(root/'Raw_source_points.npz',XYZ_mm=V,source_uv=uv,original_faces=F,original_point_id=np.arange(len(V)),native_pixel_id=y*640+x,RGB=rgb[y,x]/255.);np.savez_compressed(root/'RAW_NATIVE_MESH.npz',V=V,F=F,original_face_id=np.arange(len(F)),uv=uv,native_pixel_id=y*640+x,K=Kn,T=C);assert np.array_equal(np.load(root/'pack_native.npz')['depth_mm'],z);rec.update(success=True,unit='mm',depth_definition='axialZ',native_shape=list(z.shape),native=str(root/'HERO_native.npz'),pack=str(root/'pack_native.npz'),mesh=str(root/'Raw_open_mesh.ply'),points=str(root/'Raw_source_points.npz'),K=Kn,C=C,peak_GPU_bytes=torch.cuda.max_memory_allocated(),new_inference=True,native_depth_stats_mm=stats(z.ravel()),original_raw_faces=len(F),native_pixels=len(V));del out
 except Exception as e:rec.update(error=repr(e),traceback=traceback.format_exc());print('HERO_FAILURE',r['id'],repr(e),flush=True)
 rec.update(seconds=time.time()-start);save('hero_fit/'+r['id']+'/SOURCE.json',rec);gc.collect();torch.cuda.empty_cache();print('HERO_FINISH',r['id'],rec['success'],round(rec['seconds'],2),flush=True);return rec

def main():
 assert load(N/'STAGE_D_READY.json')['PASS'];checkfreeze('provenance/ALL_CAMERAS_FROZEN_BEFORE_COVERAGE_HERO.json')
 torch.set_num_threads(4);torch.manual_seed(20261115);plans=[]
 for g in GROUPS:
  checkfreeze(planfreeze(g));plans+=load(selpath(g,'_HERO_PLAN.json'))
 mf=meshfn();model=None;records=[];snapshot_read([Path(__file__),P18/'code/infer018.py',F1/'scripts/run_mvs_adapter3.py',OLD/'experiments/ring_first_v1/scripts/common.py'],'HERO_CODE_AND_INTERFACE.json')
 for r in plans:
  p=N/'hero_fit'/r['id']/'SOURCE.json'
  if p.exists():records.append(load(p));continue
  if model is None:model=loader()
  records.append(one(model,r,mf));save('metrics/HERO_INFERENCE_RESULTS.json',records)
 save('metrics/HERO_INFERENCE_RESULTS.json',records);freeze('provenance/NEW_RAW_HERO_FROZEN.json',[N/'hero_fit'/r['id']/'SOURCE.json'for r in records],GT=False,depth_interpolation=0);print('ALL_HERO_DONE',len(records),sum(r['success']for r in records),flush=True)
if __name__=='__main__':main()
