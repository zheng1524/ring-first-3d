"""V5 actual-label boundary policy: Polyp-adjacent material edges are order-UNKNOWN."""
from ucommon import *
V5ADAPTER=OLD/'experiments/ring_first_v4_synthetic_audit/scripts/adapter.py'
def qualified(v):
 r=np.load(N/'ring_evidence'/(v['id']+'.npz'));lab=np.load(v['cache'])['labels'];near=cv2.dilate((lab==1).astype(np.uint8),np.ones((5,5),np.uint8))>0;out={};audit=[]
 for key in ['inner','outer']:
  q=np.asarray(r[key]);px=np.clip(np.floor(q+.5).astype(int),[0,0],[639,359]);unknown=near[px[:,1],px[:,0]];out[key]=q[~unknown];out[key+'_unknown']=q[unknown];audit.append(dict(group=v['group'],view=v['id'],role=v['role'],channel=key,raw_observations_N=len(q),visible_actual_N=int((~unknown).sum()),order_UNKNOWN_N=int(unknown.sum()),unsupported_ellipse_added=0,policy='exact V5 adapter5x5 nearPolyp mask; integerpixelcenterK; nofilledarcs',source=asset(V5ADAPTER)))
 return out,audit

def main():
 rows=[]
 for v in load(N/'config/VIEWS.json'):
  o,a=qualified(v);rows+=a
 table('metrics/ACTUAL_VISIBLE_ARC_QUALIFICATION.csv',rows);save('metrics/ACTUAL_VISIBLE_ARC_QUALIFICATION.json',rows);freeze('provenance/VISIBLE_ARCS_FROZEN_BEFORE_BA.json',[Path(__file__),V5ADAPTER,N/'metrics/ACTUAL_VISIBLE_ARC_QUALIFICATION.json'],threshold_source='historicalV5notnewtuning',GT=False)
 print('QUALIFIED98;actualarcs',sum(r['visible_actual_N']for r in rows),'UNKNOWN',sum(r['order_UNKNOWN_N']for r in rows),flush=True)
if __name__=='__main__':main()
