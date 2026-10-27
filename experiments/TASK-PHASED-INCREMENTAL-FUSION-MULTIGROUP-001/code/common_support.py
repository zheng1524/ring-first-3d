"""Compare unchanged predictions on shared target pixels; no fitting or selection."""
from pipeline import *
def main():
    rows=[]
    for spec in load(R/'provenance/REVIEW_TARGETS_FROZEN.json'):
        sc=spec['scene'];t=spec['target'];B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0)==1;pairs=[('primary','core')]+([('B','evidence'),('C','evidence')]if sc.startswith('G01')else[])
        for left,right in pairs:
            a=np.load(R/f'local_results/coverage/{sc}/{left}/{t["id"]}/source_RGB_prediction.npz');b=np.load(R/f'local_results/coverage/{sc}/{right}/{t["id"]}/source_RGB_prediction.npz')
            for typ in ['point','triangle']:
                A=a[typ+'_RGBA'];C=b[typ+'_RGBA'];valid=(A[:,:,3]>0)&(C[:,:,3]>0)&mask;rows.append(dict(scene=sc,left=left,right=right,target=t['id'],view_role=spec['role'],projection=typ,target_mask_N=int(mask.sum()),common_support_N=int(valid.sum()),left_RGB=errors(dict(RGBA=A),B,valid),right_RGB=errors(dict(RGBA=C),B,valid),GT_error=None))
    save('metrics/E_common_support.json',rows);csvsave('metrics/E_common_support.csv',rows);print('COMMON_SUPPORT',len(rows),'comparisons',flush=True)
if __name__=='__main__':main()
