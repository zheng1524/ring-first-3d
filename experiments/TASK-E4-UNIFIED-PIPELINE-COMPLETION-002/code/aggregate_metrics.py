"""Uniform fixed-denominator metric tables; no fitting or GT content access."""
from pathlib import Path
import csv
import pipeline as p
def readcsv(file):return list(csv.DictReader(Path(file).open())) if Path(file).exists() else []
def main():
    views=[];depth=[];geometry=[]
    for c in p.cases():
        g=c['case']
        for vi in ['004','005']:
            base=p.OLD/'metrics' if p.inherited(g,vi) else p.TASK/'metrics'/g/vi
            metrics=readcsv(base/'PER_VIEW_METRICS.csv');dm=readcsv(base/'DEPTH_METRICS.csv');gm=readcsv(base/'GEOMETRY_METRICS.csv');execution='FROZEN_REFERENCE' if p.inherited(g,vi) else 'NEW'
            for v in p.instance_views(g,vi):
                cid=v['meta']['id'];role='FIT' if v['meta']['role']=='FIT' else 'HOLDOUT'
                for arm in ['B0','B1','B2']:
                    r=next((dict(r) for r in metrics if r['group']==g and r['arm']==arm and r['id']==cid),dict(group=g,video=vi,arm=arm,id=cid,role=role,camera_status='NOT_RUN',IoU='NaN',Boundary_MAE_px='NaN',Boundary_Fscore_at2px='NaN'))
                    r.update(video=vi,execution=execution)
                    for k in ['IoU','Boundary_MAE_px','Boundary_Fscore_at2px']:
                        if r.get(k) in ['',None]:r[k]='NaN'
                    cam=(p.OLD/'runs/RF_ONLY_V1' if p.inherited(g,vi) else p.OUT)/g/vi/'camera'/cid/'ADMISSION.json'
                    r['camera_status']=p.read(cam)['status'];r['projection_status']='PASS' if r['IoU']!='NaN' else 'NOT_RUN'
                    views.append(r)
                    if role=='FIT':
                        d=next((dict(r) for r in dm if r['group']==g and r['arm']==arm and r['view']==cid),None) if dm and 'view' in dm[0] else next((dict(r) for r in dm if r['group']==g and r['arm']==arm and r.get('id')==cid),None)
                        if d is None:d=dict(group=g,video=vi,arm=arm,view=cid,status='NOT_RUN',fixed_N='NaN',active_N='NaN',depth_MAE_mm='NaN',depth_p95_mm='NaN',coverage='NaN')
                        d.setdefault('status','PASS')
                        d.update(video=vi,execution=execution);depth.append(d)
            geometry.extend(dict(r,video=vi,execution=execution) for r in gm if r['group']==g)
    assert len(views)==315 and len(depth)==240
    p.table(p.TASK/'metrics/PER_VIEW_METRICS.csv',views);p.table(p.TASK/'metrics/DEPTH_METRICS.csv',depth);p.table(p.TASK/'metrics/GEOMETRY_METRICS.csv',geometry)
    print('UNIFORM_METRICS',len(views),'view-arm rows;',len(depth),'depth view-arm rows',flush=True)
if __name__=='__main__':main()
