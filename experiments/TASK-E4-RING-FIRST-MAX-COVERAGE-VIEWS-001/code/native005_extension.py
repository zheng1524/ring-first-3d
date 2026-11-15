"""One explicit asset-completeness extension, not a threshold/loss search.
Preserves first-pass004-only map and all frozen predictions. Reuses native005
real-SIFT map with actual18 cross-RGB identities. No3D-nearest merge.
"""
from register import *

def pnp_bank(v,video):
 f=features(v);mp=dict(np.load(G/'landmarks'/('G01_'+video+'.npz')));X=mp['X'].copy();common=load(P/'observations/CROSS_COMMON_TRACKS.json');link={r['source_landmark005']:r['source_landmark004']for r in common};H0=np.array(load(U/'config/H0.json')['G01_005_to004']);H21=np.array(load(P/'results/B3.json')['T'])
 if video=='005':D=H0@np.linalg.inv(H21);X=X@D[:3,:3].T+D[:3,3]
 pairs=mutual(mp['des'],f['des']);rr=[]
 for k,j,d in pairs:
  uid=k if video=='004'else link.get(k,100000+k);rr.append(dict(landmark=uid,native_landmark=k,native_map=video,feature=j,distance=d,X=X[k],uv=f['xy'][j],region=int(f['region'][j]),role='FEATURE_HELD'if uid%5==0 else'FIT'))
 fit=[r for r in rr if r['role']=='FIT'];C=None;inrows=[]
 if len(fit)>=6:
  xx=np.array([r['X']for r in fit]);uv=np.array([r['uv']for r in fit]);cv2.setRNGSeed(20261115);ok,r,t,ids=cv2.solvePnPRansac(xx,uv,K0,None,iterationsCount=1000,reprojectionError=3.,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
  if ok and ids is not None and len(ids)>=6:
   ii=ids.ravel();r,t=cv2.solvePnPRefineLM(xx[ii],uv[ii],K0,None,r,t);W=np.eye(4);W[:3,:3]=cv2.Rodrigues(r)[0];W[:3,3]=t.ravel();C=np.linalg.inv(W);inrows=[fit[j]for j in ii]
 return dict(matches=rr,fit_pnp_inliers=inrows,C=C,map_source=asset(G/'landmarks'/('G01_'+video+'.npz')),map_ancestry='native005 map transformed frozenRoMa;18crossRGB mergedUID only;005 native fixedXYZ diagnostics transformed withcandidateH',features_N=len(f['xy']))

def main():
 g='G01';old=load(N/'config/G01_INITIAL_CAMERAS.json');vs=[];root=N/'registration/G01/NATIVE005_EXTENSION';root.mkdir(parents=True,exist_ok=True);save('config/NATIVE005_EXTENSION_PROTOCOL.json',dict(reason='firstpass omitted existing980native005RGBlandmarks; restore audited authorizedinput, not tuning basedHERO',source=asset(G/'landmarks/G01_005.npz'),same_thresholds=True,same_algorithms=True,common_identity='018crossRGBlinks from021; noNN',GT=False,newHERO_read=False));snapshot_read([Path(__file__),N/'code/register.py',N/'config/NATIVE005_EXTENSION_PROTOCOL.json'],'NATIVE005_EXTENSION_CODE.json')
 for v in old:
  if v['role']!='FIT'or v['video']=='004':vs.append(v);continue
  dest=root/(v['id']+'_INITIAL.json');rgbp=root/(v['id']+'_RGB.json')
  if dest.exists():vs.append(load(dest));continue
  try:
   ob=observe(v);banks=[pnp_bank(v,video)for video in (['005']if v['video']=='005'else['004','005'])];numeric=[b for b in banks if b['C']is not None];rr=min(numeric,key=lambda x:score(np.array(x['C']),ob,x))if numeric else banks[0];save(str(rgbp.relative_to(N)),rr);poses=[];v2=v|dict(rgb_geometry_path=str(rgbp));
   if rr['C']is not None and len(ob['q_train'])>=20:
    raw=load(N/'registration'/v['id']/'RF_MULTISOLUTION.json');rings=raw['ring_candidates'];aa=yaw_resolve(rings,rr,ob);cs=[dict(C=x[0],FIT_objective=x[1],source='originalRF5D_native005RGB_yaw')for x in aa];cs.append(dict(C=rr['C'],FIT_objective=score(np.array(rr['C']),ob,rr),source='native005_REAL_PNP_LM'));ch=min(cs,key=lambda c:c['FIT_objective']);C=np.array(ch['C']);v2.update(C=C,status='NUMERIC_RGB_REGISTERED',candidate_source=ch['source'],FIT_objective=ch['FIT_objective'],Ring=physical(v,C,ob),RGB_inliers_N=len(rr['fit_pnp_inliers']),RGB_matches_N=len(rr['matches']))
   save(str(dest.relative_to(N)),v2);vs.append(v2);print('NATIVE005_EXTENSION',v['id'],len(rr['fit_pnp_inliers']),flush=True)
  except Exception as e:vs.append(v|dict(extension_error=repr(e)));print('EXT_FAIL',v['id'],repr(e),flush=True)
 selected=select_for_BA(vs)
 for mode in ['SHARED_SE3','JOINT_FULL6']:
  b=Bundle(g,vs,mode,selected);b.label=mode+'_NATIVE005';r=b.run()
 poses=r['poses'];save('registration/G01/NATIVE005_EXTENSION/PRIMARY_POSES.json',dict(poses=poses,selection='same fixed JOINT_FULL6 route, extended actualnative005RGBinput, noheldorHEROselection'))
 freeze('provenance/G01_NATIVE005_CAMERAS_FROZEN_BEFORE_HELD_HERO.json',[root/'PRIMARY_POSES.json',N/'registration/G01/JOINT_FULL6_NATIVE005_FINAL.json'],GT=False,HERO=False,held=False)
 out=[]
 for v in vs:
  C=poses.get(v['id']);out.append(v|dict(C=C,**qualification(v,np.array(C)if C is not None else None)))
 save('config/G01_CAMERAS_WITH_NATIVE005.json',out);print('NATIVE005_CAMERA_COMPLETE',len(out),'formal',sum(v['formal']for v in out),flush=True)
if __name__=='__main__':main()
