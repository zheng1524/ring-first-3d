"""Known CAD ray controlled order tests; no real HERO/Polyp GT used."""
from common import *
from evaluate020 import visibility_query
def main():
 v=next(x for x in load(R/'config/VIEWS.json')if x['id']=='G01_004_ref08');C=np.asarray(v['T']);K=np.asarray(v['K']);r=np.load(R/'inputs/G01/RING.npz');cad=scene(r['V'],r['F']);depth=cast(cad,K,C,360,640);yx=np.argwhere(np.isfinite(depth));y,x=yx[len(yx)//2];z=depth[y,x];ray=np.array([x,y,1.])@np.linalg.inv(K).T;rows=[]
 cases=[('TARGET_BEHIND_CAD_IS_UNKNOWN',-.3,.3,'target_Ring_order_unreliable'),('RELIABLE_FRONT_PROXY',-1.,-.2,'front'),('DEEPER_LAYER_NOT_FRONT_CONFLICT',-.2,-1.,'behind'),('CANDIDATE_BEHIND_CAD_IS_OCCLUDED',.2,-.5,'cad_occluded')]
 for name,src,tar,key in cases:
  X=(ray*(z+src))@C[:3,:3].T+C[:3,3];grid=np.full((360,640),np.nan);grid[y,x]=z+tar;o=visibility_query(X[None],C,K,grid,cad);passed=bool(o[key][0])
  if key in ['target_Ring_order_unreliable','cad_occluded']:passed&=not bool(o['known'][0]or o['front'][0]or o['behind'][0])
  if key=='behind':passed&=not bool(o['front'][0])
  rows.append(dict(case=name,passed=passed,source_offset_from_CAD_mm=src,target_offset_from_CAD_mm=tar,status={k:bool(o[k][0])for k in ['known','target_Ring_order_unreliable','cad_occluded','front','behind']}))
 save('metrics/HERO_VISIBILITY_CONTROL_TESTS.json',dict(cases=rows,all_passed=all(x['passed']for x in rows),controlled_known_CAD_ray=True,actual_HERO_used=False,Polyp_GT_used=False,thresholds_unchanged=True));assert all(x['passed']for x in rows);print('HERO_VISIBILITY_ORDER_CONTROL_PASSED',len(rows),flush=True)
if __name__=='__main__':main()
