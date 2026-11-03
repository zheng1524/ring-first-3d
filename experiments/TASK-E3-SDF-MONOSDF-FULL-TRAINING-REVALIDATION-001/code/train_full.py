"""Single-reference full schedule using the official MonoSDF runner update loop.

Only runner IO, one-device setup, exact step count, telemetry and resume are ported.
Geometry quality never stops a primary run. Nonfinite/hardware failures are recorded.
"""
import argparse, random, traceback, signal, gc
import official_adapter as adapter
from official_adapter import *
from geometry_monitor import geometry_checkpoint


def atomic_json(relative, value):
    target = R/relative
    temporary = target.with_suffix(target.suffix+'.tmp')
    temporary.write_text(json.dumps(clean(value), ensure_ascii=False, indent=2)+'\n')
    os.replace(temporary, target)


def port_official_run():
    source = R/'runtime/official_exact/code/training/monosdf_train.py'
    text = source.read_text(); tree = ast.parse(text)
    cls = next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MonoSDFTrainRunner')
    node = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    original = ast.get_source_segment(text,node)
    run = original.replace('self.iter_step = 0','self.iter_step = self.resume_step',1)
    run = run.replace('self.scheduler.step()',
        'self.scheduler.step()\n                del model_outputs, loss_output, loss, psnr\n                self.after_update()',1)
    assert run != original
    # Genuine original zero_grad -> model -> loss -> backward -> step block is unchanged.
    block='''                self.optimizer.zero_grad()
                
                model_outputs = self.model(model_input, indices)
                
                loss_output = self.loss(model_outputs, ground_truth)
                loss = loss_output['loss']
                loss.backward()
                self.optimizer.step()'''
    assert block in original and block in run
    (R/'provenance/OFFICIAL_RUNNER_PORT.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True),run.splitlines(True),fromfile='official/MonoSDFTrainRunner.run',tofile='adapted/MonoSDFTrainRunner.run')))
    scope=dict(torch=torch,rend_util=rend_util)
    exec(compile(run,str(source),'exec'),scope)
    return scope['run']


class FrozenDataset:
    def change_sampling_idx(self, count):
        assert count==1024


class FrozenLoader:
    def __init__(self, runner): self.runner=runner
    def __iter__(self):
        step=self.runner.iter_step+1
        data,batch=packet(SOURCES[0],step,N=1024)
        yield torch.tensor([0],device='cuda'),data,batch
    def __len__(self): return 1


class OfficialModelIO:
    def __init__(self, runner): self.runner=runner
    def __call__(self, data, indices):
        runner=self.runner; batch=runner.current_batch
        adapter.model_for_loss=runner.network; adapter.current_input=data
        runner.network._visibility_bounds=(batch['near'],batch['far'])
        return runner.network(data,indices)


class OfficialLossIO:
    def __init__(self, runner): self.runner=runner
    def __call__(self, out, batch):
        terms=self.runner.project_loss(out,batch)
        assert torch.isfinite(terms['loss']), 'NONFINITE_LOSS'
        self.runner.last_terms={k:float(v.detach())for k,v in terms.items()}
        sdf=out['sdf']; crossing=(sdf[:,:-1]>0)&(sdf[:,1:]<=0)
        self.runner.last_terms.update(minibatch_front_hit_fraction=float(crossing.any(1).float().mean().detach()),
            minibatch_opacity_mean=float(out['weights'].sum(1).mean().detach()),
            sample_N=out['z_vals'].shape[1])
        assert (out['z_vals']>=batch['near']-1e-5).all()and(out['z_vals']<=batch['far']+1e-5).all(), 'VISIBILITY_INTERVAL_VIOLATION'
        return terms


class BoundLoader(FrozenLoader):
    def __iter__(self):
        for indices,data,batch in super().__iter__():
            self.runner.current_batch=batch
            yield indices,data,batch


class FullRunner:
    run=port_official_run()
    def __init__(self,arm,resume=False):
        self.arm=arm; self.key='single_'+arm
        self.GPU_INDEX=1  # skip distributed-only writer/plots; use task-local single-device hooks
        self.do_vis=False; self.num_pixels=1024
        self.resume_step=0; self.start_epoch=0; self.nepochs=200000-1
        self.network=make_model(); self.project_loss=ProjectLoss(arm)
        self.optimizer=torch.optim.Adam(self.network.parameters(),lr=5e-4,betas=(.9,.999),eps=1e-8)
        self.scheduler=torch.optim.lr_scheduler.LambdaLR(self.optimizer,
            lambda epoch:min(1.,(epoch+1)/1000)*.1**((epoch+1)/200000))
        self.train_dataset=FrozenDataset(); self.train_dataloader=BoundLoader(self)
        self.model=OfficialModelIO(self); self.loss=OfficialLossIO(self)
        self.events=instrument(self.network); self.current_batch=None; self.last_terms={}
        self.started=time.monotonic(); self.last_clock=self.started
        self.output=R/'checkpoints'/self.key; self.output.mkdir(exist_ok=True)
        self.log=R/'metrics'/f'{self.key}_TRAINING.csv'
        self.freeze=load(R/'provenance/BEFORE_FORMAL_TRAINING.json')
        assert self.freeze['training_authorization']['stages']==['single']
        for a in self.freeze['code']: assert sha(a['path'])==a['sha256'], 'FROZEN_CODE_CHANGED'
        for a in load(R/'provenance/INPUT_FREEZE.json')['files']: assert sha(a['path'])==a['sha256']
        latest=self.output/'latest.pt'
        if resume:
            assert latest.exists(), 'NO_CHECKPOINT_TO_RESUME'
            index=load(self.output/'LATEST.json'); assert sha(latest)==index['sha256']
            state=torch.load(latest,map_location='cuda',weights_only=False)
            self.network.load_state_dict(state['model'],strict=True)
            self.optimizer.load_state_dict(state['optimizer']); self.scheduler.load_state_dict(state['scheduler'])
            self.resume_step=int(state['step']); self.start_epoch=self.resume_step
            self.project_loss.step=int(state['loss_step'])
            torch.set_rng_state(state['torch_rng'].cpu()); torch.cuda.set_rng_state(state['cuda_rng'].cpu())
            random.setstate(state['python_rng']); np.random.set_state(state['numpy_rng'])
        else:
            assert not latest.exists() and not self.log.exists(), 'DO_NOT_OVERWRITE_FORMAL_RUN'
        self.optimizer.register_step_pre_hook(self.check_gradients)
        self.checkpoint_steps=set(protocol()['checkpoint_steps'])

    def check_gradients(self,opt,args,kwargs):
        values=[torch.isfinite(p.grad).all() for p in self.network.parameters() if p.grad is not None]
        assert values and torch.stack(values).all(), 'NONFINITE_GRADIENT'
        # No clipping: diagnostics cannot silently modify updates.
        if (self.iter_step+1)%100==0 or self.iter_step<10:
            self.last_terms['gradient_L2']=float(torch.sqrt(sum((p.grad.detach()**2).sum()for p in self.network.parameters()if p.grad is not None)))

    def save_checkpoint(self,step,permanent=False):
        state=dict(step=step,model=self.network.state_dict(),optimizer=self.optimizer.state_dict(),
            scheduler=self.scheduler.state_dict(),loss_step=self.project_loss.step,
            torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state(),
            python_rng=random.getstate(),numpy_rng=np.random.get_state(),arm=self.arm,
            stage='single',input_freeze=load(R/'provenance/INPUT_FREEZE.json'),
            code_freeze_sha256=sha(R/'provenance/BEFORE_FORMAL_TRAINING.json'))
        tmp=self.output/'latest.tmp'; torch.save(state,tmp); os.replace(tmp,self.output/'latest.pt')
        info=dict(step=step,arm=self.arm,**asset(self.output/'latest.pt'))
        atomic_json(f'checkpoints/{self.key}/LATEST.json',info)
        if permanent:
            target=self.output/f'step{step:06d}.pt'
            assert not target.exists(), 'DO_NOT_OVERWRITE_HISTORICAL_CHECKPOINT'
            import shutil
            shutil.copy2(self.output/'latest.pt',target)
            save(f'checkpoints/{self.key}/step{step:06d}.json',dict(step=step,**asset(target)))
            index_path=R/f'metrics/{self.key}_CHECKPOINT_INDEX.json'
            entries=load(index_path)['files']if index_path.exists()else[]
            entries.append(dict(step=step,**asset(target)))
            atomic_json(f'metrics/{self.key}_CHECKPOINT_INDEX.json',dict(local_only=True,files=entries))

    def after_update(self):
        step=self.iter_step
        assert step<=200000
        if step<=10 or step%100==0:
            now=time.monotonic()
            row=dict(step=step,arm=self.arm,stage='single',source=SOURCES[0],formal=True,
                **self.last_terms,lr_used=5e-4*min(1.,step/1000)*.1**(step/200000),
                beta_mm=float(self.network.density.get_beta().detach())*protocol()['geometry']['mm_per_model_unit'],
                session_wall_seconds=now-self.started,session_last_log_seconds=now-self.last_clock,
                peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20)
            # Fixed column order also accommodates terms absent from an M0 arm.
            columns=['step','arm','stage','source','formal','loss','base','rgb','SSI_depth','normal_l1',
                'normal_cos','eikonal','smooth','surface','first_depth','free_space','positive_mask',
                'minibatch_front_hit_fraction','minibatch_opacity_mean','sample_N','gradient_L2',
                'lr_used','beta_mm','session_wall_seconds','session_last_log_seconds','peak_allocated_MiB']
            fresh=not self.log.exists()
            with self.log.open('a',newline='')as f:
                writer=csv.DictWriter(f,fieldnames=columns); writer.writeheader()if fresh else None
                writer.writerow(clean(row));f.flush();os.fsync(f.fileno())
            self.last_clock=now
            atomic_json(f'metrics/{self.key}_STATUS.json',dict(status='RUNNING',step=step,planned_updates=200000,
                official_chain_calls=self.events,latest=row,scientific_acceptance='NOT_YET_EVALUABLE'))
            print('FORMAL_UPDATE',self.key,step,'loss',round(row['loss'],6),'beta_mm',round(row['beta_mm'],6),flush=True)
        if step in self.checkpoint_steps or step%1000==0:
            free=os.statvfs(R)
            assert free.f_bavail*free.f_frsize>1024**3, 'HARDWARE_LOW_DISK_LESS_THAN_1GiB'
            self.save_checkpoint(step,permanent=step in self.checkpoint_steps)
        if step in self.checkpoint_steps:
            self.current_batch=None; self.optimizer.zero_grad(set_to_none=True);gc.collect();torch.cuda.empty_cache()
            result=geometry_checkpoint(self.network,self.arm,step,final=step==200000)
            print('GEOMETRY_CHECKPOINT',self.key,step,'faces',result['faces_N'],'negative_mm3',round(result['negative_grid_volume_mm3'],3),flush=True)
            # Evaluation must not alter training RNG sequence.
            saved=torch.load(self.output/'latest.pt',map_location='cpu',weights_only=False)
            torch.set_rng_state(saved['torch_rng']);torch.cuda.set_rng_state(saved['cuda_rng'])
            random.setstate(saved['python_rng']);np.random.set_state(saved['numpy_rng']);del saved
            torch.cuda.empty_cache()


def main(arm,resume=False):
    torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.cuda.reset_peak_memory_stats();runner=None
    try:
        runner=FullRunner(arm,resume=resume)
        if not resume:
            runner.iter_step=0;runner.save_checkpoint(0,permanent=True)
            result=geometry_checkpoint(runner.network,arm,0)
            print('INITIAL_GEOMETRY',arm,result['faces_N'],flush=True)
            saved=torch.load(runner.output/'latest.pt',map_location='cpu',weights_only=False)
            torch.set_rng_state(saved['torch_rng']);torch.cuda.set_rng_state(saved['cuda_rng'])
            random.setstate(saved['python_rng']);np.random.set_state(saved['numpy_rng']);del saved
        runner.run()
        assert runner.iter_step==200000
        atomic_json(f'metrics/single_{arm}_STATUS.json',dict(status='COMPLETED_200K',step=200000,
            official_chain_calls=runner.events,scientific_acceptance='REQUIRES_GEOMETRY_REVIEW',GT=False))
        return 0
    except BaseException as error:
        step=getattr(runner,'iter_step',0)
        save(f'metrics/single_{arm}_INTERRUPTION.json',dict(status='ENGINEERING_INTERRUPTION_NOT_SCIENTIFIC_FAILURE',
            completed_updates=step,type=type(error).__name__,reason=str(error),traceback=traceback.format_exc()))
        print(traceback.format_exc(),flush=True)
        return 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('arm',choices=['M0','M1']);parser.add_argument('--resume',action='store_true')
    a=parser.parse_args();sys.exit(main(a.arm,a.resume))
