"""Small geometric/evaluation invariants; no GT, no new reconstruction."""
from io_utils import *
from reprojection import render,evaluate
def main():
    tests=[]
    def check(name,test):assert test,name;tests.append(name)
    c,P,C,m,p,uv=source('G01_004_ref08');xy,z=vis.project_camera(P,p['K'],p['pose']);check('source XYZ reprojects to ORIGINAL pixel identities',np.max(abs(xy-uv))<1e-4)
    H=np.eye(4);H[:3,3]=[2,3,4];xy2,z2=vis.project_camera(P+H[:3,3],p['K'],H@p['pose']);check('joint rigid translation preserves pixels and axial mm',np.allclose(xy,xy2)and np.allclose(z,z2))
    red=np.tile([1.,0.,0.],(len(P),1));a=render(P,m.faces,red,p['K'],p['pose'],np.eye(4),c['ring']);check('source triangles preserve constant A vertex color',np.all(a['RGBA'][a['valid'],:3]==[255,0,0]))
    v=a['valid'];n=int(v.sum());lab=np.zeros((360,640),np.uint8);lab[v]=1;B1=np.zeros((360,640,3),np.uint8);B1[v]=[255,0,0];s1,_,_=evaluate(a,B1,lab);B2=np.full_like(B1,255);s2,_,_=evaluate(a,B2,lab);check('evaluation uses exact declared common support denominator',s1['common_pixels']==n and s1['target_coverage']==1);check('B changes evaluation but never prediction',s1['RGB_MAE_0_255']==0 and s2['RGB_MAE_0_255']>0 and np.all(a['RGBA'][v,:3]==[255,0,0]))
    check('outside-target predictions retained in separate denominator',evaluate(a,B1,np.zeros_like(lab))[0]['predicted_outside_target_pixels']==n)
    check('historical formal diameter failures remain 81/81',all(x['status']=='NOT_EVALUABLE'and x['Dproj_mm']is None for x in load(R/'prediction_snapshot/D_projected_diameter.json')))
    save('metrics/small_tests.json',dict(passed=len(tests),tests=tests));print('SMALL_TESTS',len(tests),'PASS')
if __name__=='__main__':main()
