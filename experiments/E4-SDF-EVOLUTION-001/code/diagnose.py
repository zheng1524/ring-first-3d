"""Local failure mechanism and physical (not just field-value) HERO protection."""
from solver import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.optimize import brentq
def main():
    a=np.load(R/'local_results/INITIAL/FIELD.npz');b=np.load(R/'local_results/FINAL/FIELD.npz');g=Field(a['origin'],a['shape'],float(a['h']));e=Evolution(g,a['phi'],Data());H=e.hero[e.eligible][e.protect];r0=mesh_scene(a['V'],a['F']);r1=mesh_scene(b['V'],b['F']);d0=abs(signed(r0,H));d1=abs(signed(r1,H))
    prot=dict(N=len(H),initial_actual_mesh_distance_mm=stats(d0),final_actual_mesh_distance_mm=stats(d1),individual_worse_by_gt_0p05mm_N=int((d1-d0>.05).sum()),max_individual_distance_increase_mm=float(max(d1-d0)),worst_point_mm=H[np.argmax(d1)],field_contract_does_not_equal_exact_mesh_distance=True)
    m=trimesh.Trimesh(b['V'],b['F'],process=False);ang=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',m.face_normals[m.face_adjacency[:,0]],m.face_normals[m.face_adjacency[:,1]]),-1,1)));worst=np.argsort(ang)[-12:];sharp=[dict(angle_deg=float(ang[i]),face_ids=m.face_adjacency[i],position_mm=m.vertices[m.face_adjacency_edges[i]].mean(0),edge_length_mm=float(np.linalg.norm(np.diff(m.vertices[m.face_adjacency_edges[i]],axis=0))),two_face_area_mm2=float(m.area_faces[m.face_adjacency[i]].sum()))for i in worst]
    log=load(R/'metrics/UPDATE_LOG.json');rejected=[r for r in log if not r['accepted']];it=max([r['iteration']for r in rejected],default=1);bi=max([r['iteration']for r in log if r['accepted']and r['iteration']<it],default=0);base='ACCEPTED_%02d'%bi if bi else'INITIAL';basearr=np.load(R/'local_results'/base/'FIELD.npz');delta=np.load(R/'local_results'/('iter_%02d_PROPOSAL.npz'%it))['delta'];motion=[];grad=g.gradient(b['phi']);gn=np.linalg.norm(grad,axis=1)
    for alpha in protocol()['line_search']:
        v,f=g.mesh(basearr['phi']+alpha*delta);rt=mesh_scene(v,f);di=rt.compute_distance(o3d.core.Tensor(basearr['V'].astype(np.float32))).numpy();j=np.argmax(di);P=basearr['V'][j];B,_=g.basis(P[None])
        closest=rt.compute_closest_points(o3d.core.Tensor(P[None].astype(np.float32)))['points'].numpy()[0];direction=g.query_gradient(basearr['phi'],P[None])[0];direction/=np.linalg.norm(direction);candidate=basearr['phi']+alpha*delta;ts=np.linspace(-.4,.4,401);vals=g.value(candidate,P[None]+ts[:,None]*direction);roots=[]
        for k in np.flatnonzero(vals[:-1]*vals[1:]<0):roots.append(float(brentq(lambda t:g.value(candidate,(P+t*direction)[None])[0],ts[k],ts[k+1])))
        exact_grad=np.array([(g.value(basearr['phi'],(P+np.eye(3)[k]*1e-5)[None])[0]-g.value(basearr['phi'],(P-np.eye(3)[k]*1e-5)[None])[0])/2e-5 for k in range(3)])
        motion.append(dict(iteration=it,base_stage=base,alpha=alpha,max_base_to_candidate_mm=float(di[j]),worst_base_point_mm=P,selected_cell_gradient=g.query_gradient(basearr['phi'],P[None])[0],exact_trilinear_centered_gradient=exact_grad,local_field_delta_mm=float((B@(alpha*delta))[0]),closest_candidate_point=closest,field_value_at_closest_candidate_triangle_mm=float(g.value(candidate,closest[None])[0]),field_value_at_old_mesh_point_mm=float(g.value(basearr['phi'],P[None])[0]),trilinear_field_roots_on_old_normal_mm=roots))
    near=abs(b['phi'])<.5;low=near&(gn<.35)
    save('metrics/LOCAL_STABILITY_DIAGNOSIS.json',dict(HERO_protection=prot,sharp_edges=sharp,terminal_proposal_motion=motion,near_surface_nodes_N=int(near.sum()),near_surface_gradient_lt_0p35_N=int(low.sum()),all_near_surface_min_gradient=float(gn[near].min()),interpretation='Field gradient percentile gate does not certify every local zero neighborhood. Inspect raw meshes, actual HERO distances and candidate rejections; neither closure nor improved silhouette certifies true/smooth anatomy.'))
    # Exact same local window, actual meshes only; no region deletion or smoothing.
    center=np.mean([r['worst_base_point_mm']for r in motion],axis=0);lo=center-1;hi=center+1;fig,axs=plt.subplots(1,3,figsize=(13,4.5),subplot_kw={'projection':'3d'})
    V0,F0=g.mesh(basearr['phi']+delta)
    for ax,(V,F,name)in zip(axs,[(basearr['V'],basearr['F'],base),(V0,F0,'Proposal %d, alpha=1 (diagnostic)'%it),(a['V'],a['F'],'INITIAL same local window')]):
        t=V[F];sel=((t.max(1)>=lo)&(t.min(1)<=hi)).all(1);mesh=trimesh.Trimesh(V,F,process=False);col=np.tile([.2,.57,.8],(sel.sum(),1));ax.add_collection3d(Poly3DCollection(t[sel],facecolors=col,edgecolors=(.1,.1,.1,.2),linewidth=.25));ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=name);ax.set_box_aspect([1,1,1]);ax.view_init(22,-75)
    fig.suptitle('Actual local geometry instability, same 2 mm window; rejected state is NOT final output');fig.tight_layout();fig.savefig(R/'figures/full/FAILED_PROPOSAL_LOCAL.png',dpi=170);plt.close(fig)
    print('LOCAL_DIAGNOSIS',prot,'terminal',motion,flush=True)
if __name__=='__main__':main()
