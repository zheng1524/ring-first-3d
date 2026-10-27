"""Post-prediction comparisons on identical target-mask pixel support."""
from evaluation import *
def compare(left,right,t,meta):
    B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0);rows=[]
    for typ in ['point','triangle']:
        a=dict(np.load(left/(typ+'_prediction_exact.npz')));b=dict(np.load(right/(typ+'_prediction_exact.npz')));common=(a['kind']==1)&(b['kind']==1)&(mask==1);rows.append(dict(**meta,projection=typ,target=t['id'],target_mask_N=int((mask==1).sum()),left_support_N=int(((a['kind']==1)&(mask==1)).sum()),right_support_N=int(((b['kind']==1)&(mask==1)).sum()),common_support_N=int(common.sum()),left_RGB=errors(a,B,common),right_RGB=errors(b,B,common),comparison_identity='RGB_CONSISTENCY_NOT_GEOMETRY_ACCURACY'))
    return rows
def main():
    rows=[];tag=load(R/'metrics/D1_display_candidate.json')['candidate']
    for video,other in [('005','004'),('004','005')]:
        for t in target(other,'holdout'):
            base=R/'local_results/D1_evaluation';sub=video+'_to_'+other;rows+=compare(base/'HISTORICAL_FULL_LightGlue'/sub/t['id'],base/tag/sub/t['id'],t,dict(stage='D1',source_video=video,left='HISTORICAL_FULL_LightGlue',right=tag))
    for video in ['004','005']:
        for t in target(video,'holdout'):
            for old in ['SINGLE','B','C']:
                base=R/f'local_results/D0_evaluation/{video}';rows+=compare(base/old/t['id'],base/'D0_FULL'/t['id'],t,dict(stage='D0',source_video=video,left=old,right='D0_FULL'))
    save('metrics/PAIRED_COMMON_SUPPORT.json',rows);csvsave('metrics/PAIRED_COMMON_SUPPORT.csv',rows);print('PAIRED_SUPPORT',len(rows),'comparisons',flush=True)
if __name__=='__main__':main()
