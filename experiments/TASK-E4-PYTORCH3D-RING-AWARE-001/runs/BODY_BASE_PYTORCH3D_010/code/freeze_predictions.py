from common import *
def main():
 s=load(R/'runtime/SERIAL_STATUS.json');assert len(s)==18
 for a in load(R/'assets_index/PREOPT_FREEZE.json')['files']:assert sha(a['path'])==a['sha256'],a['path']
 for a in load(R/'assets_index/HISTORY_PROTECTION.json'):assert sha(a['path'])==a['sha256'],a['path']
 files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()];save('assets_index/PREDICTIONS_FROZEN.json',dict(files=files,time_epoch=time.time(),formal_attempts=18,completed_300=sum(x.get('run',{}).get('status')=='COMPLETED'for x in s),all_formal_attempts_retained=True,real_GT_read=False));print('PREDICTIONS_FROZEN',len(files))
if __name__=='__main__':main()
