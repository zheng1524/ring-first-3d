"""Mandatory independent mesh -> frozen camera -> Blender Mask gate."""
from renderer import *
def main():
    renderer=Renderer();rows=[];cad=np.load(R/'inputs/RING_CAD.npz');views=renderer.views
    for name,path in [('BASE',R/'inputs/BASE_SOURCE_MESH.npz'),('TARGET',R/'audit_only/NATIVE_CAD_GT.npz')]:
        ar=np.load(path);rt=scene(ar['V'],ar['F'])
        for c in views:
            d=renderer.data[c['id']];rgb=np.asarray(Image.open(R/'inputs'/(name+'__'+c['id']+'.png')));target=(rgb[:,:,0]>128)&(rgb[:,:,0]>rgb[:,:,1]);ring=rgb[:,:,1]>128;pred,z,_=renderer.project(rt,c['id']);cadpred=(d['cz'].reshape(z.shape)<z)&np.isfinite(d['cz'].reshape(z.shape));inter=(pred&target).sum();union=(pred|target).sum();a=contour(pred);b=contour(target);dd=np.r_[cKDTree(a).query(b)[0],cKDTree(b).query(a)[0]];rr=(cadpred&ring).sum()/max(1,(cadpred|ring).sum());iou=inter/max(1,union);p95=np.quantile(dd,.95)
            passed=iou>=protocol()['projection_gate']['min_IoU']and rr>=protocol()['projection_gate']['min_IoU']and p95<=protocol()['projection_gate']['max_p95_contour_px'];rows.append(dict(state=name,view=c['id'],body_IoU=float(iou),Ring_IoU=float(rr),contour=stats(dd),passed=bool(passed),pixel_convention='archived K_edge retained; K_pixel_center principal point minus .5; Open3D rays at integer pixel centers'))
            np.savez_compressed(R/'audit_only'/(name+'__'+c['id']+'_PROJECTION_GATE.npz'),Blender=target,pred=pred,Ring_Blender=ring,Ring_pred=cadpred)
    point=load(R/'metrics/BLENDER_RENDER_IDENTITY.json')['rows'];passed=all(x['passed']for x in rows)and max(x['max_point_error_px']for x in point)<.001
    save('metrics/PROJECTION_GATE.json',dict(passed=passed,backend='Blender -> Open3D fallback (PyTorch3D NOT_INSTALLED / NOT_TESTED)',PyTorch3D_gate='NOT_RUN_NOT_CLAIMED',rows=rows,point_max_error_px=max(x['max_point_error_px']for x in point),official_DMTet_derivative=load(R/'metrics/DMTET_DERIVATIVE_TEST.json'),optimization_allowed=passed));table('metrics/PROJECTION_GATE.csv',rows);print('PROJECTION_GATE',passed,[(x['state'],x['view'],x['body_IoU'],x['Ring_IoU'])for x in rows],flush=True)
    assert passed,'NO_OPTIMIZATION_BEFORE_PROJECTION_GATE'
if __name__=='__main__':main()
