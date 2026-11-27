"""Post-result interface diagnostic for one explicitly selected M4 candidate.
No new prediction, no new held validation, no change to primary M5 experiment.
"""
from context import *
from clean_after import one
from evaluate_real2 import load_geometry,geometric
import traceback
GROUP='GP_IIa_14.0mm_closed_R5_single_refY'
def main():
 out=RUN/'real'/GROUP;pred=read(out/'PREDICTIONS.json');assert sha(out/'PREDICTIONS.json')==read(out/'PREDICTION_FREEZE.json')['predictions_sha256'];freeze('CANDIDATE_M4_CLEAN',out,[out/'EVALUATION.json',out/'PREDICTION_FREEZE.json']);save(out/'CANDIDATE_SELECTION.json',dict(group=GROUP,method='M4',selection_timing='AFTER primary held evaluation',reason='lowest bidirectional M4 conditional MAE in six groups; fourteen independent two-sided held tracks; only a candidate, LOO .613deg remains',not_blind_validation=True,body_update_authorized=False));a=read(T/'config'/GROUP/'ASSETS.json');old=read(out/'CLEAN_INDEX.json');index=[]
 for i,s in enumerate(a['sources']):
  try:
   if s['side']=='A':
    r=next(r for r in old if r['source']['side']==s['side']and r['source']['tag']==s['tag']);assert np.array_equal(r['T_local_to_global'],np.eye(4));assert sha(r['selection_path'])==r['selection_sha256'];r=dict(r,origin='REUSED_SAME_POST_REGISTRATION_A_FRAME',registration_method='M4')
   else:r=one(s,i,out,np.array(pred['M4']['T']),method='M4')
  except Exception as e:r=dict(source=s,status='MISSING',origin='NOT_COMPLETED',error=repr(e),traceback=traceback.format_exc())
  index.append(r);save(out/'CLEAN_INDEX_M4_CANDIDATE.json',index)
 assert len(index)==len(a['sources']);packs=load_geometry(out)
 for p,r in zip(packs,index):
  assert p['source']['tag']==r['source']['tag']and p['source']['side']==r['source']['side'];p['state']=np.load(r['selection_path'])['state']if r.get('status')!='MISSING'else None;p['record']=r
 save(out/'CANDIDATE_M4_CLEAN_RESULT.json',dict(group=GROUP,method='M4',new_B_sources=sum(r['origin']=='NEW_POST_REGISTRATION'for r in index),reused_A_sources=sum(r['origin'].startswith('REUSED')for r in index),missing=sum(r.get('status')=='MISSING'for r in index),clean=geometric(packs,np.array(pred['M4']['T']),True),raw_area_mm2=sum(r.get('raw_area_mm2',0)for r in index),clean_area_mm2=sum(r.get('trusted_area_mm2',0)for r in index),common_face_extra_movement_mm=0,postselection=True))
 interface=read(out/'interfaces/M4.json');by={(r['source']['side'],r['source']['tag']):r for r in index}
 for s in interface['Raw_sources']:
  r=by[s['side'],s['tag']];s['clean_selection']=r.get('selection_path');s['clean_coordinate_frame']='M4 shared frame; post-result candidate interface diagnostic'
 interface['post_result_candidate']=True;save(out/'interfaces/M4_CANDIDATE_WITH_CLEAN.json',interface);print('M4 CANDIDATE CLEAN DONE',len(index),flush=True)
if __name__=='__main__':main()
