"""Same-RGB, same frozen Ring geometry for named historical G01 candidates.
Evaluation only. Candidate H moves native005 non-common map; no pose selection.
"""
from register import *
def main():
 rows=load(N/'metrics/ALL_POSE_CANDIDATE_COMPARISONS.json');vv=load(camera_file('G01'));uv={v['id']:v for v in load(U/'config/VIEWS.json')};H0=np.array(load(U/'config/H0.json')['G01_005_to004']);hist=[h for h in load(P/'config/HISTORICAL_CANDIDATES.json')if h['tag']in ['HISTORICAL_FULL_RoMa','HISTORICAL_FULL_LightGlue']]
 for tag,f in [('FROZEN020_R2','B0_020_R2.json'),('FROZEN020_R3','B0_020_R3.json'),('FROZEN020_MASK_ONLY','B0_020_MASK.json')]:hist.append(dict(tag=tag,T=load(P/'results'/f)['T'],source=asset(P/'results'/f)))
 rows=[r for r in rows if not(g:=r['group']=='G01')or r['method']not in [h['tag']for h in hist]]
 for h in hist:
  H=np.array(h['T']);D=H@np.linalg.inv(H0)
  for v in vv:
   ov=uv.get(v.get('initial_canonical_id'))
   if v['role']!='FIT'or v['video']!='005'or ov is None:continue
   C=H@np.array(ov['RF_native']);rr=load(v.get('rgb_geometry_path',N/'inputs'/v['id']/'RGB_GEOMETRY.json'));rows.append(dict(group='G01',id=v['id'],video='005',method=h['tag'],role='FIT',physical=physical(v,C,observe(v)),RGB=errors(v|dict(evaluation_map_H=D),C,rr),unit='mm',scope='same canonical005RGB;map005followscandidateH;notcomparedtoadditionalrawframecount',source=h.get('source',asset(P/'config/HISTORICAL_CANDIDATES.json')),same_input_map_basis=True))
 save('metrics/ALL_POSE_CANDIDATE_COMPARISONS.json',rows);table('metrics/ALL_POSE_CANDIDATE_COMPARISONS.csv',rows);save('metrics/HISTORICAL_SAME_INPUT_EVALUATION_RECEIPT.json',dict(tags=[h['tag']for h in hist],selection_used=False,HERO_used=False,source=asset(Path(__file__))));print('HISTORICAL_SAME_INPUT_EVALUATED',len(rows),flush=True)
if __name__=='__main__':main()
