"""Canonical E2.6 CPU initialization -> FP32 device port; official MLP unchanged."""
from common import *
def forbid_gpu(*args,**kwargs):raise RuntimeError('CPU_CANONICAL_CONSTRUCTOR_ONLY')
ns=extract(E25/'code/official_sdf_cpu_adapter.py',['model_config','construct_official'],dict(globals()))

def canonical_model():
    c=cfg();torch.random.default_generator.manual_seed(c['seed'])
    conf=ns['model_config'](domain(),'B_SOURCE_ROI_PHYSICAL',c);conf['implicit_network']['bias']=c['initialization']['bias_network']
    original=torch.Tensor.cuda
    try:model,ports=ns['construct_official'](conf)
    finally:torch.Tensor.cuda=original
    actual=parameter_hash(model);assert actual==c['initialization']['model_parameter_SHA256'],actual
    assert actual=='7b5b64e57523d72ededf4c27f2314dd84776066f66197056c44bf014b2b3c81c'
    return model,ports

def move(model,device,dtype=torch.float32):
    model=model.to(device=device,dtype=dtype)
    # Two official tensors are ordinary attributes, not registered buffers.
    model.bg_color=model.bg_color.to(device=device,dtype=dtype)
    model.density.beta_min=model.density.beta_min.to(device=device,dtype=dtype)
    assert all(p.device==torch.device(device) for p in model.parameters())
    return model

def initialized_model(device='cpu'):
    model,ports=canonical_model();sha64=parameter_hash(model);model=move(model,device)
    return model,dict(canonical_SHA256=sha64,FP32_SHA256=parameter_hash(model),constructor_CPU_ports=ports,
        canonical_device='cpu',target_device=device,random_initialization_on_GPU=False)

def checkpoint(model,arm,step,kind='scheduled'):
    folder=R/'checkpoints'/arm;folder.mkdir(exist_ok=True,parents=True);path=folder/(f'step{step:03d}.pt' if kind=='scheduled' else f'{kind}_step{step:03d}.pt')
    state={k:v.detach().cpu().contiguous().clone() for k,v in model.state_dict().items()};torch.save(state,path)
    record=dict(arm=arm,step=step,kind=kind,path=str(path.relative_to(R)),file_SHA256=sha(path),parameter_SHA256=parameter_hash(model),bytes=path.stat().st_size,state_dict_only=True)
    records=load(R/'provenance/CHECKPOINT_HASHES.json') if (R/'provenance/CHECKPOINT_HASHES.json').exists() else []
    records=[r for r in records if r['path']!=record['path']]+[record];save('provenance/CHECKPOINT_HASHES.json',records)
    return record

def load_checkpoint(path,device='cuda:0'):
    model,_=initialized_model('cpu');model.load_state_dict(torch.load(R/path,map_location='cpu',weights_only=True));return move(model,device)

def save_initial():
    model,ports=canonical_model();path=R/'checkpoints/INITIAL_CANONICAL.pt';torch.save({k:v.detach().cpu().clone() for k,v in model.state_dict().items()},path)
    fp32=move(model,'cpu');save('provenance/INITIAL_MODEL.json',dict(canonical_SHA256=cfg()['initialization']['model_parameter_SHA256'],FP32_SHA256=parameter_hash(fp32),
        path=str(path.relative_to(R)),file_SHA256=sha(path),constructor_CPU_ports=ports,official_revision=git(SDF,'rev-parse','HEAD'),
        official_network_SHA256=sha(SDF/'code/model/network.py'),preexisting_lazy_hashencoder_import_port=True,new_upstream_edits=False))
    return fp32
