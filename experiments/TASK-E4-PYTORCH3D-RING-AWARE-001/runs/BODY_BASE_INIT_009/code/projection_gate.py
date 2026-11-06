"""Independent pre-optimization camera audit; native GT permitted only in this process."""
from p3d import *

def iou(a,b):return float((a&b).sum()/max(1,(a|b).sum()))
def cd(a,b):
    a=contour(a);b=contour(b)
    return stats(np.r_[cKDTree(a).query(b)[0],cKDTree(b).query(a)[0]])if len(a)and len(b)else stats([])
def main():
    assert load(R.parent/'VISIBILITY_ORDER_REPAIR_001/metrics/PROJECTION_GATE.json')['passed']
    rows=[]
    for name in load(R/'config/PROTOCOL.json')['cases']:
        c=Case(name);rs=scene(c.ringV,c.ringF);bs=scene(c.V,c.F)
        for cid,d in c.views.items():
            K=d['Ksmall'];T=d['T'];P=c.V[::max(1,len(c.V)//2000)]
            cv=(P-T[:3,3])@T[:3,:3];q=cv@K.T;uv=q[:,:2]/q[:,2:]
            pp=d['cam'].transform_points_screen(tensor((P-c.center)/c.scale))[0:len(P),:2].detach().cpu().numpy()-.5
            point_error=float(abs(uv-pp).max())
            with torch.no_grad():
                bz=c.hard(c.base,cameras=d['cam']).zbuf[0,...,0].cpu().numpy()*c.scale
                rz=c.hard(c.ring,cameras=d['cam']).zbuf[0,...,0].cpu().numpy()*c.scale
            oz=cast(bs,K,T,180,320);orz=cast(rs,K,T,180,320)
            good=(bz>0)&np.isfinite(oz); interior=cv2.erode(good.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
            depth_error=stats(bz[interior]-oz[interior]);ringdepth=stats(rz[(rz>0)&np.isfinite(orz)]-orz[(rz>0)&np.isfinite(orz)])
            hard_iou=iou(bz>0,np.isfinite(oz));ring_iou=iou(rz>0,np.isfinite(orz))
            nativez=cast(rs,d['K'],T,360,640);lab=d['labels'];ringpred=np.isfinite(nativez)&(lab!=1);ringobs=lab==2
            boundary=cd(ringpred,ringobs)
            cad_pass=boundary['median'] is not None and boundary['median']<=3. and boundary['p95']<=10.
            row=dict(case=name,view=cid,role=d['meta']['role'],point_max_px=point_error,body_P3D_Open3D_IoU=hard_iou,Ring_P3D_Open3D_IoU=ring_iou,body_depth_mm=depth_error,Ring_depth_mm=ringdepth,CAD_observed_contour_px=boundary,CAD_observed_IoU=iou(ringpred,ringobs),projection_pass=point_error<.001 and hard_iou>=.98 and ring_iou>=.98 and depth_error['median']<.01,CAD_observed_pass=cad_pass)
            if name.startswith('virtual'):
                gt=np.load(OLD/'audit_only/NATIVE_CAD_GT.npz' if name=='virtual_IIa' else R/'audit_only'/name/'GT.npz');gz=cast(scene(gt['V'],gt['F']),K,T,180,320)
                with torch.no_grad():pz=c.hard(mesh((gt['V']-c.center)/c.scale,gt['F']),cameras=d['cam']).zbuf[0,...,0].cpu().numpy()*c.scale
                target=d['small']==1;visible=(pz>0)&((pz<rz)|(rz<0));oracle=np.isfinite(gz)&(gz<orz)
                # Validate native Blender labels at native resolution, avoiding label-resize aliasing.
                rot=T[:3,:3].T;tv=(rot@c.center-rot@T[:3,3])/c.scale;Ke=d['K'].copy();Ke[:2,2]+=.5
                nativecam=cameras_from_opencv_projection(tensor(rot[None]),tensor(tv[None]),tensor(Ke[None]),tensor([[360,640]]))
                nativehard=MeshRasterizer(raster_settings=RasterizationSettings(image_size=(360,640),blur_radius=0.,faces_per_pixel=1,max_faces_per_bin=max(len(gt['F']),len(c.ringF))+1))
                with torch.no_grad():
                    ngz=nativehard(mesh((gt['V']-c.center)/c.scale,gt['F']),cameras=nativecam).zbuf[0,...,0].cpu().numpy()*c.scale
                    nrz=nativehard(c.ring,cameras=nativecam).zbuf[0,...,0].cpu().numpy()*c.scale
                ngt=(ngz>0)&((ngz<nrz)|(nrz<0))
                row.update(GT_P3D_Open3D_visible_IoU=iou(visible,oracle),GT_Blender_resized_label_IoU_diagnostic=iou(visible,target),GT_Blender_native_visible_IoU=iou(ngt,lab==1))
                row['GT_projection_pass']=row['GT_P3D_Open3D_visible_IoU']>=.98 and row['GT_Blender_native_visible_IoU']>=.98
            rows.append(row)
        print(name,rows[-len(c.views):],flush=True)
    save('metrics/PROJECTION_GATE.json',dict(rows=rows,passed=all(r['projection_pass']and r.get('GT_projection_pass',True)for r in rows),native_K_unchanged=True,opencv_to_p3d='official conversion + explicit center-to-edge half-pixel; same physical ray'))
    table('metrics/PROJECTION_GATE.csv',rows)
if __name__=='__main__':main()
