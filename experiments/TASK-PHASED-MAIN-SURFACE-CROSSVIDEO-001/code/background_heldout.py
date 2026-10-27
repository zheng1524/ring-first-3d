"""Evaluate already-frozen H on third-reference background, never select by it."""
from registration import *
def main():
    paths=[R/'metrics/D1_candidates.json',R/'provenance/D1_FIT_SELECTION_FROZEN.json',*[R/f'local_results/background/{v}_working.npz'for v in ['004','005']]];save('provenance/BACKGROUND_HELDOUT_BEFORE_COMPUTE.json',dict(**stamp([Path(__file__),*paths]),post_prediction=True,used_to_choose_H=False,GT_error=False));P={v:np.load(R/f'local_results/background/{v}_working.npz')['heldout_XYZ_mm']for v in ['004','005']};norm={v:np.asarray(cloud(P[v]).normals)for v in P};rows=[]
    for c in load(R/'metrics/D1_candidates.json'):
        H=np.array(c['H_005_to_004'])
        for a,b,T in [('005','004',H),('004','005',np.linalg.inv(H))]:rows.append(dict(candidate=c['tag'],source_video=a,target_video=b,**pair_stats(P[a],P[b],T,norm[b]),support_identity='THIRD_REFERENCE_FROZEN_DEPTH_NOT_FITTED; MODEL_CONDITIONAL_NOT_GT',used_for_H_selection=False))
    save('metrics/D1_BACKGROUND_HELDOUT.json',rows);csvsave('metrics/D1_BACKGROUND_HELDOUT.csv',rows);print('BACKGROUND_HELDOUT',len(rows),'fixed-prediction rows',flush=True)
if __name__=='__main__':main()
