"""The inherited SGD/rendering loop, with fixed B/C/D changes only."""
from components import *
import argparse
from pytorch3d.io import save_obj

def main():
    ap=argparse.ArgumentParser();ap.add_argument('case',choices=['virtual','real']);ap.add_argument('arm',choices=['B','C','D']);args=ap.parse_args()
    guard_optimizer();reads=[]
    def track(event,aa):
        if event=='open'and isinstance(aa[0],(str,bytes)):
            pp=str(Path(os.fsdecode(aa[0])).resolve())
            if '/depth_observations/'in pp:
                if args.arm!='D':raise PermissionError('NO_DEPTH_IN_B_C')
                reads.append(pp)
    sys.addaudithook(track)
    gate=load(R/'metrics/PREFLIGHT.json');assert gate['passed'];freeze=load(R/'assets_index/PREOPT_FREEZE.json')
    for a in freeze['files']:assert sha(a['path'])==a['sha256'],a['path']
    cfg=load(R/'config/PROTOCOL.json');c=Case(args.case);prior=RelativePrior(c);depth=Depth(c)if args.arm=='D'else None
    torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);out=R/'local_results'/args.case/args.arm;out.mkdir(parents=True,exist_ok=True);assert not(out/'FINAL.npz').exists()
    v0=c.base.verts_packed().detach();F=c.base.faces_packed();global_q=torch.zeros(6,device=device,requires_grad=True);local=torch.zeros_like(v0,requires_grad=True);origin=v0;stage='LOCAL'if args.arm=='B'else'GLOBAL6'
    params=[local]if args.arm=='B'else[global_q];opt=torch.optim.SGD(params,lr=1.,momentum=.9)
    def current():return Meshes(verts=[v0*global_q[3:].exp()+global_q[:3]if stage=='GLOBAL6'else origin+local],faces=[F])
    def snap(step,label=None):
        mm=current();V,ff=c.mm(mm);tag=label or'STEP_%04d'%step
        np.savez_compressed(out/(tag+'.npz'),V=V,F=ff,origin=origin.detach().cpu().numpy(),local=local.detach().cpu().numpy(),global_q=global_q.detach().cpu().numpy(),stage=stage,step=step,center=c.center,scale=c.scale)
        trimesh.Trimesh(V,ff,process=False).export(out/(tag+'_mm.ply'))
        torch.save(dict(step=step,stage=stage,origin=origin.detach().cpu(),local=local.detach().cpu(),global_q=global_q.detach().cpu(),optimizer=opt.state_dict(),numpy_state=np.random.get_state(),torch_state=torch.get_rng_state(),cuda_state=torch.cuda.get_rng_state(),config=cfg),out/(tag+'.pt'))
    snap(0);hist=[];depthhist=[];t0=time.time();status='COMPLETED';steps=0;accepted=0;vlast=v0
    for i in range(300):
        if i==100 and args.arm!='B':
            origin=(v0*global_q[3:].exp()+global_q[:3]).detach();local=torch.zeros_like(v0,requires_grad=True);stage='LOCAL';params=[local];opt=torch.optim.SGD(params,lr=1.,momentum=.9);snap(i,'STAGE2_START');prev=np.load(out/'STEP_0100.npz');assert np.array_equal(prev['V'],c.mm(current())[0])
        tick=time.time();opt.zero_grad();m=current();before=m.verts_packed().detach().clone();pr=prior(m);chosen=np.random.permutation(len(c.fit))[:2];sil=sum(c.loss(m,c.fit[j],'RingAware')for j in chosen)/len(chosen)
        dl=sil*0;dinfos=[]
        if depth:
            depth.begin(m)
            for j in chosen:
                d,inf=depth.loss(m,c.fit[j]);dl+=d/len(chosen);dinfos.append(dict(case=args.case,arm=args.arm,step=i+1,**inf))
        reg=relative_total(pr);total=sil+reg+(.01*dl if depth else 0.);total.backward();gnorm=float(torch.sqrt(sum((p.grad**2).sum()for p in params)));reason=None
        if not torch.isfinite(total)or not all(torch.isfinite(p.grad).all()for p in params):reason='NONFINITE_LOSS_OR_GRADIENT'
        elif gnorm>100.:reason='GRADIENT_NORM_OVER_100'
        if reason:
            status='STOPPED';save('metrics/'+args.case+'_'+args.arm+'_STOP.json',dict(step=i+1,reason=reason,gradient_norm=gnorm,optimizer_steps=steps,accepted_steps=accepted));break
        opt.step();steps+=1;candidate=current().verts_packed().detach();disp=float((candidate-before).norm(dim=1).max())*c.scale
        V,ff=c.mm(current());mm=trimesh.Trimesh(V,ff,process=False);v0vol=trimesh.Trimesh(c.V,c.F,process=False).volume;ratio=float(mm.volume/v0vol)
        if not torch.isfinite(candidate).all():reason='NONFINITE_CANDIDATE'
        elif disp>2.:reason='SINGLE_CANDIDATE_STEP_OVER_2MM'
        elif not(.1<=ratio<=10.):reason='VOLUME_OUTSIDE_EMERGENCY_RANGE'
        if reason:
            status='STOPPED';snap(steps,'UNSAFE_CANDIDATE');np.savez_compressed(out/'LAST_SAFE.npz',V=before.cpu().numpy()*c.scale+c.center,F=c.F)
            save('metrics/'+args.case+'_'+args.arm+'_STOP.json',dict(step=i+1,reason=reason,gradient_norm=gnorm,candidate_step_mm=disp,volume_ratio=ratio,optimizer_steps=steps,accepted_steps=accepted));break
        accepted+=1;vlast=candidate;torch.cuda.synchronize()
        hist.append(dict(case=args.case,arm=args.arm,step=i+1,stage=stage,views=[c.fit[j]for j in chosen],silhouette=float(sil.detach()),depth=float(dl.detach()),total=float(total.detach()),gradient_norm=gnorm,step_max_mm=disp,max_displacement_P0_mm=float((candidate-v0).norm(dim=1).max())*c.scale,volume_mm3=float(mm.volume),volume_ratio_P0=ratio,seconds_per_step=time.time()-tick,elapsed_seconds=time.time()-t0,**{k:float(v.detach())for k,v in pr.items()}));depthhist+=dinfos
        if(i+1)in cfg['checkpoints']:snap(i+1)
        if(i+1)%25==0:print(args.case,args.arm,i+1,stage,'L',hist[-1]['total'],'V',ratio,flush=True)
    if status=='COMPLETED':
        V,ff=c.mm(current());np.savez_compressed(out/'FINAL.npz',V=V,F=ff);trimesh.Trimesh(V,ff,process=False).export(out/'FINAL_mm.ply');save_obj(str(out/'FINAL_normalized.obj'),current().verts_packed(),F,decimal_places=16)
    table('metrics/'+args.case+'_'+args.arm+'_TRAINING.csv',hist);table('metrics/'+args.case+'_'+args.arm+'_DEPTH_TRACE.csv',depthhist)
    save('metrics/'+args.case+'_'+args.arm+'_RUN.json',dict(case=args.case,arm=args.arm,status=status,optimizer_steps=steps,accepted_steps=accepted,elapsed_seconds=time.time()-t0,peak_GPU_bytes=torch.cuda.max_memory_allocated(),depth_observations_read=sorted(set(reads)),GT_mesh_read=False,ideal_depth_exception=args.case=='virtual'and args.arm=='D',stage2_momentum_reset=args.arm!='B',data_or_camera_modified=False,hyperparameter_search=False))
    print('FINISHED',args.case,args.arm,status,steps,flush=True)
if __name__=='__main__':main()
