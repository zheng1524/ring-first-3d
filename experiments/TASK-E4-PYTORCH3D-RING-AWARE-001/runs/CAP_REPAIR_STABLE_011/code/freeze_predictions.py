from common import *
def main():
 s=load(R/'runtime/SERIAL_STATUS.json');assert len(s)==9
 for a in load(R/'assets_index/PREOPT_FREEZE.json')['files']:assert sha(a['path'])==a['sha256'],a['path']
 for a in load(R/'assets_index/HISTORY_PROTECTION.json'):assert sha(a['path'])==a['sha256'],a['path']
 save('assets_index/PREDICTIONS_FROZEN.json',dict(files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()],time_epoch=time.time(),source_unchanged=True,GT_read=False));print('PREDICTIONS_FROZEN')
if __name__=='__main__':main()
