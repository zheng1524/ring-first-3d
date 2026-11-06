"""Dependency-free closed-section polygon area. Evaluation only, never mesh repair."""
from common import *

def section_area(V,F,z):
 m=trimesh.Trimesh(V,F,process=False);sec=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
 if sec is None:return 0.,'NO_INTERSECTION'
 loops=sec.discrete
 if not len(loops):return None,'NO_CLOSED_LOOPS'
 polys=[];areas=[]
 for line in loops:
  if np.linalg.norm(line[0]-line[-1])>1e-5:return None,'OPEN_SECTION'
  q=line[:,:2];area=.5*abs(np.sum(q[:-1,0]*q[1:,1]-q[1:,0]*q[:-1,1]));polys.append(q);areas.append(area)
 total=0.
 for i,(q,a)in enumerate(zip(polys,areas)):
  inside=sum(cv2.pointPolygonTest(p.astype(np.float32),tuple(map(float,q[0])),False)>0 for j,p in enumerate(polys)if j!=i);total+=a*(-1)**inside
 return float(total),'CLOSED_LOOP_SHOELACE_EVEN_ODD_PROXY'
def main():
 assert load(R/'assets_index/PREDICTIONS_FROZEN.json')['all_expected_finals'];checks=load(R/'metrics/EXACT_GEOMETRY.json');rows=[];test=[]
 # Analytic square-plane sanity; independent of any dataset/optimization choice.
 for L in[1.,2.,3.]:
  m=trimesh.creation.box(extents=[L,L,L]);a,status=section_area(m.vertices,m.faces,0);test.append(dict(side=L,expected_area=L*L,computed_area=a,status=status,passed=abs(a-L*L)<1e-9))
 assert all(x['passed']for x in test)
 for c in['virtual_Ip','virtual_Is','virtual_IIa']:
  g=np.load(OLD/'audit_only/NATIVE_CAD_GT.npz'if c=='virtual_IIa'else R/'audit_only'/c/'GT.npz');low=g['V'][:,2].min();high=g['V'][:,2].max()
  for arm in['P0','B','E1','E2','E3']:
   a=np.load(R/'inputs'/c/'INITIAL.npz'if arm=='P0'else R/'local_results'/c/arm/'FINAL.npz');solid=next(x['solid_geometry_valid']for x in checks if x['case']==c and x['arm']==arm and x['step']==(0 if arm=='P0'else 300))
   for z in np.linspace(low,high,25)[1:-1]:
    pp,ps=section_area(a['V'],a['F'],z);ga,gs=section_area(g['V'],g['F'],z);rows.append(dict(case=c,arm=arm,z_mm=float(z),prediction_section_area_mm2=pp if solid else None,prediction_raw_proxy_area_mm2=pp,GT_section_area_mm2=ga,prediction_solid_valid=solid,prediction_section_status=ps,GT_section_status=gs,GT_solid_caveat='Native Ip/Is self-intersection; reference section proxy, not certified Boolean'))
 table('metrics/CROSS_SECTIONS.csv',rows);save('metrics/SECTIONS.json',rows);save('metrics/SECTION_OPERATOR_AUDIT.json',dict(tests=test,implementation='trimesh triangle-plane section, closed polyline shoelace with even-odd nesting; no Shapely required',no_mesh_edit=True,virtual_GT_Ip_Is_not_certified_solid=True));print('SECTION_AUDIT_DONE')
if __name__=='__main__':main()
