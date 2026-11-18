"""Read-only streaming forensic inventory. No deletion/migration capability."""
import os, sys, stat, sqlite3, hashlib, json, time, re, csv, gzip, collections
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]
HOME = Path('/home/liu')
SELF = OUT.parents[1]
ROOTS = sorted(p for p in HOME.glob('ring_first_3d*') if p.is_dir() and p != SELF)
ROOTS += [HOME/'polyp_research', HOME/'ring-first-hero-core', HOME/'new-polyp-dxy']
ROOTS = list(dict.fromkeys(p for p in ROOTS if p.exists()))
DB = OUT/'ASSET_INVENTORY.sqlite'
if DB.exists():
    raise SystemExit('Refuse to overwrite an existing audit')
con = sqlite3.connect(DB)
con.execute('PRAGMA journal_mode=MEMORY')
con.execute('CREATE TABLE assets(path TEXT PRIMARY KEY,root TEXT,task TEXT,kind TEXT,size INTEGER,allocated INTEGER,dev INTEGER,inode INTEGER,nlink INTEGER,mtime_ns INTEGER,ctime_ns INTEGER,sha256 TEXT,hash_status TEXT,hash_source TEXT,symlink TEXT,value TEXT,extension TEXT)')
con.execute('CREATE TABLE refs(source TEXT,target TEXT,exists_now INTEGER,scope TEXT)')
con.execute('CREATE TABLE errors(path TEXT,error TEXT)')
cache = {}
refcache = {}
start=time.time()
text_ext={'.py','.sh','.json','.yaml','.yml','.toml','.md','.txt','.ini','.cfg','.html'}
stats=[]
def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def category(p):
    if '__pycache__' in p.parts or p.suffix=='.pyc': return 'REGENERABLE_CACHE'
    if p.suffix.lower() in {'.mp4','.avi','.mov','.blend'}: return 'UNIQUE_RAW_DATA'
    if p.suffix.lower() in {'.ckpt','.pth','.pt','.safetensors'}: return 'UNIQUE_MODEL_WEIGHT'
    if any(x in p.name.upper() for x in ('FAILURE','FAILED','REJECTION')): return 'FAILED_BUT_INFORMATIVE'
    if '/ring_first_3d_mainline/mainline/' in str(p) or '/ring_first_3d_mainline/src/' in str(p): return 'ACTIVE_MAINLINE'
    if p.suffix.lower() in {'.md','.csv','.json','.npz','.ply','.obj','.glb','.png','.html'} and any(x.startswith('TASK-') for x in p.parts): return 'HISTORICAL_EVIDENCE'
    if p.suffix.lower() in {'.py','.cpp','.cu','.h','.sh'}: return 'REUSABLE_REFERENCE'
    return 'UNKNOWN'
