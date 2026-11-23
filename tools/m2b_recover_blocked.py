#!/usr/bin/env python3
"""M2B recover R1 blocked videos using largest real component / existing bridge frames."""
import json,os,subprocess,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2b_ring_global_branch'; M2A=WS/'runs/m2a_w0_recovery'; PREP=WS/'runs/m1_final_39/prepared'
sys.path.insert(0,str(WS/'tools'))
from m2a_c3 import pair_graph
from m2a_recover import make_subset
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'

def run(g,v,preproot,method,n):
 out=OUT/'recovery'/method/g/v; work=OUT/'work_recovery'/method/g/v; out.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)
 cmd=[PY,'tools/run_w0_camera.py','--group',g,'--video',v,'--stage','all','--prepared-root',str(preproot),'--output',str(out),'--workdir',str(work),'--ring-mode','all','--pair-offsets',','.join(str(i) for i in range(1,n))]
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 r=subprocess.run(cmd,cwd=WS,capture_output=True,text=True,env=env); (out/'stdout.log').write_text(r.stdout); (out/'stderr.log').write_text(r.stderr)
 st=json.loads((out/'STATUS.json').read_text()) if (out/'STATUS.json').exists() else {}
 q=json.loads((out/'quality_summary.json').read_text()) if (out/'quality_summary.json').exists() else {}
 return dict(group_id=g,video_id=v,method=method,returncode=r.returncode,execution_status=st.get('status'),reason=st.get('reason'),n_w0_poses=q.get('n_w0_poses'),n_accept=q.get('n_accept'),ring_mae=q.get('ring_mae_mean_px'),held_median=q.get('held_median_px'),held_p95=q.get('held_p95_px'),max_rot=q.get('max_adjacent_rotation_deg'),output_path=str(out))

def main():
 st=pd.read_csv(OUT/'R1_RUN_STATUS.csv'); blocked=st[st.status=='BLOCKED_QUALITY_GATE']
 rows=[]
 for _,r in blocked.iterrows():
  g,v=str(r.group_id),f'{int(r.video_id):03d}'; work=OUT/'work_r1'/g/v
  try:
   tr,edges,comps=pair_graph(work); keep=[str(tr['ids'][i]) for i in comps[0]]
  except Exception as e:
   rows.append(dict(group_id=g,video_id=v,method='C3',returncode=-1,execution_status='IMPLEMENTATION_ERROR',reason=str(e))); continue
  if len(keep)>=4:
   root=OUT/'prepared_c3'/f'{g}_{v}'; root.mkdir(parents=True,exist_ok=True)
   meta=json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text()); m2=dict(meta); m2['views']=[q for q in meta['views'] if q['view'] in set(keep)]; m2['selection_reason']='M2B_C3_LARGEST_COMPONENT'; (root/'PREPARED.json').write_text(json.dumps(m2,indent=1))
   rows.append(run(g,v,OUT/'prepared_c3','C3',len(keep)))
  # fallback to M2A bridge prepared if C3 failed
  if rows and rows[-1].get('execution_status') not in ('COMPLETED_VALID','COMPLETED_LIMITED'):
   for cand in [M2A/'prepared_c2b'/f'{g}_{v}',M2A/'prepared_c2'/f'{g}_{v}',M2A/'prepared_b1r'/f'{g}_{v}',M2A/'prepared_c3'/f'{g}_{v}']:
    if (cand/'PREPARED.json').exists():
     n=len(json.loads((cand/'PREPARED.json').read_text())['views']); rows.append(run(g,v,cand.parent,'BRIDGE',n)); break
 pd.DataFrame(rows).to_csv(OUT/'R1_RECOVERY_RESULTS.csv',index=False)
 print(pd.DataFrame(rows)[['group_id','video_id','method','execution_status','n_w0_poses','n_accept']].to_string(index=False))
if __name__=='__main__': main()
