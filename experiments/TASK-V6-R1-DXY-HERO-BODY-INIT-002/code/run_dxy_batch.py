"""Scheduling only: prioritize existing 3D-selected frames, preserve every ledger row."""
from dxy_full import *
import concurrent.futures
from collections import Counter

def main():
 rows,lock=inventory();byid={r['source_id']:r for r in rows};records={};failures={};started=time.time()
 priority=['GP_IIa_14.0mm_closed_R5_single_refY','GP_IIa_22.0mm_closed_R10_single_refY','GP_Ip_10.3mm_closed_R5_single_refY','GP_IIa_5.2mm_closed_R10_single_refY']
 work=sorted(rows,key=lambda r:(r['role']=='UNSELECTED',priority.index(r['group']) if r['group'] in priority else len(priority),r['group'],r['case'],r['index']))
 def publish():
  data=[]
  for key in sorted(records):
   r=records[key];p=T/'runs/dxy'/r['case']/r['frame_id']/'FRAME.json'
   data.append({k:r[k] for k in ['group','case','index','frame_id','role','status','quality','selected_record_id','official_measurement_valid','official_ring_valid','candidate_count','P_count','Q_count','X_count']}|dict(path=str(p),sha256=sha(p)))
  save(T/'evidence/DXY_FRAME_INDEX.json',dict(frames=1700,completed=len(data),statuses=dict(Counter(r['status'] for r in data)),roles=dict(Counter(r['role'] for r in data)),rows=data,failures=list(failures.values()),pending=[r['source_id'] for r in rows if r['source_id'] not in records and r['source_id'] not in failures],inputs=asset(T/'evidence/DXY_INPUT_INDEX.json'),DXY_commit=COMMIT))
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(run_frame,r,lock):r for r in work}
  for i,f in enumerate(concurrent.futures.as_completed(futures)):
   row=futures[f]
   try:
    r=f.result();records[row['source_id']]=r;print(i+1,row['case'],row['frame_id'],r['status'],round(r['seconds'],2),flush=True)
   except Exception as e:
    failure=dict(source_id=row['source_id'],error=repr(e),traceback=traceback.format_exc(),row=row);failures[row['source_id']]=failure;save(T/'runs/dxy'/row['case']/row['frame_id']/'FAILURE.json',failure);print('FAIL',row['source_id'],repr(e),flush=True)
   if(i+1)%20==0:publish()
 publish();save(T/'evidence/DXY_BATCH_RECEIPT.json',dict(start=started,end=time.time(),workers=4,scientific_code=asset(T/'code/dxy_full.py'),scheduler=asset(__file__),complete=len(records),failure_count=len(failures),order='Existing FIT/HOLDOUT before UNSELECTED; smoke groups first; roles and scientific settings unchanged'))
 print('COMPLETE',len(records),'FAIL',len(failures),flush=True)
if __name__=='__main__':main()
