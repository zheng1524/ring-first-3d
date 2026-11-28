"""Dispatch original pipeline; per-group receipt prevents writers sharing SMOKE_STATUS."""
import core,sys,fcntl
group=sys.argv[1];original_save=core.save
lock_path=core.T/'runs/results'/group/'EXECUTION.lock';lock_path.parent.mkdir(parents=True,exist_ok=True);lock=lock_path.open('a');fcntl.flock(lock,fcntl.LOCK_EX)
def save(path,value):
 if str(path).endswith('/SMOKE_STATUS.json'):path=core.T/'runs/results'/group/'EXECUTION_RECEIPT.json'
 return original_save(path,value)
core.save=save
import pipeline
sys.argv=[sys.argv[0],'--group',group];pipeline.main()
