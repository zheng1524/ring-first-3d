"""Read-only scientific review/export after Runner completion; never trains/selects.

Hard links preserve disk space. Existing linked artifacts are never rewritten.
"""
from pathlib import Path
import os,sys,json,hashlib,shutil,csv,html,collections,subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

TD=Path(__file__).resolve().parents[1]
ROOT=TD.parents[1]
RUN=TD/'runs/STRUCTURAL_004'
VIS=TD/'visualization'

def read(p):return json.loads(Path(p).read_text())
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Never overwrite '+str(p))
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stage(name):
    paths=[p for p in (RUN/'attempts').glob('*-'+name+'-*') if not p.name.startswith('.')]
    assert len(paths)==1,(name,paths)
    assert read(paths[0]/'result.json')['status']=='PASS'
    return paths[0]
def link(src,dst):
    src,dst=Path(src),Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert digest(src)==digest(dst),(src,dst)
    else:os.link(src,dst)
def csvout(name,rows):
    with (TD/name).open('x',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def projection(row,role,key='IoU'):
    return float(np.mean([v[key] for v in row['projection'] if v['role']==role]))

def main():
    assert read(stage('artifacts')/'result.json')['status']=='PASS'
    publication=stage('G4_visualize')
    VIS.mkdir(exist_ok=False)
    for folder in ['figures','meshes','evidence']:
        shutil.copytree(publication/folder,VIS/folder,copy_function=os.link)
    for name in ['C0_METRICS.json','REAL_BODY_METRICS.json','REAL_HERO_METRICS.json','INITIALIZATION_AUDIT.json','DEFORM_ONLY_UPDATES.json','DEFORM_GROW_UPDATES.json']:
        link(publication/name,VIS/name)
    body=stage('G5_real_update');he=stage('G6_hero_relocate');ev=stage('G7_real_evaluate')
    bodyrows=[];updates=[];trace=[];hero_audit=[]
    # Complete per-view traces at four stages; every other stage remains in Runner.
    for case in ['G01','G03','G05']:
        for arm in ['DEFORM_ONLY','DEFORM_GROW']:
            src=body/case/arm;dest=VIS/'evidence/REAL'/case/arm
            for n in ['UPDATES.json','INITIAL.npz','FINAL.npz']:link(src/n,dest/n)
            for n in ['STEP_000','STEP_012','STEP_024','STEP_035','FINAL_CORRESPONDENCES']:
                shutil.copytree(src/n,dest/n,copy_function=os.link)
            u=read(src/'UPDATES.json');initial=np.load(src/'INITIAL.npz');final=np.load(src/'FINAL.npz')
            displacement=np.linalg.norm(final['V'][:len(initial['V'])]-initial['V'],axis=1)
            rejected=collections.Counter(z for r in u['records'] for q in r['rejections'] for z in q['reasons'])
            updates.append(dict(case=case,arm=arm,accepted_deformations=u['accepted_deformations'],accepted_growth=u['accepted_growth'],initial_V=len(initial['V']),final_V=len(final['V']),displacement_MAE_mm=float(displacement.mean()),displacement_P95_mm=float(np.quantile(displacement,.95)),displacement_max_mm=float(displacement.max()),rejections=dict(rejected),growth=u['growth']))
            # Every view's gradient and actual common delta are preserved; one
            # explicit accepted Face/bary record per view makes the chain readable.
            for step in ['STEP_000','STEP_012','STEP_024','STEP_035']:
                mesh=np.load(src/step/'BODY_AFTER.npz')
                for p in sorted((src/step).glob('*_GRADIENT.npz')):
                    view=p.name[:-len('_GRADIENT.npz')];g=np.load(p);a=np.load(src/step/(view+'.npz'));ids=np.flatnonzero(a['accepted'])
                    if not len(ids):continue
                    j=int(ids[np.argmax(a['distance_px'][ids])]);face=int(a['face'][j]);vertices=mesh['F'][face]
                    trace.append(dict(case=case,arm=arm,step=step,view=view,face=face,vertices=vertices.tolist(),bary=a['bary'][j].tolist(),target_uv=a['target_uv'][j].tolist(),projected_uv=a['projected_uv'][j].tolist(),residual_px=float(a['distance_px'][j]),per_view_gradient_on_face_vertices=g['gradient'][vertices].tolist(),actual_shared_delta_mm=g['actual_shared_vertex_delta'][vertices].tolist(),per_view_gradient_norm=float(np.linalg.norm(g['gradient'])),total_descent_work=float(g['descent_work'].sum()),evidence=str((dest/step/p.name).relative_to(TD))))
        for method in ['M0','RAY_INITIAL','RAY_UPDATED']:
            for p in sorted((he/case/method).glob('*.npz')):
                link(p,VIS/'evidence/HERO'/case/method/p.name)
                if 'CORRESPONDENCES' in p.name:continue
                m=np.load(p);m0=np.load(he/case/'M0'/p.name)
                assert np.array_equal(m['F'],m0['F']) and np.array_equal(m['uv'],m0['uv'])
                hero_audit.append(dict(case=case,method=method,source=p.stem,V=len(m['V']),F=len(m['F']),source_topology_identical=True,source_uv_identical=True,sha256=digest(p)))
        for p in (ev/case).glob('*'):link(p,VIS/'evidence/GT_EVALUATION_ONLY'/case/p.name)
    for name,st in [('BODY_PREDICTIONS_FROZEN.json',body),('HERO_PREDICTIONS_FROZEN.json',he)]:link(st/name,TD/'evidence'/name)
    for n in ['G01_FIXED_OVERLAPS.json','G03_FIXED_OVERLAPS.json','G05_FIXED_OVERLAPS.json']:link(ev/n,VIS/n)
    save(TD/'REAL_UPDATE_SUMMARY.json',updates);save(TD/'evidence/2D_TO_3D_TRACE.json',trace);save(TD/'evidence/HERO_NATIVE_TOPOLOGY_AUDIT.json',hero_audit)
    for r in read(ev/'REAL_BODY_METRICS.json')['rows']:
        bodyrows.append(dict(case=r['case'],arm=r['arm'],**r['Chamfer_mm'],Fscore_0p5mm=r['Fscore_0p5mm'],GT_coverage_0p5mm=r['GT_coverage_0p5mm'],FIT_IoU=projection(r,'FIT'),HOLDOUT_IoU=projection(r,'HOLDOUT'),FIT_BF2px=projection(r,'FIT','Boundary_Fscore_at2px'),HOLDOUT_BF2px=projection(r,'HOLDOUT','Boundary_Fscore_at2px'),GT_alignment='EVALUATION_COPY_ONLY_SCALE1'))
    csvout('REAL_BODY_METRICS.csv',bodyrows)
    hrows=[]
    for r in read(ev/'REAL_HERO_METRICS.json')['rows']:
        views=r['details'].get('per_view',[])
        hrows.append(dict(case=r['case'],method=r['method'],within_N=r['within_video']['N'],within_MAE_mm=r['within_video']['MAE'],within_P95_mm=r['within_video']['p95'],within_max_mm=r['within_video']['maximum'],cross_N=r['cross_video']['N'],cross_MAE_mm=r['cross_video']['MAE'],cross_P95_mm=r['cross_video']['p95'],cross_max_mm=r['cross_video']['maximum'],HOLDOUT_IoU=float(np.mean([x['mask_IoU'] for x in r['HOLDOUT']])),HOLDOUT_recall=float(np.mean([x['mask_recall'] for x in r['HOLDOUT']])),correspondence_N=sum(x['accepted_N'] for x in views),source_vertex_N=sum(x['target_N'] for x in views),max_source_pixel_error_px=max([x['source_pixel_error_max_px'] for x in views]or[0]),max_edge_P95_fraction=max([x['edge_relative_change_P95'] for x in views]or[0]),max_axial_change_mm=max([x['axial_change_max_mm'] for x in views]or[0]),absolute_3D_accuracy='NOT_EVALUABLE'))
    csvout('REAL_HERO_METRICS.csv',hrows)
    hero_pixels(he)
    save(TD/'evidence/DELIVERY_SOURCE_BINDING.json',dict(run=str(RUN),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),publication=str(publication),publication_result_sha256=digest(publication/'result.json'),packager=str(Path(__file__)),packager_sha256=digest(__file__),mutable_predictions=False))
    print(json.dumps(dict(body=bodyrows,hero=hrows,updates=[{k:v for k,v in r.items()if k!='growth'}for r in updates]),indent=2))

