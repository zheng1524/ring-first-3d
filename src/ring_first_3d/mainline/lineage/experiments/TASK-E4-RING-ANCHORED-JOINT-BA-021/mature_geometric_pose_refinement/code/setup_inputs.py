"""Restore audited local input links; never modify frozen predictions or upstream assets."""
from gcommon import *
def main():
 old=P/'geometric_pose_optimization'
 for name in ['VIEWS.json']:
  dst=M/'config'/name
  if dst.exists():assert sha(dst)==sha(old/'config'/name)
  else:dst.write_bytes((old/'config'/name).read_bytes())
 for folder in ['features','ring_evidence','landmarks']:
  for p in(old/folder).glob('*'):
   dst=M/folder/p.name
   if not dst.exists():dst.symlink_to(p.resolve())
 for v in load(M/'config/VIEWS.json'):
  dst=M/'inputs'/v['id']/'RGB_GEOMETRY.json';dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():dst.symlink_to((old/'inputs'/v['id']/'RGB_GEOMETRY.json').resolve())
 print('AUDITED_INPUT_LINKS_READY; NO_REINITIALIZATION')
if __name__=='__main__':main()
