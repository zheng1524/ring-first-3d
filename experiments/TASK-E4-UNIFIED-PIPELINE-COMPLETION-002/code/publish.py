"""Actual per-instance evidence tables and static scientific figures."""
from pathlib import Path
import csv,json,ast,shutil
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import cKDTree
import pipeline as p
from ring_first_3d.mainline.native.camera import torus_contours,observe
from ring_first_3d.mainline.native.io import save_json,sha256
T=p.TASK;VIS=T/'visualization';plt.rcParams.update({'font.size':8,'savefig.dpi':120})
helpers=[n for n in ast.parse((p.OLD/'code/visualize_final.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ['full_mesh','axes3','limits']]
exec(compile(ast.Module(body=helpers,type_ignores=[]),str(p.OLD/'code/visualize_final.py'),'exec'),globals())
def readcsv(path):return list(csv.DictReader(Path(path).open())) if Path(path).is_file() else []
def num(x):
    try:return float(x)
    except (TypeError,ValueError):return float('nan')
def fmt(x):return f'{num(x):.5f}' if np.isfinite(num(x)) else 'NaN'
def root(g,vi):return p.OLD/'runs/RF_ONLY_V1'/g/vi if p.inherited(g,vi) else p.OUT/g/vi
def camera(v):
    m=v['meta'];new=p.OUT/m['case']/m['video']/'camera'/m['id']
    return new if (new/'ADMISSION.json').exists() else root(m['case'],m['video'])/'camera'/m['id']
def status(n,N):return 'PASS' if n==N and N else 'PARTIAL' if n else 'FAIL'
def figsave(fig,path):fig.tight_layout(rect=(0,0,1,.86));fig.savefig(path);plt.close(fig)

def figures():
    assert p.read(p.OUT/'ALL_PREDICTIONS_FROZEN_BEFORE_GT.json')['all_new_training_complete']
    pointers=[]
    for c in p.cases():
        g=c['case'];ring=dict(np.load(c['static']['RING.npz']['path']));initial=dict(np.load(c['initial']['path']))
        for vi in ['004','005']:
            out=VIS/g/vi;out.mkdir(parents=True,exist_ok=True);r=root(g,vi);vv=p.instance_views(g,vi)
            if p.inherited(g,vi):
                for src in (p.OLD/'visualization'/g).glob('Figure*.png'):
                    dest=out/('FROZEN_REFERENCE_'+src.name);shutil.copy2(src,dest);pointers.append(dict(source=p.asset(src),copy=p.asset(dest),scientific_result_recomputed=False))
            for v in vv:
                m=v['meta'];cam=camera(v);ad=p.read(cam/'ADMISSION.json');a=p.check_input(v)
                if p.inherited(g,vi) and not (p.OUT/g/vi/'camera'/m['id']/'CAMERA_RESULT.json').exists():continue
                fig,axs=plt.subplots(1,3,figsize=(14,4));axs[0].imshow(a['RGB']);axs[0].contour(a['labels']==2,levels=[.5],colors='cyan');axs[0].set_title('Frozen RGB + Ring Mask')
                for ax in axs[1:]:ax.imshow(a['RGB'],alpha=.55)
                result=cam/'CAMERA_RESULT.json'
                if result.exists():
                    cr=p.read(result);C=np.array(cr['c2w_mm']);curves=torus_contours(C,a['K']);q=observe(a['labels'])['q_train'];d=cKDTree(curves.reshape(-1,2)).query(q)[0]
                    for line in curves:axs[1].plot(*line.T,c='yellow',lw=.8)
                    sc=axs[2].scatter(*q.T,c=d,s=10,vmin=0,vmax=6,cmap='magma');fig.colorbar(sc,ax=axs[2],label='Observed Ring -> CAD [px]');axs[1].set_title('RF-only final candidate '+ad['status']);axs[2].set_title(f'MAE={d.mean():.4f}px P95={np.percentile(d,95):.4f}px\nFrozen 3px MAE gate')
                else:
                    for ax in axs[1:]:ax.text(.5,.5,ad['status']+'\n'+','.join(ad['reasons']),ha='center',transform=ax.transAxes,color='red',wrap=True)
                for ax in axs:ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_xlabel('u [px]');ax.set_ylabel('v [px]')
                fig.suptitle(m['id']+' | '+m['role']+' | '+ad['status']+' | actual input '+v['cache']['sha256'][:12]);figsave(fig,out/(m['id']+'_RingFirst.png'))
            if p.inherited(g,vi):continue
            fig=plt.figure(figsize=(7,6));ax=fig.add_subplot(111,projection='3d');full_mesh(ax,ring['V'],ring['F'],'black',.6);centers=[]
            for v in vv:
                cam=camera(v)
                if not (cam/'CAMERA_RESULT.json').exists():continue
                C=np.array(p.read(cam/'CAMERA_RESULT.json')['c2w_mm']);centers.append(C[:3,3]);ad=p.read(cam/'ADMISSION.json');col='orange' if ad['status']!='PASS' else 'royalblue' if v['meta']['role']!='FIT' else 'firebrick';ax.scatter(*C[:3,3],c=col,s=22);ax.quiver(*C[:3,3],*(C[:3,2]*5),color=col,arrow_length_ratio=.2)
            axes3(ax,limits(np.concatenate([ring['V']]+[np.array(centers)] if centers else [ring['V']])));ax.set_title('Red FIT / Blue HOLDOUT / Orange rejected\nArrows: camera forward 5mm; black R10 CAD');fig.suptitle(g+'/'+vi+': own metric Ring coordinate gauge; no cross-video alignment');figsave(fig,out/'Figure1_CameraPoses.png')
            fit=[v for v in vv if v['meta']['role']=='FIT'];rep=fit[4];cid=rep['meta']['id'];a=p.check_input(rep);hero=r/'hero'/cid;fig=plt.figure(figsize=(15,4))
            ax=fig.add_subplot(141);ax.imshow(a['RGB']);ax.set_title('Frozen FIT index 4 RGB')
            if (hero/'ADMISSION.json').exists() and p.read(hero/'ADMISSION.json')['status']=='PASS':
                z=np.load(hero/'HERO_native.npz')['depth_mm'];valid=np.load(hero/'MODEL_DEPTH_VALIDITY.npz')['valid'];native=dict(np.load(hero/'RAW_NATIVE_MESH.npz'))
                ax=fig.add_subplot(142);im=ax.imshow(z,cmap='turbo',vmin=0,vmax=100);fig.colorbar(im,ax=ax,label='Axial Z [mm]');ax.set_title('Fresh official HERO\nOut of 0–100mm scale: '+str(int((z>100).sum())))
                ax=fig.add_subplot(143);ax.imshow(valid,cmap='gray',vmin=0,vmax=1);ax.set_title('Official masked-depth validity\nNot calibrated accuracy/confidence')
                ax=fig.add_subplot(144,projection='3d');full_mesh(ax,native['V'],native['F'],'orange');axes3(ax,limits(native['V']));ax.set_title(f"Actual full raw Mesh\n{len(native['V'])} vertices / {len(native['F'])} faces")
            else:
                ax=fig.add_subplot(1,4,(2,4));ax.axis('off');ax.text(.5,.5,'HERO NOT_RUN\nNo complete admitted same-video FIT camera set\nNo substitute depth',ha='center',transform=ax.transAxes)
            fig.suptitle(g+'/'+vi+' '+cid+' | original input identity, no favorable frame reselection');figsave(fig,out/'Figure2_HERO.png')
            bodies={'B0':initial}
            for arm in ['B1','B2']:
                file=r/'body'/arm/'FINAL.npz'
                if file.exists():bodies[arm]=dict(np.load(file))
            for arm,b in bodies.items():
                if arm=='B0' and len(bodies)==1:continue
                export=r/'exported'/arm;export.mkdir(parents=True,exist_ok=True)
                for key,name in [('F','WORLD_surface.ply'),('F_solid','WORLD_solid_cap.ply')]:
                    file=export/name;trimesh.Trimesh(b['V'],b[key],process=False).export(file);reload=trimesh.load(file,process=False);assert np.array_equal(reload.faces,b[key]);assert np.max(abs(reload.vertices-b['V']))<1e-5
                save_json(export/'SOURCE.json',dict(arm=arm,world_coordinates=True,GT_transform_applied=False,original_NPZ=str(Path(c['initial']['path']) if arm=='B0' else r/'body'/arm/'FINAL.npz'),inferred_base_faces=int(b['inferred_base_faces'].sum()),PLY_precision_tolerance_mm=1e-5))
            lim=limits(np.concatenate([b['V'] for b in bodies.values()]+[ring['V']]));fig=plt.figure(figsize=(15,5))
            for i,arm in enumerate(['B0','B1','B2']):
                ax=fig.add_subplot(1,3,i+1,projection='3d');full_mesh(ax,ring['V'],ring['F'],'black',.4)
                if arm in bodies:full_mesh(ax,bodies[arm]['V'],bodies[arm]['F_solid'],'#8855aa')
                else:ax.text(0,0,0,'NOT_RUN',color='red')
                axes3(ax,lim);ax.set_title(arm+' own video Ring frame; mm')
            fig.suptitle(g+'/'+vi+': real world-coordinate meshes, fixed view and mm scale; no cross-video alignment');figsave(fig,out/'Figure3_Body.png')
            metrics=readcsv(T/'metrics'/g/vi/'PER_VIEW_METRICS.csv')
            for v in vv:
                m=v['meta'];a=p.check_input(v);fig,axs=plt.subplots(1,3,figsize=(14,4))
                for ax,arm in zip(axs,['B0','B1','B2']):
                    ax.imshow(a['RGB']);ax.contour(a['labels']==1,levels=[.5],colors='lime',linewidths=.7);file=r/'evaluation/projections'/arm/(m['id']+'.npz')
                    if file.exists():
                        z=np.load(file);ax.contour(z['predicted'],levels=[.5],colors='magenta',linewidths=.8);row=next(x for x in metrics if x['arm']==arm and x['id']==m['id']);ax.set_title(arm+' IoU '+fmt(row['IoU']))
                    else:ax.set_title(arm+' NOT_EVALUABLE',color='red')
                    ax.set_xlim(0,640);ax.set_ylim(360,0);ax.axis('off')
                fig.suptitle(m['id']+' '+m['role']+' | green observed Mask; magenta actual Mesh projection; Ring unknown excluded');figsave(fig,out/(m['id']+'_BodyProjection.png'))
            aligned={a:r/'evaluation'/(a+'_GT_ALIGNED.npz') for a in bodies}
            if any(f.exists() for f in aligned.values()):
                gt=dict(np.load(c['GT']['path']));aligned={a:dict(np.load(f)) for a,f in aligned.items() if f.exists()};lim=limits(np.concatenate([gt['V']]+[a['V'] for a in aligned.values()]));fig=plt.figure(figsize=(15,5))
                for i,arm in enumerate(['B0','B1','B2']):
                    ax=fig.add_subplot(1,3,i+1,projection='3d');full_mesh(ax,gt['V'],gt['F'],'gray',.22)
                    if arm in aligned:full_mesh(ax,aligned[arm]['V'],aligned[arm]['F_solid'],'#8855aa',.8)
                    axes3(ax,lim);ax.set_title(arm+' actual scale-fixed SE(3) evaluation copy')
                fig.suptitle(g+'/'+vi+': independent GT shape evaluation; transforms never affect training/world predictions');figsave(fig,out/'Figure5_GT_Aligned.png')
    save_json(VIS/'FROZEN_REFERENCE_POINTERS.json',pointers)

def main(make_figures=True):
    p.verify();rows=[];stages=[];allbody=[];failures=[];allcamera=[];oldbody=readcsv(p.OLD/'metrics/ACTUAL_BODY_METRICS.csv')
    source_paths={Path(r['path']) for r in p.read(T/'audit/INPUT_FREEZE.json')['scientific_sources']};source_paths.update((T/'code').glob('*.py'));source_paths.update((T/'code/frozen_calibration').glob('*'));p.table(T/'audit/VERSION_SOURCES.csv',[p.asset(f) for f in sorted(source_paths) if f.is_file()])
    for c in p.cases():
        g=c['case']
        for vi in ['004','005']:
            rr=root(g,vi);vv=p.instance_views(g,vi);fit=[v for v in vv if v['meta']['role']=='FIT'];held=[v for v in vv if v['meta']['role']!='FIT'];cams=[]
            for v in vv:
                cam=camera(v);ad=p.read(cam/'ADMISSION.json');res=p.read(cam/'CAMERA_RESULT.json') if (cam/'CAMERA_RESULT.json').exists() else {};m=v['meta'];row=dict(group=g,video=vi,id=m['id'],role=m['role'],status=ad['status'],Ring_MAE_px=res.get('ring_boundary_MAE_px'),Ring_P95_px=res.get('ring_boundary_p95_px'),candidate_source=res.get('candidate_source'),admission=str(cam/'ADMISSION.json'),result=str(cam/'CAMERA_RESULT.json') if res else '',reasons=ad.get('reasons',[]));cams.append(row);allcamera.append(row)
                if ad['status']!='PASS':failures.append(dict(id=m['id']+'_CAMERA',group=g,video=vi,stage='Ring-First',kind='SOURCE_OR_CAMERA_GATE',code_bug=False,reasons=ad.get('reasons'),evidence=str(cam/'ADMISSION.json'),permanent_rule_promotion='NOT_REVIEWED'))
            fitn=sum(r['status']=='PASS' and r['role']=='FIT' for r in cams);hn=sum(r['status']=='PASS' and r['role']!='FIT' for r in cams);rf=status(fitn+hn,len(vv));yaw=status(sum(r['candidate_source']=='originalRF5DoF_RGB_yaw' for r in cams),len(vv));resolved=[r for r in cams if r['result']];proj=status(sum(num(r['Ring_MAE_px'])<=3 for r in resolved),len(vv)) if resolved else 'NOT_RUN';bank=p.read(p.OUT/g/vi/'bank/ADMISSION.json');hero=[f for f in (rr/'hero').glob('*/INFERENCE.json') if (f.parent/'ADMISSION.json').exists() and p.read(f.parent/'ADMISSION.json')['status']=='PASS'];hs='PASS' if len(hero)==8 else 'PARTIAL' if hero else 'NOT_RUN';arms={a:'PASS' if (rr/'body'/a/'TASK_PREDICTION_FROZEN.json').exists() else 'FAIL' if (rr/'body'/a/'FAILURE.json').exists() else 'NOT_RUN' for a in ['B1','B2']};bs='PASS' if all(a=='PASS' for a in arms.values()) else 'PARTIAL' if 'PASS' in arms.values() else 'FAIL' if 'FAIL' in arms.values() else 'NOT_RUN';evaldone=(rr/'GT_EVALUATION_COMPLETE.json').exists() if not p.inherited(g,vi) else (p.OLD/'runs/RF_ONLY_V1/GT_EVALUATION_COMPLETE.json').exists();gt='PASS' if bs=='PASS' and evaldone else 'FAIL' if (rr/'EVALUATION_FAILURE.json').exists() else 'NOT_RUN';hold=status(hn,len(held)) if gt=='PASS' else 'NOT_RUN'
            row=dict(Group=g,Video=vi,Execution='FROZEN_REFERENCE' if p.inherited(g,vi) else 'NEW',RGB_reference_bank=bank['status'],Ring_First=rf,yaw=yaw,Ring_projection=proj,HERO=hs,BodyInitialization='PASS' if bs=='PASS' else 'NOT_RUN',PyTorch3D=bs,B1=arms['B1'],B2=arms['B2'],GT_evaluation=gt,HOLDOUT_evaluation=hold,FIT_camera_PASS=fitn,FIT_expected=8,HOLDOUT_camera_PASS=hn,HOLDOUT_expected=len(held),HERO_targets=len(hero),evidence=str(T/'report/PIPELINE_STAGE_RECORDS.csv'));rows.append(row)
            logbase=p.OLD if p.inherited(g,vi) else T
            outputs=dict(RGB_reference_bank=Path(bank.get('bank',p.OUT/g/vi/'bank/ADMISSION.json')),Ring_First=rr/'camera',yaw=rr/'camera',Ring_projection=rr/'camera',HERO=rr/'hero',BodyInitialization=Path(c['initial']['path']),PyTorch3D=rr/'body',B1=rr/'body/B1/TASK_PREDICTION_FROZEN.json',B2=rr/'body/B2/TASK_PREDICTION_FROZEN.json',GT_evaluation=rr/'evaluation',HOLDOUT_evaluation=rr/'evaluation/projections')
            if (rr/'body/B1/INITIAL.npz').exists():outputs['BodyInitialization']=rr/'body/B1/INITIAL.npz'
            for s in outputs:
                log=logbase/'logs/CAMERA_RUN.log' if s in ['Ring_First','yaw','Ring_projection'] else logbase/'logs/HERO_RF_ONLY.log' if p.inherited(g,vi) and s=='HERO' else T/'logs/HERO_RUN.log' if s=='HERO' else logbase/'logs/BODY_BATCH.json' if s in ['PyTorch3D','B1','B2'] else logbase/'logs/GT_EVALUATION.log' if s in ['GT_evaluation','HOLDOUT_evaluation'] else T/'logs/BANK_BUILD.log' if s=='RGB_reference_bank' else T/'logs/INPUT_AUDIT.log'
                evidence=p.OUT/g/vi/'bank/ADMISSION.json'
                if s in ['Ring_First','yaw','Ring_projection']:evidence=T/'metrics/CAMERA_METRICS.csv'
                elif s=='HERO' and hero:evidence=hero[0]
                elif s in ['B1','B2']:evidence=outputs[s]
                elif s in ['PyTorch3D','BodyInitialization'] and bs=='PASS':evidence=rr/'body/B1/TASK_PREDICTION_FROZEN.json'
                elif s in ['GT_evaluation','HOLDOUT_evaluation']:evidence=(p.OLD/'runs/RF_ONLY_V1/GT_EVALUATION_COMPLETE.json') if p.inherited(g,vi) else rr/'GT_EVALUATION_COMPLETE.json'
                if not p.inherited(g,vi):
                    if s in ['RGB_reference_bank','Ring_First','yaw','Ring_projection']:
                        suffix='NATIVE_REFERENCE_DENSITY_REV2.log' if s=='RGB_reference_bank' else 'CAMERA_RUN_REF_DENSITY_REV2.log'
                        if bank.get('input_completion_revision')=='REF_DENSITY_REV2':log=T/'logs'/suffix
                        elif bank.get('execution')=='MATURE_G01_NATIVE_REFERENCE_BUILD_REV1':log=T/'logs'/('NATIVE_REFERENCE_BUILD_REV1_RESUME.log' if s=='RGB_reference_bank' else 'CAMERA_RUN_REF_BUILD_REV1.log')
                    if s=='HERO' and g in ['G03','G06']:log=T/'logs/HERO_G03_G06_REV1.log'
                    if s=='HERO' and bank.get('input_completion_revision')=='REF_DENSITY_REV2':log=T/'logs/HERO_FINAL_NEW_INSTANCES.log'
                if s in ['B1','B2']:log=logbase/'logs'/(f'TRAIN_{g}_{s}.log' if p.inherited(g,vi) else f'TRAIN_{g}_{vi}_{s}.log')
                if s=='BodyInitialization':log=logbase/'logs'/(f'TRAIN_{g}_B1.log' if p.inherited(g,vi) else f'TRAIN_{g}_{vi}_B1.log')
                stages.append(dict(Group=g,Video=vi,Stage=s,Status=row[s],Input=str(T/'audit/INPUT_FREEZE.json'),Output=str(outputs[s]) if outputs[s].exists() else '',SourceVersion=str(T/'audit/VERSION_SOURCES.csv'),Log=str(log) if log.exists() else '',Evidence=str(evidence) if evidence.exists() or s in ['Ring_First','yaw','Ring_projection'] else '',Protocol=str(T/'PROTOCOL_REF_DENSITY_REV2.yaml') if bank.get('input_completion_revision')=='REF_DENSITY_REV2' else str(T/'PROTOCOL_REF_BUILD_REV1.yaml'),Execution=row['Execution']))
            metrics=[dict(x,video=vi,execution='FROZEN_REFERENCE') for x in oldbody if x['group']==g] if p.inherited(g,vi) else readcsv(T/'metrics'/g/vi/'ACTUAL_BODY_METRICS.csv')
            for arm in ['B0','B1','B2']:
                m=next((dict(x) for x in metrics if x['arm']==arm),dict(group=g,video=vi,arm=arm,status='NOT_RUN',GT_MAE_mm='NaN',strict_3D_IoU='NaN',conditional_occupancy_IoU='NaN',GT_P95_mm='NaN',FIT_IoU_all_frozen='NaN',HOLDOUT_IoU_all_frozen='NaN'));m.update(video=vi,execution=row['Execution']);allbody.append(m)
            if not p.inherited(g,vi) and bank['status']!='PASS':failures.append(dict(id=g+'_'+vi+'_CALIBRATION',group=g,video=vi,kind='MATURE_REFERENCE_BUILD_FAILED' if bank.get('execution')=='MATURE_G01_NATIVE_REFERENCE_BUILD_REV1' else 'MISSING_PREBUILT_REFERENCE_INITIAL_DIAGNOSIS',code_bug='NameError' in bank.get('error',''),reasons=bank['reasons'],raw_RGB_and_Mask_available=True,confirmed_error=bank.get('error'),evidence=str(p.OUT/g/vi/'bank/ADMISSION.json'),permanent_rule_promotion='NOT_REVIEWED'))
            for arm in ['B1','B2']:
                if arms[arm]=='FAIL':failures.append(dict(id=g+'_'+vi+'_'+arm+'_BODY',group=g,video=vi,kind='BODY_STAGE_FAILURE',code_bug=False,evidence=str(rr/'body'/arm/'FAILURE.json')))
    numeric=['strict_3D_IoU','conditional_occupancy_IoU','GT_MAE_mm','GT_P95_mm','Fscore_0_5mm','GT_coverage_0_5mm','GT_median_mm','GT_max_mm','GT_median_relative_to_diagonal','vertex_displacement_MAE_mm','vertex_displacement_p95_mm','GT_volume_error_mm3','GT_volume_relative_error','FIT_IoU_admitted_subset','FIT_IoU_all_frozen','HOLDOUT_IoU_admitted_subset','HOLDOUT_IoU_all_frozen']
    for r in allbody:
        for k in numeric:
            if r.get(k) in ['',None]:r[k]='NaN'
    p.table(T/'report/PIPELINE_COMPLETENESS.csv',rows);p.table(T/'report/PIPELINE_STAGE_RECORDS.csv',stages);p.table(T/'metrics/CAMERA_METRICS.csv',allcamera);p.table(T/'metrics/BODY_METRICS.csv',allbody)
    missing=[];calibration=[]
    for c in p.read(T/'audit/CALIBRATION_INPUTS.json'):
        admission=p.read(p.OUT/c['group']/c['video']/'bank/ADMISSION.json');calibration.append(dict(group=c['group'],video=c['video'],prebuilt_archived_reference_views=len(c['views']),status=admission['status'],execution=admission.get('execution'),method=admission.get('method'),points=admission.get('points'),bank=admission.get('bank'),reason=admission.get('reasons')))
        if admission['status']!='PASS':missing.append(dict(group=c['group'],video=c['video'],raw_video_available=True,frozen_FIT_RGB_count=8,missing_prebuilt_reference_is_not_terminal=True,actual_terminal_stage='Native reference construction',actual_reason=admission.get('reasons'),error=admission.get('error'),evidence=str(p.OUT/c['group']/c['video']/'bank/ADMISSION.json')))
    p.table(T/'audit/MISSING_ASSETS.csv',missing);p.table(T/'audit/CALIBRATION_METHODS.csv',calibration)
    if not missing:(T/'audit/MISSING_ASSETS.csv').write_text('group,video,asset_missing,reason\n')
    failures.append(dict(id='VIDEO_ROUTING_ADAPTER_ASSERTION',kind='ENGINEERING_BUG_REPAIRED',code_bug=True,science_executed_before_fix=False,evidence=str(T/'audit/ROUTING_FIX.json')));failures.append(dict(id='REFERENCE_TRACKER_PATH_NAMESPACE',kind='ENGINEERING_BUG_REPAIRED',code_bug=True,scientific_parameters_changed=False,evidence=str(T/'audit/REFERENCE_BOOTSTRAP_PATH_FIX.json')))
    failures.append(dict(id='MISSING_PREBUILT_BANK_WRONGLY_TREATED_AS_TERMINAL',kind='WORKFLOW_INCOMPLETENESS_CORRECTED',code_bug=True,scientific_negative=False,confirmed_cause='Initial implementation omitted the existing mature native reference-preparation chain',repair='User-reviewed REF_BUILD_REV1 reuses the mature G01 upstream',evidence=str(T/'PROTOCOL_REF_BUILD_REV1.yaml')))
    if (T/'audit/REPORT_EVIDENCE_PATH_REPAIR.json').exists():failures.append(dict(id='DEFERRED_REPORT_EVIDENCE_PATHS',kind='ENGINEERING_REPORT_ORDERING_BUG_REPAIRED',code_bug=True,scientific_negative=False,evidence=str(T/'audit/REPORT_EVIDENCE_PATH_REPAIR.json')))
    for history in ['BEFORE_REF_BUILD_REV1','REF_BUILD_REV1_RESULTS']:
        for f in (T/'runs'/history).rglob('ADMISSION*.json'):
            x=p.read(f)
            if x.get('status')=='PASS':continue
            failures.append(dict(id=history+'_'+str(f.relative_to(T/'runs'/history)).replace('/','_'),kind='SUPERSEDED_STAGE_EVIDENCE',current=False,status=x.get('status'),reasons=x.get('reasons'),code_bug='NameError' in x.get('error',''),evidence=str(f)))
    for f in (T/'runs/RF_ONLY_V1').glob('G*/0*/bank/ADMISSION_PRE*.json'):failures.append(dict(id=str(f.relative_to(T/'runs/RF_ONLY_V1')).replace('/','_'),kind='SUPERSEDED_ENGINEERING_OR_SOURCE_STATUS',current=False,status=p.read(f).get('status'),evidence=str(f)))
    paired=[]
    for row in rows:
        g,vi=row['Group'],row['Video'];arms={r['arm']:r for r in allbody if r['group']==g and r['video']==vi}
        if not all(arms[a]['status']=='PASS' for a in ['B1','B2']):continue
        x,y=arms['B1'],arms['B2'];pair=dict(group=g,video=vi,execution=row['Execution'],delta_GT_MAE_B2_minus_B1_mm=num(y['GT_MAE_mm'])-num(x['GT_MAE_mm']),delta_GT_P95_B2_minus_B1_mm=num(y['GT_P95_mm'])-num(x['GT_P95_mm']),delta_FIT_IoU_B2_minus_B1=num(y['FIT_IoU_all_frozen'])-num(x['FIT_IoU_all_frozen']),delta_HOLDOUT_IoU_all_frozen_B2_minus_B1=num(y['HOLDOUT_IoU_all_frozen'])-num(x['HOLDOUT_IoU_all_frozen']))
        dep=readcsv(p.OLD/'metrics/DEPTH_METRICS.csv') if p.inherited(g,vi) else readcsv(T/'metrics'/g/vi/'DEPTH_METRICS.csv')
        for arm in ['B1','B2']:
            dd=[d for d in dep if d['group']==g and d['arm']==arm];N=sum(int(d['fixed_N']) for d in dd);A=sum(int(d['active_N']) for d in dd);pair[arm+'_depth_fixed_N']=N;pair[arm+'_depth_coverage']=A/N if N else None;pair[arm+'_depth_active_MAE_mm']=sum(num(d['depth_MAE_mm'])*int(d['active_N']) for d in dd if int(d['active_N'])>0)/A if A else None
        paired.append(pair)
        if num(pair['B2_depth_active_MAE_mm'])<num(pair['B1_depth_active_MAE_mm']) and pair['delta_GT_MAE_B2_minus_B1_mm']>0:failures.append(dict(id=g+'_'+vi+'_DEPTH_BETTER_GT_WORSE',group=g,video=vi,kind='SCIENTIFIC_NEGATIVE',code_bug=False,confirmed_cause='Observed paired metrics only; physical causal mechanism not proven',metrics=pair,evidence=str(T/'metrics/PAIRED_B2_VS_B1.csv')))
        if row['Execution']=='NEW':
            for arm in ['B1','B2']:
                file=root(g,vi)/'body'/arm/'UPDATES.json';u=p.read(file);reject=[q for q in u['iterations'] if not q['accepted']];failures.append(dict(id=g+'_'+vi+'_'+arm+'_CANDIDATE_REJECTIONS',kind='GEOMETRY_OR_PROJECTION_CANDIDATE_REJECTIONS',code_bug=False,rejected_updates=len(reject),fixed_updates=36,evidence=str(file)));failures.append(dict(id=g+'_'+vi+'_'+arm+'_NO_SWEEP',kind='UNDERCONSTRAINED_GROWTH',code_bug=False,reason='Same frozen >=2-video evidence gate; single-video fitting cannot create eligible new Sweep',evidence=str(file)))
    p.table(T/'metrics/PAIRED_B2_VS_B1.csv',paired)
    for f in failures:f.setdefault('permanent_rule_promotion','NOT_REVIEWED')
    save_json(T/'FAILURE_REGISTRY.json',dict(failures=failures,scientific_failures_preserved=True,permanent_rules_changed=False))
    full=sum(r['Ring_First']=='PASS' for r in rows);fitpass=sum(r['FIT_camera_PASS']==8 for r in rows);hcount=sum(r['HERO']=='PASS' for r in rows);bcount=sum(r['PyTorch3D']=='PASS' for r in rows);new=[r for r in rows if r['Execution']=='NEW' and r['PyTorch3D']=='PASS'];summary=dict(status='PARTIAL' if bcount<10 or full<10 else 'PASS',target_groups=5,target_videos=10,full_Ring_First_videos=full,FIT_Ring_First_videos=fitpass,HERO_videos=hcount,Body_videos=bcount,new_body_videos=[r['Group']+'/'+r['Video'] for r in new],new_HERO_inferences=sum(r['HERO_targets'] for r in rows if r['Execution']=='NEW'),historical_prediction_fallback=0,GT_used_for_selection=False,G03_prediction_changed=False)
    save_json(T/'metrics/SUMMARY.json',summary)
    headers=['Group','Video','RGB_reference_bank','Ring_First','yaw','Ring_projection','HERO','PyTorch3D','B1','B2','GT_evaluation','HOLDOUT_evaluation'];md=['# 十段视频标准流程验收','', '| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(str(r[k]) for k in headers)+' |' for r in rows];md+=['','Ring-First PASS 要求全部冻结 FIT/HOLDOUT；FIT 完整但 HOLDOUT 失败记 PARTIAL。HERO PASS 仅覆盖冻结的 8 个 FIT 目标；HOLDOUT 不参与训练。原有参考未重训。每项 PASS 的实际路径、源码、日志见 PIPELINE_STAGE_RECORDS.csv。'];(T/'report/PIPELINE_COMPLETENESS.md').write_text('\n'.join(md)+'\n')
    if make_figures:figures()
    links=['# 静态结果索引','', '所有图来自真实 RGB、Mask、相机和实际 Mesh；无 HTML。']
    for r in rows:links.append(f"- {r['Group']}/{r['Video']}：[{r['Execution']} 图像](./{r['Group']}/{r['Video']}/)，RF={r['Ring_First']}，HERO={r['HERO']}，Body={r['PyTorch3D']}。")
    (VIS/'README.md').write_text('\n'.join(links)+'\n')
    report=['# 标准流程补全 002','',f'十段视频中，严格全视角 Ring-First 完成 **{full}/10**；全部 FIT 合格 **{fitpass}/10**；正式 HERO **{hcount}/10**；PyTorch3D B1/B2 **{bcount}/10**。新增主体实例：'+(', '.join(summary['new_body_videos']) or '无')+'。','', 'G01/005 的参考图身份和原生地图坐标得到修复；G02/004 补建同视频参考库。G03/004 原失败 HOLDOUT 同参数重放仍为 3.0651759247 px，超过原 3 px 门限，预测完全保留，不能宣称因本轮得到形态改善。','', '## 唯一标准与冻结边界','', '复用 G01/004 RF_ONLY_V1 的 native camera.recover、RGB yaw 消歧和来源过滤；RF_CONFIG、3px 验收、正式权重、原生 axial-Z、8 FIT 视角、支持偏移 2/4/6、EXACT013、36×3 Graph/SmoothARAP/Sweep 更新器和 HeroDepth018 参数全部相同。没有新相机算法、跨视频 BA、DXY 修改或 GT 选模。','', '001 的四个 004 是冻结引用，G03/004 只重放失败 HOLDOUT。新驱动的差异仅是 video 选择、实例输出路径和首次推理辅助输出保留；完整差异见 audit/driver_adapters。Body 的实际 optimizer_adapter.py 应与 001/G01 一致。','', '## 参考库与真实来源','', 'G01/005：52 张历史 FIT 参考图均具实际 RGB/Mask 文件及 SHA；980 个原地标由历史明确记录的 H 逆变换恢复到原生 005 Ring 坐标。不是重新估计 H，也未认证 004/005 共同坐标。往返最大差 2.84e−14 mm，980/980 地标保留，无当前 HOLDOUT 像素混入。','', 'G02/004：使用 7 张同视频历史 FIT 标定图，原 features019.landmarks 函数不改数值参数，得到 125 个合格地标。历史标定相机只定义参考图三角化，最终相机全部重新由 Ring-First 求解；纯 PnP 候选只保留诊断。此种历史 RGB 标定是条件标定，并非独立位姿 GT。','', 'G02/005、G03/005、G05/005、G06/005：真实视频、8 张冻结 FIT RGB/Mask 均存在，但未找到独立同视频原生 Ring 位姿标定图/参考库。014 的新增帧相机采用历史背景 PnP 扩展，其代码在没有本视频原库时允许回退到 004 地标，不能据此认证新库。需要补充的资料明确列在 audit/MISSING_ASSETS.csv；没有将“缺原生标定”写成“缺原始图像”。','', '原视频逐帧只读解码与像素 SHA 对照见 RAW_FRAME_BINDING.json。新增 G01/005 和 G02/004 的参考/目标图均找到精确原视频像素匹配。G01/004 部分历史工作图未能以本轮固定 INTER_AREA 解码获得逐字节匹配，仍只具归档图像身份，不声称重新认证其全部原始帧号；该基线未被修改。原始 ZIP 及其他资产保持只读。','']+md[2:]+['','## 三臂真实指标','', '| Group | Video | Arm | GT MAE mm | GT P95 mm | Strict IoU | Conditional IoU | FIT IoU | HOLDOUT完整IoU |','|---|---|---|---|---|---|---|---|---|']
    for r in allbody:report.append('| '+' | '.join([r['group'],r['video'],r['arm']]+[fmt(r.get(k)) for k in ['GT_MAE_mm','GT_P95_mm','strict_3D_IoU','conditional_occupancy_IoU','FIT_IoU_all_frozen','HOLDOUT_IoU_all_frozen']])+' |')
    report+=['','Strict IoU 无效保持 NaN，条件占据不冒充严格实体 IoU。GT 只在全部新预测固定终点和 SHA 冻结后读取；沿用 015 的 96 起点、尺度固定 SE(3) 及实际对齐副本。GT 对齐不回写世界坐标预测、相机或 HERO。完整 MAE/P95/最大值、覆盖率、F-score、顶点位移、深度有效分母、几何状态在逐实例 metrics 和 BODY_METRICS.csv。','', '## 失败、保留和解释范围','', '- 四个缺少原生参考的 005 停止其不合格下游，没有换方法。','- G03 的 HOLDOUT 投影仍未通过，原 B1/B2 与全部失败证据保留。旧缺柄问题未因来源补全而解决。','- 原生长门禁至少要求两个视频的证据；本轮每视频独立 Body，两臂均不得擅自放宽，不能宣称新增连续柄部。','- 15 项新增契约测试曾发现实例路由适配器把原代码的两个 video 常量误计为一个；测试门禁阻断科学运行，修复记录及失败日志保留。','- 原 001 的深度改善而 GT 恶化、严格 IoU 无效及 Ring 数值容差累计漂移仍是有效负证据；没有为新病例调权重或事后修复预测。','', '## 固定审计表','', '| 审计项目 | 必须汇报 |','|---|---|','|目标组数|5 物理组、10 视频；固定 80 FIT、25 HOLDOUT|',f'|本算法独立成功|{bcount}/10 视频产生 B1/B2；包括明确标注的冻结同路线引用，不等于正确重建|',f'|本算法失败|{10-bcount}/10 视频无完整新路线主体输出；各臂保留 NaN|','|历史测量值回退|0；冻结同路线参考和统一 EXACT013 初始化均明确列出，非其他路线回填|','|失败组及具体原因|FAILURE_REGISTRY.json、逐阶段验收表、对应 PNG|',f'|最终统计样本|{bcount} 个完整 B1/B2 视频实例；始终给出总分母 10 和物理组分母 5|','|是否使用 GT 选择算法|否；预测与代码先冻结，固定 FINAL36，不以 GT/HOLDOUT 选择 checkpoint|','', '## 使用与交付','', '统一入口：`code/run.py run --stage all`；阶段可选 audit/banks/cameras/hero/body/evaluate/report/check，参数 --group/--video/--arm。`run.py check` 核验输入和科学源码。已有冻结阶段拒绝覆盖或直接复用；更换任何输入/算法必须开新版本。','', '共享环境：`bash /home/liu/ring_first_3d_workspace/mainline/scripts/python.sh <入口>`；未创建环境或安装依赖。','',f'静态图绝对目录：`{VIS}`；索引 `{VIS/"README.md"}`。全部路径由交付检查器核验；没有 HTML。']
    text='\n'.join(report)+'\n'
    original_missing='G02/005、G03/005、G05/005、G06/005：真实视频、8 张冻结 FIT RGB/Mask 均存在，但未找到独立同视频原生 Ring 位姿标定图/参考库。014 的新增帧相机采用历史背景 PnP 扩展，其代码在没有本视频原库时允许回退到 004 地标，不能据此认证新库。需要补充的资料明确列在 audit/MISSING_ASSETS.csv；没有将“缺原生标定”写成“缺原始图像”。'
    text=text.replace(original_missing,'原先把没有现成历史参考库当作阻断是不充分的，人工指出后以 REF_BUILD_REV1 修订。四段 005 已实际调用成熟 G01 上游模块：原有 native Ring 五自由度、V6 RGB 跟踪/yaw 初始化/同视频局部标定、features019 三角化。未使用旧 PnP 相机、HERO 或 GT。全部成熟函数逐文件复制并验证原 SHA，最终相机仍执行同一 native RF_ONLY 和 3px 门限；没有跨视频 BA。详细结果见 CALIBRATION_METHODS.csv。\n\n对于最终 FIT 相机尚不完整的实例，REF_DENSITY_REV2 一次性纳入全部现成同视频历史 FIT RGB/Mask，严格剔除当前 HOLDOUT 像素。算法、数值参数和原八个 Body FIT 不变。该补充与 G01 原库使用额外标定 FIT 的规则一致；所有 REV1 结果完整保留在 runs/REF_BUILD_REV1_RESULTS，未根据 GT/HERO 选择帧。当前确实缺失或构建失败的项目以 MISSING_ASSETS.csv 和失败台账为准，不再把“无现成库”作为最终理由。')
    text=text.replace('- 四个缺少原生参考的 005 停止其不合格下游，没有换方法。','- 所有实例均走共享成熟构库和相机求解；真正未通过的 Ring/yaw/参考几何门禁停止该实例下游。初始缺库诊断和工程适配失败不被冒充科学负结果。')
    text=text.replace('统一入口：`code/run.py run --stage all`','统一入口：`code/standard.py run --stage all`')
    g3={r['arm']:r for r in allbody if r['group']=='G03' and r['video']=='005'}
    g3text='G03/004 原预测及失败 HOLDOUT 保持不变。'
    if all(g3.get(a,{}).get('status')=='PASS' for a in ['B0','B1','B2']):g3text+=' 新增 G03/005 独立结果：GT MAE B0/B1/B2='+ '/'.join(fmt(g3[a].get('GT_MAE_mm')) for a in ['B0','B1','B2'])+' mm，FIT IoU='+ '/'.join(fmt(g3[a].get('FIT_IoU_all_frozen')) for a in ['B0','B1','B2'])+'。这是新视频相对自身初始 Body 的配对评价，不能宣称旧 004 相机或旧缺柄问题被修复；两臂均未放宽 Sweep 生长门禁。'
    else:g3text+=' 新 G03/005 的实际执行状态和失败证据见逐阶段表。'
    text+='\n## G03 的本轮独立回答\n\n'+g3text+'\n'
    text=text.replace('## 唯一标准与冻结边界','G03：'+g3text+'\n\n## 唯一标准与冻结边界',1)
    text=text.replace('## 唯一标准与冻结边界','已修复：G01/005 图像来源与原生地图坐标、G02/004 构库，以及四段 005 的成熟原生构库入口；G02/005 再由同视频现成 FIT 补充恢复全部相机。剩余问题是 G03/004 的一个 HOLDOUT，以及 G05/005 的 Ring 标签/投影和 RGB 内点门禁，均不是“缺现成库”所致。\n\n## 唯一标准与冻结边界',1)
    text+='\n## 最终仍未通过的具体原因\n\n参考库缺失已通过成熟构建链处理；当前失败以实际相机观测/匹配为准。CAMERA_FAILURE_DIAGNOSTICS.csv 记录各失败帧的特征、匹配和内点数；RING_COMPONENT_DIAGNOSTICS.csv 保留固定相机下的逐连通分量贡献。G05_v005_raw00404 的主环 9901 像素、113/128 观测边界点 MAE=0.72386px；离散 63 像素标签占 15/128 点，MAE=75.19221px，对原总 MAE 贡献 8.81159px。原标签全部保留，没有删分量以通过门禁。该图像证据不自动解释其他 RGB 消歧失败的物理原因。\n'
    groups_with_output={r['Group'] for r in rows if r['PyTorch3D']=='PASS'};summary.update(physical_groups_with_independent_route_output=len(groups_with_output),physical_group_denominator=5,video_denominator=10,reference_banks_PASS=sum(r['RGB_reference_bank']=='PASS' for r in rows));text+='\n物理组独立覆盖：'+str(len(groups_with_output))+'/5 至少有一段同路线 Body；视频完整 Body 覆盖 '+str(bcount)+'/10。两种分母并列报告，不将物理组覆盖冒充十视频全部完成。\n';save_json(T/'metrics/SUMMARY.json',summary)
    text=text.replace('## 使用与交付','## 使用与交付',1)
    summary.pop('G03_prediction_changed',None);summary.update(G03_004_prediction_changed=False,G03_005_result=g3text);save_json(T/'metrics/SUMMARY.json',summary)
    (T/'TECHNICAL_REPORT.md').write_text(text);(T/'report/FINAL_REPORT.md').write_text(text);(T/'RESULT_CARD.md').write_text(f'# RESULT_CARD\n\n状态 {summary["status"]}\n\nRF 全视角 {full}/10，FIT {fitpass}/10；HERO {hcount}/10；Body {bcount}/10。新增 '+', '.join(summary['new_body_videos'])+'。\n\n'+g3text+'\n\n详见 report/FINAL_REPORT.md；静态图 visualization/README.md。\n')
    print('PUBLISHED',summary,'PNG',len(list(VIS.rglob('*.png'))),flush=True)
    from aggregate_metrics import main as aggregate
    aggregate()

if __name__=='__main__':main()