def hero_pixels(he):
    # All original UVs, not downsampled 3D sketches. Rejected pixels explicitly red.
    for case in ['G01','G03','G05']:
        paths=sorted((he/case/'RAY_UPDATED').glob('*_CORRESPONDENCES.npz'))
        maximum=max(float(np.max(abs(np.load(p)['corrected_axial_mm']-np.load(p)['original_axial_mm']))) for p in paths)
        for offset in range(0,len(paths),4):
            batch=paths[offset:offset+4];fig,axes=plt.subplots(len(batch),3,figsize=(14,3*len(batch)),squeeze=False)
            for j,p in enumerate(batch):
                a=np.load(p);uv=a['source_uv'];h=int(uv[:,1].max())+1;w=int(uv[:,0].max())+1
                face=np.full((h,w),np.nan);face[uv[:,1],uv[:,0]]=np.where(a['Body_face']>=0,a['Body_face'],np.nan)
                dz=np.full((h,w),np.nan);dz[uv[:,1],uv[:,0]]=a['corrected_axial_mm']-a['original_axial_mm']
                status=np.zeros((h,w,4));status[uv[:,1],uv[:,0]]=np.where(a['accepted'][:,None],[0,.8,0,1],[1,0,0,1])
                axes[j,0].imshow(face,cmap='turbo',vmin=0);axes[j,0].set_title(p.stem.replace('_CORRESPONDENCES','')+' actual Body Face IDs')
                axes[j,1].imshow(status);axes[j,1].set_title('all source UV: accepted green / rejected red')
                im=axes[j,2].imshow(dz,cmap='coolwarm',vmin=-maximum,vmax=maximum);axes[j,2].set_title('actual axial correction mm');fig.colorbar(im,ax=axes[j,2])
                for ax in axes[j]:ax.set(xlabel='native u px',ylabel='native v px')
            fig.suptitle(case+' RAY_UPDATED: source pixel identity fixed; rejected vertices retained');fig.tight_layout();fig.savefig(VIS/'figures'/(case+'_HERO_PIXEL_%02d.png'%offset),dpi=130);plt.close(fig)

if __name__=='__main__':main()
