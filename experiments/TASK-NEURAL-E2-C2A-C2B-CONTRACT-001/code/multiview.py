"""C2b: source traceable three-reference batches and shared per-video loss."""
from context import *
from opacity import *

def correlation_components(C,refs):
    parent={x:x for x in refs}
    def root(x):
        while parent[x]!=x:x=parent[x]
        return x
    links=[]
    for i,a in enumerate(refs):
        for b in refs[i+1:]:
            shared=sorted(set(C[a]['source_alias_hashes'])&set(C[b]['source_alias_hashes']))
            links.append(dict(A=a,B=b,shared_HERO_RGB_N=len(shared),shared_HERO_RGB_SHA256=shared))
            if shared:parent[root(b)]=root(a)
    groups={}
    for x in refs:groups.setdefault(root(x),[]).append(x)
    return list(groups.values()),links

class ThreeReferenceDataset:
    def __init__(self,scene):
        require_c2a()
        self.scene=scene;self.refs=selected()[scene]
        C={c['id']:c for c in registry()['references']};self.C=C
        if len(self.refs)!=3 or any(C[x]['scene_id']!=scene for x in self.refs):raise ValueError('EXACT_SINGLE_VIDEO_TRIPLE_REQUIRED')
        if len({C[x]['files']['RGB']['sha256']for x in self.refs})!=3:raise ValueError('DUPLICATE_RGB_NOT_NEW_VIEW')
        self.groups,self.links=correlation_components(C,self.refs)
        self.source_weights={x:1/len(g)for g in self.groups for x in g}
        self.model_key=scene+'_SHARED_POLYP_SDF'
        self.rays={x:np.load(R/f'local_results/rays/{x}.npz')for x in self.refs}
        self.domain=next(x for x in load(E1/'config/SDF_DOMAIN_CANDIDATES.json')['candidates'][scene]if x['id']=='VISIBLE_ROI_CENTER_ENVELOPE')

    def conflict_weights(self):
        """All directed pairs of this triple; fixed native-Z consistency rule."""
        records=[];out={}
        for ref in self.refs:
            z=self.rays[ref];valid=z['depth_weight']>0;pix=np.flatnonzero(valid);uv=np.c_[pix%640,pix//640];target=z['native_axial_Z_mm'][pix]
            P=unproject(target,z['c2w_mm'],uv,z['K']);seen=np.zeros(len(pix),int);conflict=np.zeros(len(pix),int)
            for other in self.refs:
                if ref==other:continue
                b=self.rays[other];xy,Z=vis.project_camera(P,b['K'],b['c2w_mm']);good=np.isfinite(xy).all(1)&(Z>0);px=np.zeros_like(xy,int);px[good]=np.floor(xy[good]+.5).astype(int)
                good&=(px[:,0]>=0)&(px[:,0]<640)&(px[:,1]>=0)&(px[:,1]<360);ii=np.flatnonzero(good);jj=px[ii,1]*640+px[ii,0]
                usable=b['depth_weight'][jj]>0;ii=ii[usable];jj=jj[usable]
                dz=Z[ii]-b['native_axial_Z_mm'][jj];tau=np.maximum(.5,3*Z[ii]/min(b['K'][0,0],b['K'][1,1]));bad=abs(dz)>tau
                seen[ii]+=1;conflict[ii]+=bad
                records.append(dict(scene=self.scene,A=ref,B=other,source_depth_eligible_N=len(pix),comparison_N=len(ii),conflict_N=int(bad.sum()),conflict_fraction=float(bad.mean())if len(bad)else None,
                    axial_difference_mm=stats(dz),threshold='max(0.5mm,3 pixel footprints)',not_GT=True))
            weight=np.zeros(360*640,np.float32);weight[pix]=np.where(conflict>0,.25,1.)
            out[ref]=dict(pixel_weight=weight,eligible_pixel=pix,comparison_N=seen,conflict_N=conflict)
        return out,records

    def batch(self,conflicts,iteration=0):
        cfg=load(R/'config/C2_CONTRACT.json');blocks=[]
        for ref in self.refs:
            z=self.rays[ref];picks=[]
            sampling=z['sampling_class'];importance=[];regions=[];quotas=load(R/'config/RA_ALIGNED_CONTRACT.json')['region_quota']
            rng=np.random.default_rng(cfg['seed']+self.refs.index(ref)+int(iteration)*len(self.refs))
            for label in range(5):
                pool=np.flatnonzero(sampling==label);n=min(quotas[label],len(pool))
                if n:
                    picks.extend(rng.choice(pool,size=n,replace=False));importance.extend([len(pool)/n]*n);regions.extend([label]*n)
            pix=np.asarray(picks);uv=np.c_[pix%640,pix//640]
            rays=vis.camera_rays(uv,z['K'],z['c2w_mm']);f=np.linalg.norm(rays[:,3:],axis=1);rgb=np.asarray(Image.open(self.C[ref]['RGB']).convert('RGB'))
            blocks.append(dict(source=ref,pixel=pix,uv=uv,origin=rays[:,:3],direction=rays[:,3:]/f[:,None],cosine=1/f,
                start=z['ROI_start_t_mm'][pix],end=z['ROI_end_t_mm'][pix],valid=z['ROI_valid'][pix],
                target_Z=z['native_axial_Z_mm'][pix],depth_weight=conflicts[ref]['pixel_weight'][pix]*np.asarray(importance),
                mask_weight=z['mask_weight'][pix]*np.asarray(importance),mask_target=z['mask_target'][pix],class_id=z['ray_class'][pix],sampling_class=np.asarray(regions),importance=np.asarray(importance),
                source_RGB=rgb[uv[:,1],uv[:,0]]/255.,HERO_native_SHA256=self.C[ref]['E1_actual_native']['sha256']))
        return blocks

def main():
    c2a=require_c2a()
    save('config/C2B_DATA_LOSS.json',dict(input_triples=selected(),per_pixel='source-visible Polyp only; conflict=0.25 else1; missing/occluded/unknown0',
        Huber_delta_mm=.5,source_weight='1/shared-HERO connected-component size, applied AFTER per-view pixel normalization',
        aggregate='sum(source_weight * per_view_Huber) / sum(source_weight)',
        sampling='RA five regions, quotas96/96/64/32/32, uniform without replacement; population/sample_N importance',
        depth_role='P_INTERIOR observations only; render misses emit NaN and are recorded, never zero-depth regression',
        synthetic_probe='one Sphere radius=0.5*fixed E1 ROI radius and center-Z offset0 per video; autograd only; no updates',
        target_dependent_scale_shift_fit=False,official_model_forward=False,GPU='NOT_GRANTED'))
    freeze('C2B_BEFORE_TEST.json',dict(C2a_gate=asset(R/'metrics/C2A_GATE.json'),C2a_commit=git(REPO,'rev-parse','HEAD')))
    checks=[];manifests=[];lossrows=[];conflictrows=[];probe_ids=[]
    def check(name,ok,detail=None):
        checks.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:
            save('metrics/C2B_DATA_GATE.json',dict(C2b='FAIL',checks=checks,CPU_contract_pass=False,GPU='NOT_GRANTED'));raise AssertionError((name,detail))
    for scene in selected():
        data=ThreeReferenceDataset(scene);conf,cc=data.conflict_weights();conflictrows+=cc;batch=data.batch(conf)
        repeated=data.batch(conf,iteration=0);next_batch=data.batch(conf,iteration=1)
        check('seeded batch replay exact '+scene,all(np.array_equal(a['pixel'],b['pixel'])for a,b in zip(batch,repeated)))
        check('next iteration refreshes all reference pixel samples '+scene,all(not np.array_equal(a['pixel'],b['pixel'])for a,b in zip(batch,next_batch)))
        reliability=[]
        for ref in data.refs:
            path=R/f'local_results/{ref}_depth_reliability.npz'
            np.savez_compressed(path,eligible_pixel=conf[ref]['eligible_pixel'],pixel_weight=conf[ref]['pixel_weight'],comparison_N=conf[ref]['comparison_N'],conflict_N=conf[ref]['conflict_N'])
            reliability.append(asset(path))
        save('provenance/'+scene+'_BEFORE_ANALYTIC_PROBE.json',dict(scene=scene,references=data.refs,shared_SDF_identity=data.model_key,
            source_weights=data.source_weights,reliability=reliability,loss_config=asset(R/'config/C2B_DATA_LOSS.json'),no_prediction_or_GT_used=True))
        check('three genuinely different source views '+scene,len(batch)==3 and len({b['source']for b in batch})==3)
        check('one shared SDF identity for entire triple '+scene,len({data.model_key for b in batch})==1)
        check('positive depth weights remain in every view '+scene,all((b['depth_weight']>0).sum()>=64 for b in batch))
        domain=data.domain;theta=torch.tensor([domain['ROI_radius_mm']*.5,0.],dtype=torch.float64,requires_grad=True);before=theta.detach().clone();probe_ids.append(id(theta))
        center=torch.tensor(domain['ROI_center_mm'],dtype=torch.float64)
        def raw_sdf(P):
            shift=torch.stack([theta[1]*0,theta[1]*0,theta[1]])
            return torch.linalg.vector_norm(P-center-shift,dim=-1)-theta[0]
        preds=[];targets=[];weights=[];viewids=[];sceneids=[];mask_losses=[];render_hits=[]
        for b in batch:
            q=dict(start_mm=b['start'],end_mm=b['end'],valid=b['valid'])
            pred=integrate_visible(b['origin'],b['direction'],q,raw_sdf,.08,bins=512,ray_z_cosine=b['cosine'])
            preds.append(pred['axial_depth_mm']);targets.extend(b['target_Z']);weights.extend(b['depth_weight']);viewids.extend([b['source']]*len(b['pixel']));sceneids.extend([scene]*len(b['pixel']))
            render_hits.extend(pred['render_hit'])
            check('HERO batch target belongs only to RA P_INTERIOR '+b['source'],np.all(b['depth_weight'][b['sampling_class']!=0]==0))
            check('importance correction preserves each region population '+b['source'],all(abs(b['importance'][b['sampling_class']==k].sum()-int((data.rays[b['source']]['sampling_class']==k).sum()))<1e-6 for k in range(5)))
            mask_losses.append(masked_opacity_loss(pred,dict(mask_weight=b['mask_weight'],mask_target=b['mask_target'])))
            np.savez_compressed(R/f'local_results/{b["source"]}_batch.npz',source_pixel=b['pixel'],source_uv=b['uv'],target_axial_Z_mm=b['target_Z'],depth_weight=b['depth_weight'],mask_weight=b['mask_weight'],mask_target=b['mask_target'],ray_class=b['class_id'],sampling_class=b['sampling_class'],sampling_importance=b['importance'],render_hit=pred['render_hit'],analytic_depth_mm=pred['axial_depth_mm'].detach().numpy(),source_RGB=b['source_RGB'],shared_SDF_identity=np.array(data.model_key),source_native_SHA256=np.array(b['HERO_native_SHA256']))
        prediction=torch.cat(preds);depth,per_view=shared_depth_loss(prediction,targets,weights,viewids,sceneids,source_weights=data.source_weights,render_hit=render_hits)
        total=depth+torch.stack(mask_losses).mean()
        for ref,entry in per_view.items():
            check('no source can silently disappear through render misses '+ref,entry['valid_N']>0 and entry['loss']is not None,dict(observed_N=entry['observed_N'],render_hit_N=entry['valid_N'],miss_N=entry['miss_N']))
            grad=torch.autograd.grad(entry['loss'],theta,retain_graph=True)[0]
            check('shared analytic SDF receives nonzero depth response from '+ref,bool(torch.isfinite(grad).all())and float(abs(grad).sum())>1e-10,grad.detach().tolist())
            lossrows.append(dict(scene=scene,source=ref,shared_SDF_identity=data.model_key,eligible_depth_ray_N=entry['valid_N'],
                pixel_weight_sum=entry['weight_sum'],source_dependency_weight=data.source_weights[ref],analytic_probe_depth_loss_mm=float(entry['loss'].detach()),
                observed_depth_ray_N=entry['observed_N'],render_miss_N=entry['miss_N'],
                analytic_geometry_gradient=grad.detach().tolist(),not_model_prediction=True))
        joint_grad=torch.autograd.grad(total,theta)[0]
        check('joint loss finite with finite geometry gradients '+scene,bool(torch.isfinite(total))and bool(torch.isfinite(joint_grad).all()))
        check('no parameter or weight update '+scene,torch.equal(theta.detach(),before))
        check('correlation components each have unit total source weight '+scene,all(abs(sum(data.source_weights[x]for x in g)-1)<1e-12 for g in data.groups))
        for ref in data.refs:
            c=data.C[ref];eligible=conf[ref]['eligible_pixel'];w=conf[ref]['pixel_weight'];np.savez_compressed(R/f'local_results/{ref}_depth_reliability.npz',eligible_pixel=eligible,pixel_weight=w,comparison_N=conf[ref]['comparison_N'],conflict_N=conf[ref]['conflict_N'])
        manifests.append(dict(scene=scene,coordinate_system=scene+'_LOCAL_RING_MM',references=data.refs,real_RGB_identity_N=3,
            shared_SDF_identity=data.model_key,HERO_correlation_components=data.groups,correlation_component_N=len(data.groups),source_dependency_weights=data.source_weights,
            pair_parent_links=data.links,reference_provenance=[dict(id=x,RGB=data.C[x]['files']['RGB'],Mask=data.C[x]['files']['Mask'],
                aligned_pack=data.C[x]['files']['pack'],actual_native=data.C[x]['E1_actual_native'],HERO_input_views=data.C[x]['HERO_input_views'],
                frozen_camera=data.C[x]['files']['camera_file'])for x in data.refs],
            full_source_denominators=[dict(source=x,eligible_depth_N=len(conf[x]['eligible_pixel']),conflict_weighted_N=int((conf[x]['conflict_N']>0).sum()),
                no_covisible_comparison_N=int((conf[x]['comparison_N']==0).sum()))for x in data.refs],
            sampler='RA region quotas96/96/64/32/32, seeded uniform sampling, population/sample_N correction; one joint batch includes all three sources',
            depth_loss='per-view pixel Huber -> dependency-weighted view mean; no scale/shift/GT fit',
            actual_official_SDF_forward_N=0,analytic_probe_only=True,parameters_updated=False,
            joint_analytic_loss=float(total.detach()),joint_analytic_gradient=joint_grad.tolist()))
    check('two video SDF probes are separate objects',len(set(probe_ids))==2)
    try:shared_depth_loss(torch.tensor([10.,11.]),[10.,11.],[1.,1.],['a','b'],['G01_004','G01_005']);denied=False
    except ValueError:denied=True
    check('mixed video supervision rejected',denied)
    try:shared_depth_loss(torch.tensor([float('nan')]),[10.],[1.],['a'],['G01_004']);denied=False
    except ValueError:denied=True
    check('nonfinite prediction cannot silently delete a source',denied)
    # Correlation normalization applied outside each per-view pixel mean. Test
    # duplicate-group invariance against an independent closed-form group mean.
    def grouped(names,weights):
        pred=torch.tensor([12. if x.startswith('a')else 16. for x in names],dtype=torch.float64)
        return shared_depth_loss(pred,[10.]*len(names),[1.]*len(names),names,['toy']*len(names),source_weights=weights)[0]
    a=grouped(['a1','a2','b'],dict(a1=.5,a2=.5,b=1));b=grouped(['a1','a2','a3','b'],dict(a1=1/3,a2=1/3,a3=1/3,b=1))
    expected=((2-.25)+(6-.25))/2
    check('shared-source group duplication does not increase depth evidence',abs(float(a-b))<1e-12 and abs(float(a)-expected)<1e-12,dict(two_duplicate_group=float(a),three_duplicate_group=float(b),closed_form=expected))
    table('metrics/C2B_DATA_TESTS.csv',checks);table('metrics/C2B_PER_VIEW_LOSS_RESPONSE.csv',lossrows);table('metrics/C2B_DEPTH_CONFLICTS.csv',conflictrows)
    save('provenance/C2B_DATA_MANIFEST.json',manifests)
    save('metrics/C2B_DATA_GATE.json',dict(C2b='MULTI_REFERENCE_CPU_CONTRACT_PASS_WITH_LIMITATIONS',CPU_contract_pass=True,check_N=len(checks),
        scene_N=2,physical_group_N=1,views_per_scene=3,shared_SDFs=2,cross_video_fused=False,official_model_forward_N=0,weight_update_N=0,GPU='NOT_GRANTED',
        evidence='analytic SDF autograd on true frozen camera/source-ray packets; not official MonoSDF training or prediction',
        limitations=['HERO source groups may be correlated','source conflicts retained','strict holdout0 from E1','official neural graph/sampler integration still requires an authorized runtime gate']))
    print('C2B_DATA_COMPLETE',len(checks),'checks; two isolated three-reference streams',flush=True)

if __name__=='__main__':main()