for root in ROOTS:
    n=logical=allocated=0
    for directory, dirs, files in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d!='.git')
        files=sorted(files)+[d for d in dirs if Path(directory,d).is_symlink()]
        dirs[:]=[d for d in dirs if not Path(directory,d).is_symlink()]
        for name in files:
            p=Path(directory,name)
            if name=='.git': continue
            try:
                s=p.lstat(); link=os.readlink(p) if stat.S_ISLNK(s.st_mode) else ''
                if not (stat.S_ISREG(s.st_mode) or link): continue
                key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
                if link:
                    h=hashlib.sha256(os.fsencode(link)).hexdigest(); status='HASH_RECOMPUTED'; origin=str(p)
                elif key in cache:
                    h,origin=cache[key]; status='HASH_INHERITED'
                else:
                    h=digest(p); status='HASH_RECOMPUTED'; origin=str(p); cache[key]=(h,origin)
                    after=p.stat()
                    if (after.st_size,after.st_mtime_ns)!=(s.st_size,s.st_mtime_ns):
                        raise OSError('FILE_CHANGED_DURING_HASH')
                task=next((x for x in reversed(p.parts) if x.startswith('TASK-')),'UNASSIGNED')
                kind='symlink' if link else 'file'
                con.execute('INSERT INTO assets VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(str(p),str(root),task,kind,s.st_size,s.st_blocks*512,s.st_dev,s.st_ino,s.st_nlink,s.st_mtime_ns,s.st_ctime_ns,h,status,origin,link,category(p),p.suffix.lower()))
                n+=1; logical+=s.st_size; allocated+=s.st_blocks*512
                if not link and p.suffix.lower() in text_ext and 0<s.st_size<2_000_000:
                    if key not in refcache:
                        text=p.read_text(errors='replace')
                        refcache[key]=set(re.findall(r'/home/liu/[^\s\x22\x27<>`\\,;\)\]\}]+',text))
                    for target in refcache[key]:
                        scope='INTERNAL_PROJECT' if any(target==str(r) or target.startswith(str(r)+'/') for r in ROOTS if r.name!='new-polyp-dxy') else 'INDEPENDENT_DXY_PROJECT' if target.startswith('/home/liu/new-polyp-dxy') else 'EXTERNAL_DEPENDENCY'
                        con.execute('INSERT INTO refs VALUES(?,?,?,?)',(str(p),target,int(Path(target).exists()),scope))
            except (OSError,ValueError) as e:
                con.execute('INSERT INTO errors VALUES(?,?)',(str(p),str(e)))
        if n and n%2000<10: con.commit()
    con.commit()
    stats.append(dict(root=str(root),files=n,logical_bytes=logical,path_allocated_bytes=allocated))
    print(root.name,n,round(logical/1e9,3),'GB',round(time.time()-start,1),'s',flush=True)
con.execute('CREATE INDEX hashes ON assets(sha256,size)')
con.execute('CREATE INDEX inodes ON assets(dev,inode)')
con.commit()
def export(query,name):
    cursor=con.execute(query)
    with gzip.open(OUT/name,'wt',encoding='utf8',newline='') as f:
        w=csv.writer(f);w.writerow([d[0] for d in cursor.description]);w.writerows(cursor)
export('SELECT * FROM assets','ASSET_INVENTORY.csv.gz')
export('SELECT * FROM refs','DEPENDENCY_REFERENCES.csv.gz')
export('SELECT a.* FROM assets a JOIN (SELECT sha256,size FROM assets WHERE kind="file" GROUP BY sha256,size HAVING count(*)=1) u USING(sha256,size)','UNIQUE_ASSETS.csv.gz')
export('SELECT sha256,size,count(*) paths,count(distinct printf("%d:%d",dev,inode)) physical_inodes,group_concat(path,char(10)) paths_json_lines FROM assets WHERE kind="file" GROUP BY sha256,size HAVING count(*)>1','DUPLICATE_ASSET_GROUPS.csv.gz')
export('SELECT root,task,extension,value,count(*) files,sum(size) logical_bytes,sum(allocated) path_allocated_bytes FROM assets GROUP BY root,task,extension,value','ASSET_CLASSIFICATION.csv.gz')
export("SELECT * FROM assets WHERE kind='symlink'",'SYMLINKS.csv.gz')
summary=dict(roots=list(map(str,ROOTS)),workspace_stats=stats,files=con.execute('SELECT count(*) FROM assets').fetchone()[0],logical_bytes=con.execute('SELECT sum(size) FROM assets').fetchone()[0],unique_inode_allocated_bytes=con.execute('SELECT sum(allocated) FROM (SELECT max(allocated) allocated FROM assets GROUP BY dev,inode)').fetchone()[0],unique_regular_file_inodes=con.execute('SELECT count(*) FROM (SELECT dev,inode FROM assets WHERE kind="file" GROUP BY dev,inode)').fetchone()[0],hash_counts=dict(con.execute('SELECT hash_status,count(*) FROM assets GROUP BY hash_status')),errors=list(con.execute('SELECT * FROM errors')),seconds=time.time()-start,exclusions=['.git files and directories: independent Git object audit','new forensic output worktree: self-output exclusion','directory symlinks not traversed; targets enumerated separately in runtime/dependency audit'],method='All regular-file hashes recomputed by streaming SHA256 once per stable dev/inode/size/mtime/ctime identity. HASH_INHERITED only refers to same current-scan inode, not old audit hashes. Symlink SHA hashes link text, never target bytes. No source writes. Duplicate claims require SHA256 AND size; versions/similarity never deduplicated.')
(OUT/'ASSET_SCAN_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('DONE',summary['files'],flush=True)
