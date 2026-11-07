from common import *

def main():
 assert load(R/'metrics/PREFLIGHT.json')['passed']
 for a in load(R/'assets_index/HISTORY_011_PROTECTION.json'):assert sha(a['path'])==a['sha256']
 files=[asset(p)for d in ['code','config','inputs','depth_observations']for p in sorted((R/d).rglob('*'))if p.is_file()]+[asset(p)for p in sorted((R/'local_results').glob('*_P0_SUPPORT.npz'))]+[asset(R/'01_PROTOCOL.md')]
 save('assets_index/PREOPT_FREEZE.json',dict(files=files,time_epoch=time.time(),GT_read=False,source011_unchanged=True,only_one_free_vertex_arm=True));print('PREOPT_FROZEN',len(files))

if __name__=='__main__':main()
