"""Safe public entrypoint: existing frozen camera results are read-only."""
from ucommon import *
if __name__=='__main__':
 if(N/'provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json').exists():checkfreeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json');print('ALL_CANDIDATES_ALREADY_FROZEN_NO_OPTIMIZATION');sys.exit(0)
 raise SystemExit('Fresh independent rerun requires documented prepare/StageA commands; current partially existing directory is never automatically reset.')
