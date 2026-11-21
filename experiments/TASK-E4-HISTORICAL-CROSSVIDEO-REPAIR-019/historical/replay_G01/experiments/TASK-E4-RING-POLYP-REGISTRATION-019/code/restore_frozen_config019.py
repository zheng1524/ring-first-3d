"""Restore the delivered pre-search configuration into an independent replay copy.

Run after prepare019.py in that copy, before features/search. No original writes.
"""
from common import *
import argparse

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--destination',required=True);args=parser.parse_args();dest=Path(args.destination).resolve()
 assert dest!=R,'Use an independent replay directory, never the frozen experiment'
 assert not(dest/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json').exists(),'Destination already has frozen predictions'
 (dest/'config').mkdir(exist_ok=True,parents=True);src=load(R/'provenance/BEFORE_SEARCH_FREEZE.json')
 for key in ['views','protocol','written_protocol']:assert sha(src[key]['path'])==src[key]['sha256']
 for name in ['VIEWS.json','NEGATIVE_SPLIT.json','PROTOCOL.json','HERO_SOURCE_METADATA_005.json','VIEW_PLAN.json','HISTORICAL_CANDIDATES.json']:
  data=load(R/'config'/name)
  def translate(x):
   if isinstance(x,dict):return{k:translate(v)for k,v in x.items()}
   if isinstance(x,list):return[translate(v)for v in x]
   if isinstance(x,str)and x.startswith(str(R)+'/'):return str(dest)+x[len(str(R)):]
   return x
  (dest/'config'/name).write_text(json.dumps(translate(data),ensure_ascii=False,indent=2)+'\n')
 (dest/'01_PROTOCOL.md').write_bytes((R/'01_PROTOCOL.md').read_bytes())
 print('FROZEN_CONFIG_RESTORED_INDEPENDENT_COPY',dest)
if __name__=='__main__':main()
