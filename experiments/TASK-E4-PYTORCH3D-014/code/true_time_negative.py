"""Reproduce the already executed raw-time negative-control inputs, not a new search.

Default validates all 244 frozen RGB background observations without optimization.
--solve is for a fresh isolated reproduction directory and cannot overwrite an
existing control. Archived-reference ordering is not a raw-time split.
"""
from pose_correction import *

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--solve',action='store_true');args=p.parse_args()
 vv=sorted([v for v in load(R/'config/DERIVED_VIEWS.json')if v['sid']=='G01_v004'],key=lambda v:v['raw_frame']);mid=len(vv)//2
 pick=lambda v:v[::max(1,len(v)//8)][:8]
 A,B=pick(vv[:mid]),pick(vv[mid:]);label='G01_004_TRUE_RAW_TIME_SPLIT_NEGATIVE';dest=R/'metrics/pose'/(label+'.json')
 assert max(v['raw_frame']for v in A)<min(v['raw_frame']for v in B)
 if args.solve:
  assert not dest.exists(),'Preserve the executed control; solve only in a fresh isolated reproduction'
  case=next(c for c in load(R/'config/CASE_LOCK.json')if c['name']=='G01');solve(A,B,label,case)
 old=load(dest)['BG_observations'];rows,_=build_matches(A,B)
 same=len(rows)==len(old)and all(x['view']==y['view']and x['held']==y['held']and x['image_held']==y['image_held']and np.array_equal(x['X'],y['X'])and np.array_equal(x['uv'],y['uv'])for x,y in zip(rows,old))
 assert same,'Frozen negative-control background observation regression failed'
 save('provenance/TRUE_RAW_TIME_CONTROL_REPRODUCTION.json',dict(epoch=time.time(),A_ids=[v['id']for v in A],B_ids=[v['id']for v in B],rule='sort existing derived raw candidates by actual frame; split in half; in each half floor-step sampling, first8, as originally executed',temporal_split_disjoint=True,background_observations_N=len(rows),every_X_uv_identity_and_split_exact=True,source=asset(Path(__file__)),frozen_control=asset(dest),optimizer_rerun=args.solve,GT_used=False))
 print('TRUE_RAW_TIME_INPUT_REGRESSION_PASS',len(rows))
if __name__=='__main__':main()
