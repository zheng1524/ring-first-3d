from gap017 import *
def main():
    t=load(R/'config/PROTOCOL.json')['thresholds'];K=np.array([[150.,0,23.5],[0,150.,23.5],[0,0,1.]]);T=np.eye(4);yy,xx=np.mgrid[:48,:48];ray=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)]@np.linalg.inv(K).T;lab=np.ones((48,48),np.uint8);lab[[0,-1]]=0;lab[:,[0,-1]]=0;rows=[]
    for deg in [0.,65.,80.]:
        n=np.array([np.sin(np.radians(deg)),0,np.cos(np.radians(deg))]);z=(20*n[2]/(ray@n)).reshape(48,48);P,F,uv,_=native_grid(z,lab,K,T);g,e=gap_edges(z,lab,K,T,P,F,uv,t);assert len(g)==0;rows.append(dict(control='continuous_perspective_plane_'+str(deg),confirmed_false_gaps=len(g),tested=len(e),passed=True))
    z=np.where(xx<24,20.,23.);P,F,uv,_=native_grid(z,lab,K,T);g,e=gap_edges(z,lab,K,T,P,F,uv,t);assert len(g)>0;rows.append(dict(control='two_flat_layers_sharp_depth_step',confirmed_gap_edges=len(g),tested=len(e),passed=True,interpretation='gap-invalid interpolation faces; both supported endpoint layers remain valid'))
    z=np.full((48,48),20.);z[20,20]=30.;P,F,uv,_=native_grid(z,lab,K,T);g,e=gap_edges(z,lab,K,T,P,F,uv,t);assert len(g)==0;rows.append(dict(control='unsupported_single_pixel_spike',confirmed_gap_edges=0,passed=True,interpretation='no independent support for spike endpoint; remains uncertain, not auto-deleted'))
    save('metrics/TWO_SIDED_CONTROL_TESTS.json',dict(passed=True,tests=rows,GT_used=False));print('TWO_SIDED_TESTS_PASS',rows,flush=True)
if __name__=='__main__':main()
