"""Official ShapeNet construction + strict CPU load. No forward or GT import.
The wrapper preserves the official Lightning checkpoint's `_pipeline.` namespace
without importing its training/database/evaluation implementation.
"""
from common import *
import resource,time,platform,importlib.metadata
sys.path.insert(0,str(R/'runtime/python'));sys.path.insert(0,str(NF))
import torch
from easydict import EasyDict
from pipeline.pipeline import FusionPipeline

FORWARD_CALLS=[]
def deny_forward(frame,event,arg):
    if event=='call'and frame.f_code.co_name in ['forward','training_step','test_step','_evaluate_database']:
        path=frame.f_code.co_filename
        if str(NF)in path or '/torch/nn/'in path:
            FORWARD_CALLS.append(path+':'+frame.f_code.co_name);raise PermissionError('N0_NO_MODEL_FORWARD')

def plain(v):
    if isinstance(v,dict):return {str(k):plain(x)for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [plain(x)for x in v]
    if isinstance(v,(str,int,float,bool))or v is None:return v
    return str(v)

def yaml_plain(v):
    if isinstance(v,dict):
        if 'dictitems'in v:return yaml_plain(v['dictitems'])
        return {k:yaml_plain(x)for k,x in v.items()}
    if isinstance(v,list):return [yaml_plain(x)for x in v]
    # BaseLoader has no object construction: convert scalars only to JSON types.
    if isinstance(v,str):
        try:return json.loads(v)
        except (ValueError,TypeError):return None if v=='null'else v
    return v

def state_contract(model,state):
    expected=model.state_dict();missing=sorted(set(expected)-set(state));extra=sorted(set(state)-set(expected));shapes=[dict(key=k,expected=list(expected[k].shape),actual=list(state[k].shape))for k in expected.keys()&state.keys()if expected[k].shape!=state[k].shape]
    return dict(missing=missing,unexpected=extra,shape_mismatches=shapes,match=not(missing or extra or shapes))

class CheckpointNamespace(torch.nn.Module):
    def __init__(self,pipeline_config):
        super().__init__();self._pipeline=FusionPipeline(pipeline_config)

def main():
    sys.setprofile(deny_forward);start=time.monotonic();torch.set_num_threads(2)
    files=load(R/'config/CHECKPOINT_FILES.json');rows=[];states={};details={};model=None
    import yaml
    for f in files:
        name=f['name'];p=Path(f['path']);assert sha(p)==f['sha256'];config_json=load(p.parents[1]/'config.json');hc=yaml_plain(yaml.load((p.parents[1]/'hparams.yaml').read_text(),Loader=yaml.BaseLoader))['config']
        t0=time.monotonic()
        # The only nondefault allowlisted class is the audited exact EasyDict1.9.
        with torch.serialization.safe_globals([EasyDict]):ckpt=torch.load(p,map_location='cpu',weights_only=True)
        state=ckpt['state_dict'];states[name]=state;checkpoint_config=plain(ckpt['hyper_parameters']['config'])
        expected=plain(config_json['PIPELINE']);actual=checkpoint_config['PIPELINE'];hp=hc['PIPELINE']
        # Device is runtime placement, never an architecture change.
        ec={k:v for k,v in expected.items()if k!='device'};ac={k:v for k,v in actual.items()if k!='device'};hpc={k:v for k,v in hp.items()if k!='device'}
        config_match=ec==ac==hpc
        row=dict(checkpoint=name,role='PRIMARY_CPU_STRICT'if name=='shapenet_noise_005'else 'BACKUP_STATIC_ONLY',sha256=f['sha256'],bytes=f['bytes'],N=config_json['DATABASE']['feature_grid_resolution'],n_features=expected['n_features'],use_count=expected['use_count'],learned_features=expected['n_features']-int(expected['use_count']),n_samples_each_side=expected['FUSION']['n_samples'],count_renderer=expected['use_count_renderer'],H=expected['FUSION']['resy'],W=expected['FUSION']['resx'],sdf_head=expected['RENDERER']['sdf_head'],occupancy_head=expected['RENDERER']['occ_head'],renderer_output_scale_model=expected['RENDERER']['output_scale'],state_tensors=len(state),all_CPU=all(t.device.type=='cpu'for t in state.values()),checkpoint_config_hparams_architecture_match=config_match,strict_loading='NOT_TESTED_STATIC_ONLY',forward_calls=0,load_seconds=time.monotonic()-t0)
        details[name]=dict(config_json=asset(p.parents[1]/'config.json'),hparams_yaml=asset(p.parents[1]/'hparams.yaml'),checkpoint_pipeline_config=actual,state=[dict(key=k,shape=list(v.shape),dtype=str(v.dtype),device=str(v.device))for k,v in state.items()],config_match=config_match)
        if name=='shapenet_noise_005':
            assert config_match,'OFFICIAL_CHECKPOINT_CONFIG_MISMATCH';cfg=EasyDict(config_json['PIPELINE']);cfg.device=torch.device('cpu');model=CheckpointNamespace(cfg).cpu();contract=state_contract(model,state);assert contract['match'],contract
            loaded=model.load_state_dict(state,strict=True);assert not loaded.missing_keys and not loaded.unexpected_keys
            model.eval();row.update(strict_loading='PASS_STRICT_TRUE',model_parameter_N=sum(p.numel()for p in model.parameters()),missing_N=0,unexpected_N=0,mismatched_shape_N=0,architecture_modified=False,CPU_only=all(p.device.type=='cpu'for p in model.parameters()));details[name]['contract']=contract
            # No model forward. Verify exact values were loaded, rather than shapes alone.
            assert all(torch.equal(model.state_dict()[k],v)for k,v in state.items())
        rows.append(row)
    mixed=state_contract(model,states['tanks_and_temples']);assert not mixed['match'],'NEGATIVE_MIXED_CONFIG_NOT_REJECTED'
    checks=dict(official_primary_strict=rows[0]['strict_loading']=='PASS_STRICT_TRUE',exact_loaded_tensor_values=True,wrong_checkpoint_rejected_before_load=not mixed['match'],model_forward_calls=len(FORWARD_CALLS),CUDA_initialized=torch.cuda.is_initialized(),forbidden_GT_training_imports=[n for n in sys.modules if n.startswith(('training.','graphics.','pytorch_lightning'))])
    assert checks['model_forward_calls']==0 and not checks['CUDA_initialized']and not checks['forbidden_GT_training_imports']
    details['negative_mixed_checkpoint']=mixed;details['runtime']=dict(python=platform.python_version(),torch=torch.__version__,torch_compiled_CUDA=torch.version.cuda,CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),nvidia_driver_text=Path('/proc/driver/nvidia/version').read_text()if Path('/proc/driver/nvidia/version').exists()else 'UNAVAILABLE_NO_GPU_QUERY',Lightning='not installed/not imported; official training wrapper intentionally bypassed',graphics='audited dependency only, not installed/imported',max_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,total_seconds=time.monotonic()-start)
    sys.setprofile(None);table('CHECKPOINT_COMPATIBILITY_MATRIX.csv',rows);save('config/CHECKPOINT_COMPATIBILITY_DETAILS.json',details);save('config/MODEL_LOAD_GUARD_RESULTS.json',checks)
    print('OFFICIAL_PRIMARY_STRICT_LOAD_PASS',checks,'RAM_MiB',details['runtime']['max_RSS_MiB'],flush=True)
if __name__=='__main__':main()
