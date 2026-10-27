"""Finite identifiability profile, not a new accepted registration optimizer."""
from registration import *
def main():
    old=load(ICF/'inputs/H_frozen.json');center=float(np.angle(np.mean([np.exp(1j*np.arctan2(np.array(x['H'])[1,0],np.array(x['H'])[0,0]))for x in old])));angles=np.degrees(center)+np.linspace(-10,10,11);save('provenance/D1_YAW_PROFILE_BEFORE_COMPUTE.json',dict(source_sha256=sha(Path(__file__)),reason='All free GICP endpoints crossed Ring bounds; test remaining yaw under exact Ring center/normal, not repeat failed fit or select by RGB',angles_degrees=angles,GT_used=False,acceptance_unchanged=True))
    p4=np.load(R/'local_results/background/004_working.npz')['XYZ_mm'];p5=np.load(R/'local_results/background/005_working.npz')['XYZ_mm'];n4=np.asarray(cloud(p4).normals);n5=np.asarray(cloud(p5).normals);rows=[]
    for angle in angles:
        H=np.eye(4);H[:3,:3]=Rotation.from_euler('z',angle,degrees=True).as_matrix();a=pair_stats(p5,p4,H,n4);b=pair_stats(p4,p5,np.linalg.inv(H),n5);rows.append(dict(yaw_degrees=angle,H_005_to_004=H,forward=a,reverse=b,objective=a['point_to_plane_mm']['median']+b['point_to_plane_mm']['median'],status='RING_FIXED_DIAGNOSTIC_NOT_CERTIFIED'))
    v=np.array([x['objective']for x in rows]);best=int(v.argmin());near=np.array(angles)[v<=v.min()*1.05];save('metrics/D1_yaw_observability.json',dict(rows=rows,best_index=best,near_minimum_5percent_angle_span_deg=float(np.ptp(near))if len(near)else None,best_at_search_boundary=best in [0,len(rows)-1],minimum_objective=float(v.min()),no_claim_of_unique_pose=True,used_for_D2_acceptance=False));csvsave('metrics/D1_yaw_observability.csv',rows);print('YAW_PROFILE',best,angles[best],float(v.min()),'span',float(np.ptp(near)),flush=True)
if __name__=='__main__':main()
