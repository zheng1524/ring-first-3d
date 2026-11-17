"""Actual descriptor/pixel lineage audit; no 3D-error-based identity rejection."""
from common import *
import collections
def main():
 tracks=load(R/'observations/CROSS_COMMON_TRACKS.json');allrows=[];audit=[];features={};images={};D=np.load(R/'observations/CROSS_DESCRIPTORS.npz')['descriptors'];rowidx=0;verified=0
 for t in tracks:
  ds=[];intensity=[];cells=[]
  for o in t['observations']:
   f=features.setdefault(o['view'],dict(np.load(R/'features'/(o['view']+'.npz'))));i=o['feature_id'];des=f['des'][i];assert np.array_equal(des,D[rowidx])and np.allclose(f['xy'][i],o['uv']);ds.append(des);im=images.setdefault(o['RGB_source'],cv2.imread(o['RGB_source']));p=np.rint(o['uv']).astype(int);gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);pix=int(gray[p[1],p[0]]);intensity.append(pix);cells.append((o['view'],int(p[0]//80),int(p[1]//60)));allrows.append(dict(track=t['track'],video_side=o['side'],view=o['view'],feature_id=i,u=o['uv'][0],v=o['uv'][1],descriptor_row=rowidx,descriptor_npz=str(R/'observations/CROSS_DESCRIPTORS.npz'),role=o['role'],RGB=o['RGB_source'],RGB_sha256=o['RGB_SHA'],region=o['region'],intensity=pix,direction_block=o['direction_block'],frozen_observation_weight=o['weight']*t['track_weight']));rowidx+=1
  for e in t['cross_RGB_evidence']:
   a=np.load(R/'matches'/(e['a']+'__'+e['b']+'.npz'));k=e['match_index'];assert a['RGB_RANSAC'][k]and np.array_equal(a['index_pairs'][k],[e['a_feature'],e['b_feature']]);verified+=1
  ds=np.array(ds,float);ds/=np.maximum(np.linalg.norm(ds,axis=1)[:,None],1e-12);d=(1-ds@ds.T);audit.append(dict(track=t['track'],actual_observations=len(ds),actual_RGB_RANSAC_links=len(t['cross_RGB_evidence']),descriptor_cosine_distance=stats(d[np.triu_indices(len(ds),1)]),brightness_min=min(intensity),brightness_max=max(intensity),saturated_reference_feature_N=sum(i>=245 for i in intensity),unique_view_grid_cells_N=len(set(cells)),all_material_labels=t['category'],RGB_identity='supported by descriptor plus multiframe RANSAC, not physical GT',triangulation_error_not_used_to_drop_identity=True,remaining_ambiguity='background repetitive texture and fixed-camera errors cannot be fully separated from image correspondences'))
 table('observations/CROSS_PIXEL_DESCRIPTOR_INDEX.csv',allrows);save('metrics/RGB_IDENTITY_AUDIT.json',audit);table('metrics/RGB_IDENTITY_AUDIT.csv',audit);save('provenance/OBSERVATION_IDENTITIES_VERIFIED.json',dict(epoch=time.time(),observations=rowidx,cross_links=verified,all_descriptors_exact=True,no_dynamic_identity_change=True,source=asset(Path(__file__))));print('IDENTITIES021_VERIFIED',rowidx,verified,flush=True)
if __name__=='__main__':main()
