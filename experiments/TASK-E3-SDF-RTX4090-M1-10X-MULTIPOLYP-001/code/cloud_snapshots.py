"""Official extraction from unchanged predecessor states, before remote updates."""
from geometry_monitor import *
import argparse


def main():
    torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    check=[]
    for step in [2000,4000]:
        if (R/f'metrics/single_M1_step{step:06d}_GEOMETRY.json').exists():continue
        path=TASK/'predecessors'/f'G01_004_step{step:06d}.pt'
        state=torch.load(path,map_location='cuda',weights_only=False);model=make_model();model.load_state_dict(state['model'],strict=True)
        assert all(torch.equal(v,state['model'][k])for k,v in model.state_dict().items())
        if step==4000:
            ref=np.load(TASK/'data/CPU_RAW_SDF_REFERENCE.npz');x=torch.as_tensor(ref['x_model'],device='cuda',dtype=torch.float32)
            with torch.no_grad():f=model.implicit_network(x)[:,0].cpu().numpy()*protocol()['geometry']['mm_per_model_unit']
            error=float(abs(f-ref['f_mm']).max());assert error<=2e-4,('RAW_SDF_CPU_GPU_MISMATCH',error)
        else:error=None
        result=geometry_checkpoint(model,'M1',step)
        assert all(torch.equal(v,state['model'][k])for k,v in model.state_dict().items())
        check.append(dict(step=step,faces=result['faces_N'],model_unchanged=True,
            optimizer_updates=0,raw_SDF_CPU_GPU_max_mm=error,field_and_mesh_real=True))
        del model,state;torch.cuda.empty_cache()
    save('metrics/MIGRATION_RESTORE_AND_EXTRACTION.json',dict(checks=check,mode='no optimizer updates',GT=False))
    print('MIGRATION_EXTRACTION',clean(check),flush=True)


if __name__=='__main__':main()
