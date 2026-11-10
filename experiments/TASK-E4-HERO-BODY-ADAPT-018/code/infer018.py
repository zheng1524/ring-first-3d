from common import *
import ast,copy,gc,traceback,subprocess
import torch
F1=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v1');BENCH=F1.parent/'surface_benchmark_v1';MVS=BENCH/'vendor/mvsanywhere_minimal'
def loader():
 ns=dict(sys=sys,json=json,copy=copy,torch=torch,R=F1,BENCH=BENCH,MVS=MVS)
 p=F1/'scripts/run_mvs_adapter3.py';n=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='load_official');exec(compile(ast.Module(body=[n],type_ignores=[]),str(p),'exec'),ns)
 checkpoint=F1/'weights/mvsanywhere_hero_full.ckpt';assert sha(checkpoint)==load(F1/'metrics/official_checkpoint_verification.json')['SHA256']
 wrapper,info=ns['load_official']([352,640]);info.update(checkpoint=asset(checkpoint),loader_source=asset(p),official_commit=subprocess.run(['git','-C',str(MVS),'rev-parse','HEAD'],text=True,capture_output=True).stdout.strip(),local_source_role='unchanged complete official HERO, mm input/output adapter only');save('provenance/HERO_MODEL.json',info);return wrapper,info
def mesher():
 ns=dict(np=np,cfg=lambda:load(R/'config/PROTOCOL.json'));p=F1.parent/'ring_first_v1/scripts/common.py';nodes=[n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in ['unproject','depth_mesh']];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns['depth_mesh']
def main():
 plan=load(R/'config/VIEW_PLAN.json');by={r['view_id']:r for r in plan};model=None;records=[];torch.set_num_threads(4);torch.manual_seed(20261110);meshfn=mesher()
 for r in plan:
  cid=r['view_id'];root=R/('hero_fit'if r['role']=='FIT'else'holdout/hero')/cid;root.mkdir(parents=True,exist_ok=True);record=root/'SOURCE.json'
  if record.exists():records.append(load(record));continue
  t=time.time();rec=dict(group=r['group'],view_id=cid,role=r['role'],success=False,reused=False,GT=False)
  try:
   if r['reuse']:
    a=r['reuse'];mapping={'native_depth':'HERO_native.npz','archive_pack':'pack_full.npz','archive_mesh':'Raw_open_mesh.ply','archive_points':'Raw_source_points.npz'}
    for key,name in mapping.items():
     if key in a:(root/name).symlink_to(Path(a[key]).resolve())
    rec.update(reused=True,parent_RGB=a['upstream_RGB'],native=str(root/'HERO_native.npz'),pack=str(root/'pack_full.npz'),mesh=str(root/'Raw_open_mesh.ply'),points=str(root/'Raw_source_points.npz'),source017_id=cid)
   else:
    if model is None:model,info=loader()
    d=np.load(r['cache']);K=d['K'];T=d['T'];src=[by[x]for x in r['support_views']];assert all(s['role']=='FIT'and s['group']==r['group']for s in src);poses=np.array([np.load(s['cache'])['T']for s in src]);pm=T.copy();pm[:3,3]/=1000;ps=poses.copy();ps[:,:3,3]/=1000;k=np.eye(4);k[:3,:3]=K;k[:2,2]+=.5;ks=[]
    for s in src:
     kk=np.eye(4);kk[:3,:3]=np.load(s['cache'])['K'];kk[:2,2]+=.5;ks.append(kk)
    torch.cuda.reset_peak_memory_stats();print('HERO_BEGIN',cid,r['role'],flush=True)
    with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):out=model.preprocess_and_run(cur_image=np.array(d['RGB']).copy(),src_image=[np.asarray(Image.open(s['meta']['RGB_source']).convert('RGB')).copy()for s in src],cur_pose=pm,src_pose=ps,cur_intrinsics=k.copy(),src_intrinsics=np.array(ks),depth_range=None,num_refinement_steps=1,target_image_size=[352,640],device='cuda')
    torch.cuda.synchronize();native=np.squeeze(out['depth'].float().cpu().numpy())*1000;assert native.shape==(352,640);assert (np.isfinite(native)&(native>0)).any();A=np.diag([1.,352/360,1.]);A[1,2]=.5*352/360-.5;Kn=A@K
    np.savez_compressed(root/'HERO_native.npz',depth_mm=native,K_index_native=Kn,reference_pose_mm=T,source_poses_mm=poses,reference_view=cid,source_views=np.array(r['support_views']),unit='mm',depth_definition='camera axial Z',new_inference=True)
    depth=cv2.resize(native.astype(float),(640,360),interpolation=cv2.INTER_LINEAR);np.savez_compressed(root/'pack_full.npz',depth_mm=depth,labels=d['labels'],K=K,pose=T,native_source=str(root/'HERO_native.npz'),unit='mm');m=meshfn(depth,d['labels']==1,T,K,d['RGB']);m.export(root/'Raw_open_mesh.ply');y,x=np.nonzero((d['labels']==1)&np.isfinite(depth)&(depth>0));uv=np.c_[x,y];assert len(m.vertices)==len(uv);np.savez_compressed(root/'Raw_source_points.npz',XYZ_mm=np.asarray(m.vertices),source_uv=uv,original_faces=np.asarray(m.faces),RGB=d['RGB'][y,x]/255.,original_point_id=np.arange(len(uv)))
    rec.update(native=str(root/'HERO_native.npz'),pack=str(root/'pack_full.npz'),mesh=str(root/'Raw_open_mesh.ply'),points=str(root/'Raw_source_points.npz'),parent_RGB=[dict(view_id=s['view_id'],RGB=s['meta']['RGB_source'],sha256=sha(s['meta']['RGB_source']))for s in src],model_info_path=str(R/'provenance/HERO_MODEL.json'),peak_GPU_bytes=torch.cuda.max_memory_allocated());del out;gc.collect();torch.cuda.empty_cache()
   rec.update(success=True,seconds=time.time()-t,assets={k:asset(rec[k])for k in ['native','pack','mesh','points']if Path(rec[k]).exists()})
  except Exception:rec.update(failure=traceback.format_exc(),seconds=time.time()-t);print(rec['failure'],flush=True);gc.collect();torch.cuda.empty_cache()
  record.write_text(json.dumps(clean(rec),ensure_ascii=False,indent=2)+'\n');records.append(rec);save('metrics/HERO_INFERENCE_RESULTS.json',records);print('HERO_DONE',cid,rec['success'],'reuse',rec['reused'],'sec',round(rec['seconds'],2),flush=True)
 save('metrics/HERO_INFERENCE_RESULTS.json',records)
if __name__=='__main__':main()
