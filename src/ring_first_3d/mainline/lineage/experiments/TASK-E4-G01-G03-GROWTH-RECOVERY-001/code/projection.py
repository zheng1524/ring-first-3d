"""Growth-only acceptance around the unchanged 002 correspondence generator."""
import numpy as np
from projection_gate import ProjectionGate
from ring_first_3d.multisurface.geometry import scene,closest

class RecoveryProjection(ProjectionGate):
    def setup(self,original,initial,configuration,support):
        self.original=original;self.configuration=configuration;self.support=set(support)
        self.original_pairs=self.rebuild(original,True);self.initial=self.rebuild(initial)
        centers=original['V'][original['F']].mean(1)
        self.keep_face=np.linalg.norm(centers-np.array(configuration['exit_reference']),axis=1)>configuration['attachment_region_radius_mm']
    def assess(self,body,fresh):
        reasons=[];changes=[];new_support=[];old_engine=scene(self.original['V'],self.original['F'])
        cent=body['V'][body['F']].mean(1);Q,_,oldid=closest(old_engine,cent)
        old_face=(body['face_operand']==0)&(np.linalg.norm(Q-cent,axis=1)<1e-4)
        retained=old_face&self.keep_face[oldid]
        initial_bad=self.protect(fresh)
        if initial_bad:reasons.append('INITIAL_GOOD_VIEW_REGRESSION')
        for v in self.views:
            cid=v['id'];old=self.original_pairs[cid];new=fresh[cid];a=old['stats'];b=new['stats']
            # All original views stay present, including low-IoU and difficult005.
            di=b['IoU']-a['IoU'];db=b['Boundary_MAE_px']-a['Boundary_MAE_px']
            if di<-.01-1e-12 or db>1.+1e-12:reasons.append('PER_VIEW_PROTECTION')
            op=old['pairs'];npair=new['pairs']
            old_keep=op['accepted']&self.keep_face[np.maximum(op['face'],0)]
            new_keep=npair['accepted']&retained[np.maximum(npair['face'],0)]
            oldN=int(old_keep.sum());newN=int(new_keep.sum())
            if oldN and newN<.7*oldN:reasons.append('RETAINED_SURFACE_COVERAGE_COLLAPSE')
            exposed=npair['accepted']&(body['face_operand'][np.maximum(npair['face'],0)]==1)
            score=(1-b['IoU']+.01*b['Boundary_MAE_px'])-(1-a['IoU']+.01*a['Boundary_MAE_px'])
            improved=(di>1e-5 or db<-.01)and score< -1e-6
            if cid in self.support and improved and exposed.sum()>=2:new_support.append(dict(id=cid,video=v['video'],new_pairs=int(exposed.sum())))
            changes.append(dict(id=cid,video=v['video'],original_support=cid in self.support,IoU_delta=float(di),Boundary_MAE_delta_px=float(db),
                data_score_delta=float(score),retained_old_pairs=oldN,retained_new_pairs=newN,new_exposed_pairs=int(exposed.sum()),old=a,new=b))
        # Frozen support set is not searched again. Need actual improved evidence in both videos.
        if len(new_support)<3 or {v['video']for v in new_support}!={'004','005'}:reasons.append('NO_NEW_MULTIVIEW_EXPOSED_CORRESPONDENCES')
        for video in ['004','005']:
            vv=[c for c in changes if c['original_support']and c['video']==video]
            weighted=sum(self.weights[c['id']]*c['data_score_delta']for c in vv)
            if weighted>=-1e-6:reasons.append('SUPPORT_VIDEO_DATA_NOT_IMPROVED_'+video)
        gain=self.regional_score(fresh)-self.regional_score(self.original_pairs)
        if gain>=-1e-6:reasons.append('FRESH_2D_DATA_NOT_IMPROVED')
        return sorted(set(reasons)),dict(views=changes,new_support_views=new_support,initial_protection_failures=initial_bad,
            data_score_delta=float(gain),coverage_excludes_replaced_root=True,hidden_embedded_faces_in_external_mesh=0)

