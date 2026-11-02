"""CPU shape/reset schema and adversarial coordinate controls, no NN forward."""
from crop import *
import resource
sys.path.insert(0,str(NF));import torch
from pipeline.utils import unproject as official_unproject

def main():
    tests=[]
    def add(name,ok,detail):tests.append(dict(test=name,status='PASS'if bool(ok)else 'FAIL',detail=detail))
    proto=config();metric=load(R/'METRIC_TRANSFORM.json');domain=metric['domains']['ALL_INPUTS'];L=domain['L_mm'];O=np.asarray(domain['O_mm']);N=128
    # Empty storage contract only: never passed to FusionPipeline, Integrator or Translator.
    volume=torch.zeros((N,N,N,17),dtype=torch.float32,device='cpu');count=torch.zeros((N,N,N),dtype=torch.float32,device='cpu')
    add('EMPTY_LATENT_COUNT_RESET',volume.shape==(128,128,128,17)and count.shape==(128,128,128)and not torch.count_nonzero(volume)and not torch.count_nonzero(count),dict(axis_order='XYZ,feature; last feature=count for ShapeNet use_count=True',storage_bytes=(volume.numel()+count.numel())*4,model_field_inferred=False))
    schema=[]
    for cid in IDS:
        s=native(cid);c=np.load(R/'local_results/crops'/(cid+'.npz'));T=s['T'].copy();T[:3,3]=(T[:3,3]-O)/L;depth=c['depth_mm'].astype(float)/L;valid=c['valid'];K=c['K_crop'];rgb=s['native_RGB'];labels=s['native_labels'];uv=s['native_uv'];z=s['depth'][uv[:,1],uv[:,0]].astype(float)
        # Official pure unprojection, not the neural pipeline or any forward method.
        gp=official_unproject(torch.tensor(depth[None],dtype=torch.float64),torch.tensor(T[None],dtype=torch.float64),torch.tensor(K[None],dtype=torch.float64),torch.zeros((1,1,3),dtype=torch.float64),1/N,torch.device('cpu')).numpy().reshape(240,320,3)
        world=gp[valid]/N*L+O;err=np.linalg.norm(world-c['output_X_mm'],axis=1)
        add(cid+'_OFFICIAL_GEOMETRY_ONLY',err.max()<=proto['thresholds']['analytic_XYZ_max_mm'],dict(points_N=len(err),maximum_mm=float(err.max()),field='ALL_INPUTS diagnostic candidate only; no active model domain',network_forward=0))
        add(cid+'_FIVE_MASK_CLASSES',np.all(c['depth_mm'][c['semantics']!=1]==0)and np.isfinite(c['depth_mm']).all()and np.all(c['source_ids'][c['semantics']==4]==-1),dict(semantic_counts={str(k):int((c['semantics']==k).sum())for k in range(5)}))
        add(cid+'_THIN_STRUCTURE_GATE',not np.any(ridge_proxy(valid)[1]&(2*ridge_proxy(valid)[0]<3)),dict(minimum_required_output_px=3,source=cid,uncalibrated_anatomy_proxy=True))
        add(cid+'_CAMERA_AND_SOURCE_SHA',all(sha(a['path'])==a['sha256']for a in next(r for r in MANIFEST['sources']if r['source_id']==cid)['assets'].values()),dict(source_pixel_denominator=len(uv),camera_updates=0))
        schema.append(dict(source=cid,status='SCHEMA_ONLY_NO_ACTIVE_DOMAIN',fields=dict(input=dict(shape=[1,240,320],dtype='float32',unit='model axialZ=mm/L',invalid=0),original_mask=dict(shape=[1,240,320],dtype='float32 binary'),intrinsics=dict(shape=[1,3,3],dtype='float32',value='crop K'),extrinsics=dict(shape=[1,4,4],dtype='float32',direction='c2w',translation='(C_mm-O_mm)/L_mm'),origin=dict(shape=[1,1,3],value=[0,0,0]),resolution=1/128,volume=dict(shape=[128,128,128,17],dtype='float32',reset='all0'),count=dict(shape=[128,128,128],dtype='float32',reset='all0')),device='CPU',ShapeNet_count_channel='volume[...,16]; external count also initialized0',primary_reset_per_sequence=True,forwards_performed=0))
    s=native(IDS[0]);u,v=s['native_uv'][0];labels=s['native_labels'];rgb=s['native_RGB'];original=s['depth'];neg=[]
    for value,label,name in [(float('nan'),1,'NaN'),(0.,1,'zero'),(-1.,1,'negative'),(10.,2,'Ring'),(10.,0,'Background')]:
        d=original.copy();l=labels.copy();d[v,u]=value;l[v,u]=label;a=HEROToTSDFAdapter(d,rgb,l,s['Kn'],s['T'],100.)
        ok=not a.valid[v,u]and a.depth_m[v,u]==0;add('NEGATIVE_INVALID_'+name,ok,dict(expected='explicit invalid=0',input_was_copy=True))
    ids=np.unique(np.linspace(0,len(s['native_uv'])-1,1000,dtype=int));uv=s['native_uv'][ids];z=s['depth'][uv[:,1],uv[:,0]].astype(float);X=s['X'][ids]
    for name,T,depth,K in [('WRONG_W2C',np.linalg.inv(s['T']),z,s['Kn']),('WRONG_1000_DEPTH',s['T'],z*1000,s['Kn']),('ARCHIVED_K_ON_NATIVE',s['T'],z,s['K'])]:
        wrong=unproject(depth,T,uv,K);e=np.linalg.norm(wrong-X,axis=1);add('NEGATIVE_'+name,e.max()>proto['thresholds']['analytic_XYZ_max_mm'],dict(status='ERROR_DETECTED_NOT_ACCEPTED',same_original_pixel_ids=True,median_error_mm=float(np.median(e)),maximum_error_mm=float(e.max())))
    c=np.load(R/'local_results/crops'/(IDS[0]+'.npz'));wrongK=c['K_crop'].copy();wrongK[:2,2]+=1;u2=c['output_uv'];z2=c['depth_mm'][u2[:,1],u2[:,0]];e=np.linalg.norm(unproject(z2.astype(float),s['T'],u2,wrongK)-c['output_X_mm'],axis=1);add('NEGATIVE_ONE_PIXEL_PRINCIPAL_POINT',e.max()>1e-5,dict(maximum_error_mm=float(e.max()),accepted=False))
    # Real observed55 points are not clipped into a smaller grid.
    stop=load(R/'config/METRIC_STOP.json');add('OUT_OF_GRID_STOP_RECORDED',stop['stop_requires_researcher']and stop['diagnostic_OUT_OF_GRID_total']==55 and stop['active_model_domain']is None,dict(points_retained=True,formal_domain_frozen=False));add('FORMAL_METRIC_DOMAIN_READY',False,dict(status='REQUEST_RESEARCHER_ROI_DECISION',reason='all-input coarse domain vs55 out-of-grid observations in diagnostic domain'))
    x=load(R/'config/CROSS_VIEW_GATE.json');add('ALL24_DIRECTED_INVARIANCE',x['all_analytic_pass'],x)
    add('NO_CUDA_INITIALIZED',not torch.cuda.is_initialized(),dict(device='CPU',GPU_operations=0));add('NO_GT_TRAINING_DATABASE_IMPORT',not any(n.startswith(('training.','graphics.','pytorch_lightning'))for n in sys.modules),dict(forbidden_imports=[]))
    # Test runtime guards without touching or creating a real GT file.
    for name,fn in [('GT_READ',lambda:open('/home/liu/private_gt/DO_NOT_CREATE.txt')),('TRAINING_IMPORT',lambda:__import__('training.database')),('HISTORY_WRITE',lambda:open('/home/liu/ring_first_3d_e3d0/N0_DO_NOT_CREATE.txt','w'))]:
        try:fn();blocked=False
        except PermissionError:blocked=True
        add('GUARD_'+name,blocked,dict(expected='PermissionError before filesystem access'))
    add('EMPTY_FIELDS_STILL_ZERO',not torch.count_nonzero(volume)and not torch.count_nonzero(count),dict(validity_checks_did_not_integrate=True))
    del gp,volume,count
    model=load(R/'config/MODEL_LOAD_GUARD_RESULTS.json');add('PRIMARY_STRICT_COMPATIBILITY',model['official_primary_strict']and model['exact_loaded_tensor_values']and model['model_forward_calls']==0,model)
    table('CONTRACT_TEST_RESULTS.csv',tests);save('config/CONTRACT_TEST_RESULTS.json',dict(tests=tests,PASS=sum(t['status']=='PASS'for t in tests),FAIL=sum(t['status']=='FAIL'for t in tests),max_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,GT=False,neural_forward=0,GPU=0));save('INFERENCE_ONLY_SCHEMA.json',dict(status='INTERFACE_ONLY_NOT_FUSION_AUTHORIZATION',active_metric_domain=None,candidate_domain_used_only_for_shape_and_unprojection='ALL_INPUTS',sources=schema,GT_database_allowed=False,Translator_on_unknown='NOT_TESTED_GATE_B_ONLY',reset_contract='new all0 latent,count per source-prefix sequence; never reuse prior sequence',F0_F5='NOT_RUN'))
    save('config/GEOMETRY_RUNTIME_ACCESS.json',dict(external_files=sorted(ACCESSED),expected_guard_denials=DENIALS))
    print('CONTRACTS',sum(t['status']=='PASS'for t in tests),'PASS',sum(t['status']=='FAIL'for t in tests),'FAIL_RETAINED',flush=True)
if __name__=='__main__':main()
