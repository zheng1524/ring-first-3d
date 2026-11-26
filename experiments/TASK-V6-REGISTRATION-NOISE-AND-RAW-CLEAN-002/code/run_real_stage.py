from common2 import *
import sys,traceback
from real2 import make_tracks
from clean2 import make_clean
for item in read(T/'config/SELECTION.json')['groups']:
 g=item['group'];out=RUN/'real'/g
 try:
  stage_freeze(sys.argv[1].upper(),out,[T/'config'/g/'ASSETS.json'])
  if sys.argv[1]=='track':make_tracks(g)
  else:make_clean(g)
 except Exception as e:
  save(out/(sys.argv[1]+'_FAILURE.json'),dict(error=repr(e),traceback=traceback.format_exc()));print('FAILURE',g,repr(e),flush=True)
