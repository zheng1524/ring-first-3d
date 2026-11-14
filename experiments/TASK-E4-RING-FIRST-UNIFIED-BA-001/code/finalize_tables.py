"""Explicitly retain not-run rows instead of hiding conditional branches."""
from ucommon import *
def main():
 rows=load(N/'metrics/PER_VIEW_CAMERA_GEOMETRY.json');rows=[r for r in rows if r['method']!='B4'];stage=load(N/'STAGE_DECISION.json')
 for v in load(N/'config/VIEWS.json'):rows.append(dict(group=v['group'],video=v['video'],id=v['id'],role=v['role'],method='B4',status=stage['B4_status'],C=None,Ring_IoU=None,no_historical_fallback=True,physical_unit='mm'))
 save('metrics/PER_VIEW_CAMERA_GEOMETRY.json',rows);table('metrics/PER_VIEW_CAMERA_GEOMETRY.csv',rows)
 h=load(N/'metrics/HERO_SURFACE_ALIGNMENT_SCORECARD.json');h=[r for r in h if r['method']!='B4']+[dict(group=g,method='B4',status=stage['B4_status'],fixed_N=None,known_N=None,depth_mm=None)for g in GROUPS];save('metrics/HERO_SURFACE_ALIGNMENT_SCORECARD.json',h);table('HERO_SURFACE_ALIGNMENT_SCORECARD.csv',h);print('ALL5_METHOD_OUTCOMES',len(rows))
if __name__=='__main__':main()
