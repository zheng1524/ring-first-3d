"""Safe verification entrypoint. Never refits or overwrites frozen results."""
from context import *
if __name__=='__main__':
 final=N/'provenance/FINAL_DELIVERY_FROZEN.json'
 if not final.exists():raise SystemExit('Final package not frozen yet. Do not start optimizer through replay.')
 checkfreeze('provenance/FINAL_DELIVERY_FROZEN.json');checkfreeze('provenance/ALL_CAMERAS_FROZEN_BEFORE_COVERAGE_HERO.json');
 for g in GROUPS:checkfreeze(planfreeze(g))
 result=load(N/'results/FINAL_INDEPENDENT_SUCCESS_AND_FAILURE_COUNTS.json');print(json.dumps(result,ensure_ascii=False,indent=2));print('FROZEN_RESULTS_VERIFIED_NO_OPTIMIZATION')
