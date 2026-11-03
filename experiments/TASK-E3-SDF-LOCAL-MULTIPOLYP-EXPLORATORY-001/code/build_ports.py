"""Controlled copies of the reviewed adapter/official runner ports; no new renderer."""
from pathlib import Path
import difflib,json,hashlib
TASK=Path(__file__).resolve().parents[1]
OLD=Path('/home/liu/ring_first_3d_e3_sdf_full/experiments/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001')


def replace(text,old,new,count=1):
    assert text.count(old)==count,(old,text.count(old),count)
    return text.replace(old,new)


def main():
    manifest=[]
    for name in ['official_adapter.py','prepare.py','geometry_monitor.py','train_full.py']:
        source=OLD/'code'/name;text=source.read_text();original=text
        if name=='prepare.py':
            text=replace(text,"stages={'single':['G01_004_ref08'],'three_CORE':SOURCES}","stages={'three_reference':SOURCES}")
            text=replace(text,"phase='RESOURCE_PREFLIGHT_NOT_FORMAL_TRAINING'","phase='LOCAL_EXPLORATORY_M1_10X'")
            text=replace(text,"input_baseline='N0 frozen V6 baseline + N0 fixed A2 pass; no new cleanup this task'","input_baseline='G01/G06 exact current N0 frozen inputs; G08 same fixed A2 method on frozen3; no output-driven cleanup'")
            text=replace(text,'checkpoint_steps=[0,1,10,100,1000,5000,10000,25000,50000,100000,150000,200000]','checkpoint_steps=[0,200,500,1000,2000,5000,10000]')
            text=replace(text,'coarse_checkpoint_resolution=128,final_resolution=512','coarse_checkpoint_resolution=256,final_resolution=256')
        elif name=='geometry_monitor.py':
            text=replace(text,'resolution = 512 if final else 128',"resolution = protocol()['mesh']['final_resolution'] if final else protocol()['mesh']['coarse_checkpoint_resolution']")
            text=replace(text,"in_training=cid==SOURCES[0]","in_training=cid in SOURCES")
        elif name=='train_full.py':
            text=replace(text,'data,batch=packet(SOURCES[0],step,N=1024)','data,batch=packet(SOURCES[(step-1)%len(SOURCES)],step,N=1024)')
            text=replace(text,'self.nepochs=200000-1','self.nepochs=10000-1')
            text=replace(text,"['stages']==['single']","['stages']==['three_reference']")
            text=replace(text,'step<=200000','step<=10000')
            text=replace(text,'planned_updates=200000','planned_updates=10000')
            text=replace(text,'final=step==200000','final=step==10000')
            text=replace(text,'runner.iter_step==200000','runner.iter_step==10000')
            text=replace(text,"status='COMPLETED_200K',step=200000","status='COMPLETED_10000',step=10000")
            text=replace(text,"stage='single'","stage='three_reference'",2)
            text=replace(text,"source=SOURCES[0],formal=True","source=SOURCES[(step-1)%len(SOURCES)],formal=True")
            text=replace(text,"choices=['M0','M1']","choices=['M1']")
            text=replace(text,'self.started=time.monotonic(); self.last_clock=self.started','self.started=time.monotonic(); self.last_clock=self.started; self.time_offset=0.')
            text=replace(text,"self.resume_step=int(state['step']); self.start_epoch=self.resume_step", "assert state['scene']==SCENE and state['code_freeze_sha256']==sha(R/'provenance/BEFORE_FORMAL_TRAINING.json')\n            self.resume_step=int(state['step']); self.start_epoch=self.resume_step; self.time_offset=state['accumulated_elapsed_seconds']")
            text=replace(text,"state=dict(step=step,model=", "state=dict(step=step,scene=SCENE,accumulated_elapsed_seconds=self.time_offset+time.monotonic()-self.started,model=")
            text=replace(text,"print(traceback.format_exc(),flush=True)","atomic_json(f'metrics/single_{arm}_STATUS.json',dict(status='ENGINEERING_INTERRUPTION',step=step,reason=str(error)))\n        print(traceback.format_exc(),flush=True)")
        target=TASK/'code'/name
        assert not target.exists(),'PORT_ALREADY_EXISTS'
        target.write_text(text)
        (TASK/'provenance'/(name+'.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile=str(source),tofile=str(target))))
        manifest.append(dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),target=str(target),target_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),adaptation='exact M1 backbone/sampler/loss; source dispatch, bounded loop and monitoring/restore IO only'))
    (TASK/'provenance/PORT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
