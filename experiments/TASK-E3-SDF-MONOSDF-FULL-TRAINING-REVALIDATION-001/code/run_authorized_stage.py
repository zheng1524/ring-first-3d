"""Sequential ref08 M0 then M1, exactly 200k each; no three-CORE launch."""
from common import *


def main():
    permit=load(R/'config/FORMAL_STAGE_FROZEN.json')
    assert permit['authorized_stages']==['single'] and permit['steps_per_arm']==200000
    states=[]
    for arm in ['M0','M1']:
        status=R/f'metrics/single_{arm}_STATUS.json'
        if status.exists()and load(status).get('status')=='COMPLETED_200K':
            states.append(dict(arm=arm,status='ALREADY_COMPLETED_200K'));continue
        log=R/'runtime'/f'FORMAL_single_{arm}.log'
        assert not log.exists(), 'EXISTING_RUN_REQUIRES_EXPLICIT_RESUME_NOT_REINITIALIZATION'
        with log.open('w')as output:
            result=subprocess.run([sys.executable,'-B',str(R/'code/train_full.py'),arm],
                cwd=REPO,stdout=output,stderr=subprocess.STDOUT)
        states.append(dict(arm=arm,returncode=result.returncode))
        save('metrics/AUTHORIZED_STAGE_PROGRESS.json',dict(states=states,three_CORE='NOT_AUTHORIZED_TO_START_YET'))
        if result.returncode!=0:
            print('ENGINEERING_INTERRUPTION',arm,'do not infer scientific failure; see log',flush=True)
            return result.returncode
        assert load(status)['status']=='COMPLETED_200K'
        subprocess.run([sys.executable,'-B',str(R/'code/render_progress.py')],cwd=REPO,check=True)
    save('metrics/AUTHORIZED_STAGE_PROGRESS.json',dict(status='SINGLE_M0_M1_COMPLETED_AWAIT_REVIEW',
        steps_per_arm=200000,total_formal_steps=400000,three_CORE='AWAIT_RESEARCHER_RESOURCE_REVIEW'))
    return 0


if __name__=='__main__':sys.exit(main())
