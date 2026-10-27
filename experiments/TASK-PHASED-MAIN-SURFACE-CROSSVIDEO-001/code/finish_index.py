"""Record runtime, final source hashes and actual local/public artifact indexes."""
from common import *
import platform,importlib.metadata,subprocess
def main():
    versions={}
    for name in ['numpy','scipy','opencv-python','trimesh','matplotlib','Pillow']:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]='not registered'
    sys.path.insert(0,str(OLD/'surface_fusion_v3/vendor'));import open3d
    versions['open3d']=open3d.__version__;save('provenance/RUNTIME.json',dict(python=sys.version,executable=sys.executable,platform=platform.platform(),versions=versions,Open3D_module=str(Path(open3d.__file__).resolve()),environment=dict(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')))
    save('provenance/FINAL_SOURCE_MANIFEST.json',stamp(list((R/'code').glob('*.py'))+list((R/'provenance/frozen_sources').glob('*.py'))+[R/'config.json',R/'PROTOCOL.md',R/'TASK.md']))
    local=[]
    for p in sorted((R/'local_results').rglob('*')):
        if p.is_file():local.append(dict(path=str(p),relative_to_task=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),public_uploaded=False))
    save('provenance/LOCAL_RESULT_INDEX.json',local);csvsave('provenance/LOCAL_RESULT_INDEX.csv',local)
    branch='exp/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001';base='https://github.com/zheng1524/ring-first-3d/blob/'+branch+'/experiments/'+R.name+'/';png=[]
    for p in sorted((R/'figures').glob('*.png')):
        with Image.open(p)as im:size=im.size
        png.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),size_pixels=size,GitHub_URL=base+str(p.relative_to(R)),actual_XYZ_or_actual_RGB=True))
    save('provenance/PUBLIC_FIGURES.json',png)
    commits=subprocess.check_output(['git','-C',str(REPO),'log','a992fd62dfb3c4027c09ba4855e4ebf1eed50dba..HEAD','--format=%H %s'],text=True).splitlines();glbs=load(R/'metrics/GLB_INDEX.json');text=['# 结果索引：'+R.name,'','状态：D0 多来源开放场景；D1 派生刚体候选；D2 NOT_FUSED；D3 部分可评价。GT=NONE。','','[完整报告](TECHNICAL_REPORT.md) · [可复现入口](REPRODUCE.md) · [实际指标](metrics/) · [全部本地结果 SHA 索引](provenance/LOCAL_RESULT_INDEX.csv)','','公开四张核心图：','']
    for p in png:text.append('- ['+Path(p['path']).name+']('+p['path']+') — SHA256 `'+p['sha256']+'`')
    text+=['','完整几何仅保留本地；以下文件真实存在，并已独立重载核验。所有 GLB 用米序列化，原始数据用毫米。','','| 本地 GLB | 字节 | SHA256 | 状态 |','| --- | ---: | --- | --- |']
    for x in glbs:text.append('| `'+x['file']+'` | '+str(x['bytes'])+' | `'+x['sha256']+'` | '+x['status']+' |')
    text+=['','每场景本地图像、实际 XYZ/RGB、来源及诊断相机：','']
    for x in load(R/'metrics/VISUAL_LAYER_INDEX.json'):text.append('- `'+x['local_output']+'`：Layers_L1-L5、Camera_3Views、XYZ_3Views、Real_vs_3D、Local_3D_Scene、actual_XYZ_RGB.npz、diagnostic_cameras_exact.npz。')
    text+=['','真实 A→B 的原图、两类预测、叠加、差异、XYZ 及逐像素来源：`local_results/D1_evaluation/`。历史 B/C 对照：`local_results/D0_evaluation/`。全部实际文件见 CSV 索引；完整图像、NPZ、GLB 均未批量上传。','','已完成增量提交（本索引所在最终文档提交 SHA 由 Git 历史及最终交付回执提供，避免自引用）：','']+[('- `'+x+'`')for x in commits];(R/'RESULT_INDEX.md').write_text('\n'.join(text)+'\n')
    print('INDEX_COMPLETE',len(local),'local artifacts;',len(png),'public PNGs',flush=True)
if __name__=='__main__':main()
