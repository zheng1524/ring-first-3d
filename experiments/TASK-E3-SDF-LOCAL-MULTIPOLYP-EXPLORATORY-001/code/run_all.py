"""Serial GPU use, three independent M1 models, no search or extra epochs."""
from common import *


def main():
    progress=[]
    for scene in ORDERS:
        env=os.environ.copy();env['MONOSDF_SCENE']=scene
        log=TASK/'runtime'/f'TRAIN_{scene}.log'
        assert not log.exists(),'DO_NOT_OVERWRITE_EXISTING_RUN; inspect/resume explicit checkpoint'
        with log.open('w')as output:
            result=subprocess.run([sys.executable,'-B',str(TASK/'code/train_full.py'),'M1'],
                cwd=REPO,env=env,stdout=output,stderr=subprocess.STDOUT)
        progress.append(dict(scene=scene,returncode=result.returncode))
        (TASK/'metrics/SERIAL_PROGRESS.json').write_text(json.dumps(progress,indent=2)+'\n')
        if result.returncode!=0:
            print('ENGINEERING_INTERRUPTION',scene,'not a scientific failure',flush=True)
            subprocess.run([sys.executable,'-B',str(TASK/'code/deliver.py')],cwd=REPO,check=True)
            return result.returncode
        assert load(TASK/'groups'/scene/'metrics/single_M1_STATUS.json')['status']=='COMPLETED_10000'
    subprocess.run([sys.executable,'-B',str(TASK/'code/deliver.py')],cwd=REPO,check=True)
    # User explicitly requested small results/code on the isolated GitHub branch.
    # Checkpoints/fields/raw datasets are ignored and remain local; no force push.
    subprocess.run(['git','add','--',str(TASK.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m','Complete three independent 10000-step exploratory M1 models and raw-Mesh comparisons'],cwd=REPO,check=True)
    subprocess.run(['git','push','origin','exp/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001'],cwd=REPO,check=True)
    return 0


if __name__=='__main__':sys.exit(main())
