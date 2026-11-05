"""Post-run numerical audit only. No optimizer, GT or candidate-model selection."""
from p3d import *
def main():
    guard_optimizer();c=Case('real');rows=[]
    for cid in c.fit:
        off=torch.zeros_like(c.base.verts_packed(),requires_grad=True);m=c.base.offset_verts(off);fr=c.fragments(m,cid);loss=c.aware(fr,cid)
        gz,gd=torch.autograd.grad(loss,[fr.zbuf,fr.dists],retain_graph=True)
        viaz=torch.autograd.grad(fr.zbuf,off,grad_outputs=gz,retain_graph=True)[0];viad=torch.autograd.grad(fr.dists,off,grad_outputs=gd,retain_graph=True)[0];full=torch.autograd.grad(loss,off)[0]
        flat=int(full.abs().argmax());vi,axis=divmod(flat,3);fd=[]
        for h in[1e-4,1e-5]:
            vals=[]
            for sg in[-1,1]:
                delta=torch.zeros_like(off);delta[vi,axis]=sg*h
                with torch.no_grad():vals.append(float(c.loss(c.base.offset_verts(delta),cid,'RingAware')))
            fd.append(dict(h_normalized=h,h_mm=h*c.scale,minus_loss=vals[0],plus_loss=vals[1],central_derivative=(vals[1]-vals[0])/(2*h),autodiff=float(full[vi,axis])))
        d=c.views[cid];P=c.V;pc=(P-d['T'][:3,3])@d['T'][:3,:3];q=pc@d['Ksmall'].T;uv=q[:,:2]/q[:,2:];tr=uv[c.F];area=abs(np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]))/2
        top=torch.topk(gz.abs().flatten(),20).indices;ids=fr.pix_to_face.flatten()[top].detach().cpu().numpy();weights=gz.flatten()[top].detach().cpu().numpy();depths=fr.zbuf.flatten()[top].detach().cpu().numpy()
        rows.append(dict(view=cid,loss=float(loss.detach()),full_gradient_norm=float(full.norm()),depth_path_gradient_norm=float(viaz.norm()),distance_path_gradient_norm=float(viad.norm()),depth_output_gradient_norm=float(gz.norm()),distance_output_gradient_norm=float(gd.norm()),max_vertex=vi,max_axis=axis,finite_differences=fd,top_depth_faces=[dict(face=int(i),dLoss_dz=float(w),depth=float(z),projected_area_px2=float(area[i])if i>=0 else None)for i,w,z in zip(ids,weights,depths)],gradient_sum_residual=float((full-viaz-viad).norm())))
    # Fixed stage history, no intermediate model chosen as replacement.
    histories=[]
    for arm in['Baseline','RingAware']:
        rr=list(csv.DictReader((R/'metrics'/('real_'+arm+'_TRAINING.csv')).open()))
        histories.append(dict(arm=arm,first_step=rr[0],last_step=rr[-1],first_gradient_over_1e3_step=next((int(r['step'])for r in rr if float(r['full_vertex_gradient_norm'])>1e3),None)))
    result=dict(rows=rows,histories=histories,GT_access=False,optimizer_steps=0,original_finite_nonzero_gradient_gate_inadequate=True,formal_project_rerun=False,conclusion='Ring-aware z-buffer backward is numerically explosive on actual grazing faces, while original silhouette-distance path remains finite at ordinary scale. The prior gate checked finite/nonzero only and did not certify gradient correctness or magnitude. This is an engineering failure, not evidence against silhouette optimization as a scientific route.')
    save('metrics/NUMERICAL_STABILITY_DIAGNOSIS.json',result)
    print([(r['view'],r['depth_path_gradient_norm'],r['distance_path_gradient_norm'],r['finite_differences'])for r in rows],flush=True)
if __name__=='__main__':main()
