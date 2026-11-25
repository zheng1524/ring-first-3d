"""Consolidate audited identical Open3D files onto retained .venv inodes; paths stay valid."""
import csv,json,os,time
from pathlib import Path
from cleanup_execute import sha
T=Path(__file__).resolve().parent.parent;W=Path('/home/liu/ring_first_3d_workspace');P=Path('/home/liu/polyp_research');out=T/'evidence/OPEN3D_DEDUP_RECEIPT.json';assert not out.exists()
rows=list(csv.DictReader((T.parents[1]/'docs/audits/TASK-HERO-DOWNSTREAM-AND-STORAGE-AUDIT-001/EXPERIMENT_STORAGE_MAP.csv').open()));plan=[]
for r in rows:
 if r['row_type']!='duplicate_leaf'or r['asset_kind']!='OPEN3D_RUNTIME':continue
 p=Path(r['path']);q=Path(r['retained_copy']);assert str(p).startswith(str(P/'ring_anchor_3d/experiments/surface_fusion_v3/vendor/open3d')+'/') and str(q).startswith(str(P/'ring_anchor_3d/.venv/lib/python3.12/site-packages/open3d')+'/')
 assert p.is_file()and q.is_file()and not p.is_symlink()and not q.is_symlink();a=p.stat();b=q.stat();assert sha(p)==sha(q)==r['sha256'] and a.st_dev==b.st_dev and a.st_mode==b.st_mode
 if a.st_ino!=b.st_ino:plan.append(dict(path=str(p),canonical=str(q),sha256=r['sha256'],old_inode=a.st_ino,old_nlink=a.st_nlink,blocks=a.st_blocks*512))
fs=os.statvfs(W);result=dict(epoch=time.time(),before_available=fs.f_bavail*fs.f_frsize,files=[])
for r in plan:
 p=Path(r['path']);q=Path(r['canonical']);assert sha(p)==sha(q)==r['sha256'];tmp=p.with_name(p.name+'.M2F13-link');assert not tmp.exists();os.link(q,tmp);os.replace(tmp,p);assert p.stat().st_ino==q.stat().st_ino and sha(p)==r['sha256'];result['files'].append(r)
os.sync();fs=os.statvfs(W);result.update(after_available=fs.f_bavail*fs.f_frsize,code_sha256=sha(__file__));result['net_df_release_bytes']=result['after_available']-result['before_available'];out.write_text(json.dumps(result,indent=2));print('OPEN3D_DEDUP',len(plan),'DF_NET',result['net_df_release_bytes'])
