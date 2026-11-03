"""Display-only perturbation copies, all original cleaned XYZ, never input edits."""
from residuals import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def main():
    ids=protocol()['B_orders']['G01_004'][:2];m=ResidualModel(ids);fig=plt.figure(figsize=(22,10));cad=ringmesh('G01_004');base=np.r_[m.data[0]['X'],m.data[1]['X'],cad.vertices];lo,hi=base.min(0),base.max(0);mid=(lo+hi)/2;L=max(hi-lo)*1.06
    specs=[('BASELINE',0.,0.),('B body tz +0.1mm',.1,0.),('B HERO bias +0.1mm',0.,.1),('B tz +0.1, bias -0.1mm',.1,-.1)]
    for j,(name,tz,bias)in enumerate(specs):
        y=np.zeros(m.p);y[2]=tz/.1;y[7]=bias/.1;T,b=m.state(y);cloud=[]
        for i in range(2):
            n=m.data[i];uv=n['native_uv'];z=n['depth'][uv[:,1],uv[:,0]].astype(float)+b[i];P=unproject(z,T[i],uv,n['Kn']);cloud.append(P)
        rows=[]
        for rr in m.records:
            if rr['kind']=='depth'and rr['i']==0:
                X=m.points(0,rr['ray'],rr['z'],T,b);uv,z=m.project(X,1,T);delta=z-rr['target_z']-b[1];rows.append(dict(X=X,delta=delta))
        for i,(elev,azim)in enumerate([(20,-65),(0,0)]):
            ax=fig.add_subplot(2,4,i*4+j+1,projection='3d')
            ax.scatter(*cloud[0].T,s=.12,c='#388ec2',alpha=.6,rasterized=True);ax.scatter(*cloud[1].T,s=.12,c='#ef922f',alpha=.6,rasterized=True)
            ax.add_collection3d(Poly3DCollection(cad.vertices[cad.faces],facecolor='black',edgecolor='none'))
            if rows:sc=ax.scatter(*rows[0]['X'].T,s=5,c=rows[0]['delta'],cmap='coolwarm',vmin=-2,vmax=2,depthshade=False)
            ax.set(xlim=(mid[0]-L/2,mid[0]+L/2),ylim=(mid[1]-L/2,mid[1]+L/2),zlim=(mid[2]-L/2,mid[2]+L/2),xlabel='X mm',ylabel='Y mm',zlabel='Z mm');ax.set_box_aspect((1,1,1));ax.view_init(elev,azim);ax.set_title(name+'\nall cleaned original point IDs retained',fontsize=10)
    fig.suptitle('G01 actual HERO conflict geometry | blue=ref08, orange=r14, black=CAD\nLarge diagnostic dots show fixed overlap signed Z_AtoB - (Z_B+b_B), color scale -2 to +2 mm. Perturbations are disposable copies.',fontsize=13);fig.tight_layout(rect=[0,.02,1,.91]);dest=R/'local_results/B_3D_Conflict_Diagnostic.png';fig.savefig(dest,dpi=140);plt.close(fig)
    save('metrics/LOCAL_GEOMETRY_DIAGNOSTIC.json',dict(path=str(dest),all_point_counts=[len(x)for x in cloud],input_changed=False,perturbed_geometry_adopted=False,controls=specs));print(dest,flush=True)
if __name__=='__main__':main()
