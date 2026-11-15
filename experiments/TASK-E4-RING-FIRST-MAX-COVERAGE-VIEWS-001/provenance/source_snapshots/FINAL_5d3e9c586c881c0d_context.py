from ucommon import *
from PIL import Image
import shutil,subprocess,traceback
U=REPO/'experiments/TASK-E4-RING-FIRST-UNIFIED-BA-001';P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018';P14=REPO/'experiments/TASK-E4-PYTORCH3D-014';Q=P/'quick_solver_review';CAP=Path('/home/liu/polyp_research/smart_endoscope_20260805');K0=np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1.]])
PREFIXES=dict(G01='GP_Ip_12.0mm_closed_R10_single_refY',G03='GP_Ip_20.0mm_closed_R10_single_refY',G05='GP_Is_18.0mm_closed_R10_single_refY',G06='GP_IIa_14.0mm_closed_R10_single_refY')
os.environ.update(HF_HOME=str(N/'runtime/hf'),HF_MODULES_CACHE=str(N/'runtime/hf_modules'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
for d in ['inputs','features','ring_evidence','registration','selection','evaluation']:(N/d).mkdir(exist_ok=True)
def unit(v):return np.asarray(v)/max(np.linalg.norm(v),1e-15)
def angle(a,b):return np.degrees(np.arccos(np.clip(unit(a)@unit(b),-1,1)))
def snapshot_read(paths,name):freeze('provenance/'+name,[p for p in paths if Path(p).exists()],read_only=True,GT=False)
def camera_file(g):
 if(N/'config'/(g+'_FINAL_CAMERA_POOL.json')).exists():return N/'config'/(g+'_FINAL_CAMERA_POOL.json')
 return N/'config'/(g+'_CAMERAS_WITH_NATIVE005.json')if(N/'config'/(g+'_CAMERAS_WITH_NATIVE005.json')).exists()else N/'config'/(g+'_CAMERAS.json')
def selroot(g):return N/'selection_verified'if(N/'config/VISIBILITY_FIX.json').exists()else N/'selection'
def selpath(g,suffix):return selroot(g)/(g+suffix)
def planfreeze(g):return 'provenance/'+g+'_HERO_PLAN'+('_VERIFIED'if selroot(g).name=='selection_verified'else'')+'_FROZEN.json'
